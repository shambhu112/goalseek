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
    empty_output = not result.stdout.strip() and not result.stderr.strip()
    error: str | None
    if result.exit_code != 0:
        error = stderr_text or "command failed with no output"
    elif empty_output:
        error = "command produced no output"
    elif not result.stdout and stderr_text:
        error = stderr_text
    else:
        error = None
    exit_code = result.exit_code if not (result.exit_code == 0 and empty_output) else 1
    return ProviderResponse(
        raw_text=raw_text,
        exit_code=exit_code,
        duration_sec=time.time() - start,
        changed_files=[],
        error=error,
    )


def _validate_request(request: ProviderRequest, allowed_modes: set[str]) -> str | None:
    errors: list[str] = []
    if request.mode not in allowed_modes:
        allowed = ", ".join(sorted(allowed_modes))
        errors.append(f"unsupported mode '{request.mode}' for claude_code; expected one of: {allowed}")
    if not request.prompt_text.strip():
        errors.append("prompt_text cannot be empty")
    if not request.model_name:
        errors.append("model_name cannot be empty")
    if request.timeout_sec <= 0:
        errors.append(f"timeout_sec must be positive, got {request.timeout_sec}")
    if request.iteration <= 0:
        errors.append(f"iteration must be positive, got {request.iteration}")
    for path in request.writable_paths:
        if Path(path).is_absolute():
            errors.append(f"writable_paths must be relative, got absolute path: {path}")
    for path in request.generated_paths:
        if not path:
            errors.append("generated_paths entries cannot be empty strings")
        elif path.startswith("..") or "/../" in path:
            errors.append(f"generated_paths must not escape project root with '..': {path}")
    return "; ".join(errors) if errors else None


def _sanitize_plan_output(raw_text: str) -> str:
    cleaned = re.sub(r"^.*\.claude/plans/.*$\n?", "", raw_text, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned
