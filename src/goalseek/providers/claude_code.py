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
    _PLAN_MODES = {"hypothesis", "plan"}
    _IMPLEMENT_MODES = {"implementation"}
    _EVALUATE_MODES = {"evaluation", "evaluate"}

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
            allowed_modes=self._PLAN_MODES,
            sanitize_plan_output=True,
        )

    def implement(self, request: ProviderRequest) -> ProviderResponse:
        return _run_claude_cli(
            request,
            self.capabilities(ProviderSelection(name="claude_code", model=request.model_name)),
            env=self._CLI_ENV,
            permission_mode="acceptEdits",
            allowed_modes=self._IMPLEMENT_MODES,
        )

    def evaluate(self, request: ProviderRequest) -> ProviderResponse:
        return _run_claude_cli(
            request,
            self.capabilities(ProviderSelection(name="claude_code", model=request.model_name)),
            env=self._CLI_ENV,
            permission_mode="default",
            allowed_modes=self._EVALUATE_MODES,
            sanitize_plan_output=True,
        )


def _run_claude_cli(
    request: ProviderRequest,
    capabilities: ProviderCapabilities,
    env: dict[str, str] | None,
    permission_mode: str,
    allowed_modes: set[str],
    sanitize_plan_output: bool = False,
) -> ProviderResponse:
    start = time.time()
    validation_error = _validate_request(request, allowed_modes)
    if validation_error:
        return ProviderResponse(
            raw_text="",
            exit_code=1,
            duration_sec=0.0,
            error=validation_error,
        )
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
    try:
        result = run_command(
            command,
            cwd=Path(request.project_root),
            timeout_sec=request.timeout_sec,
            env=env,
        )
    except TimeoutError as exc:
        return ProviderResponse(
            raw_text="",
            exit_code=124,
            duration_sec=time.time() - start,
            changed_files=[],
            error=str(exc),
        )
    except Exception as exc:
        return ProviderResponse(
            raw_text="",
            exit_code=1,
            duration_sec=time.time() - start,
            changed_files=[],
            error=str(exc),
        )
    raw_text = result.stdout or result.stderr
    if sanitize_plan_output:
        raw_text = _sanitize_plan_output(raw_text)
    stderr_text = result.stderr.strip()
    return ProviderResponse(
        raw_text=raw_text,
        exit_code=result.exit_code,
        duration_sec=time.time() - start,
        changed_files=[],
        error=stderr_text if result.exit_code != 0 or (not result.stdout and stderr_text) else None,
    )


def _validate_request(request: ProviderRequest, allowed_modes: set[str]) -> str | None:
    if request.mode not in allowed_modes:
        allowed = ", ".join(sorted(allowed_modes))
        return f"unsupported mode '{request.mode}' for claude_code; expected one of: {allowed}"
    if not request.prompt_text.strip():
        return "prompt_text cannot be empty"
    return None


def _sanitize_plan_output(raw_text: str) -> str:
    cleaned = re.sub(r"^.*\.claude/plans/.*$\n?", "", raw_text, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned
