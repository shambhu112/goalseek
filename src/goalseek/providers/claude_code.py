from __future__ import annotations

import logging
import re
import shutil
import time
from pathlib import Path

from goalseek.models.config import ProviderSelection
from goalseek.providers.base import ProviderCapabilities, ProviderRequest, ProviderResponse
from goalseek.utils.subprocess import run_command

logger = logging.getLogger(__name__)


class ClaudeCodeProvider:
    name = "claude_code"

    _CLI_ENV = {
        "CLAUDE_AUTO_APPROVE": "true",
        "CLAUDE_SKIP_CONFIRMATIONS": "true",
    }

    def capabilities(self, config: ProviderSelection) -> ProviderCapabilities:
        executable = config.executable or shutil.which("claude")
        return ProviderCapabilities(
            available=bool(executable),
            supports_non_interactive=True,
            supports_split_prompts=True,
            executable=executable,
        )

    def plan(self, request: ProviderRequest) -> ProviderResponse:
        logger.info("Planning with %s for model %s", self.name, request.model_name)
        return _run_claude_cli(
            request,
            self.capabilities(ProviderSelection(name="claude_code", model=request.model_name)),
            env=self._CLI_ENV,
            permission_mode="default",
            sanitize_plan_output=True,
        )

    def implement(self, request: ProviderRequest) -> ProviderResponse:
        return _run_claude_cli(
            request,
            self.capabilities(ProviderSelection(name="claude_code", model=request.model_name)),
            env=self._CLI_ENV,
            permission_mode="acceptEdits",
        )


def _run_claude_cli(
    request: ProviderRequest,
    capabilities: ProviderCapabilities,
    env: dict[str, str] | None,
    permission_mode: str,
    sanitize_plan_output: bool = False,
) -> ProviderResponse:
    start = time.time()
    if not capabilities.executable:
        return ProviderResponse(
            raw_text="",
            exit_code=1,
            duration_sec=0.0,
            error="executable not found",
        )

    command = [
        capabilities.executable,
        "--print",
        "--model",
        request.model_name,
        "--permission-mode",
        permission_mode,
        "--add-dir",
        str(request.project_root),
        "--",
        request.prompt_text,
    ]
    result = run_command(
        command,
        cwd=Path(request.project_root),
        timeout_sec=request.timeout_sec,
        env=env,
    )
    raw_text = result.stdout or result.stderr
    if sanitize_plan_output:
        raw_text = _sanitize_plan_output(raw_text)
    return ProviderResponse(
        raw_text=raw_text,
        exit_code=result.exit_code,
        duration_sec=time.time() - start,
        changed_files=[],
        error=None if result.exit_code == 0 else result.stderr.strip(),
    )


def _sanitize_plan_output(raw_text: str) -> str:
    cleaned = re.sub(r"^.*\.claude/plans/.*$\n?", "", raw_text, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned
