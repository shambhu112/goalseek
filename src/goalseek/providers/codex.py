from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

from goalseek.models.config import ProviderSelection
from goalseek.providers.base import ProviderCapabilities, ProviderRequest, ProviderResponse
from goalseek.utils.subprocess import run_command


logger = logging.getLogger(__name__)


class CodexProvider:
    name = "codex"

    def capabilities(self, config: ProviderSelection) -> ProviderCapabilities:
        executable = config.executable or shutil.which("codex")
        return ProviderCapabilities(
            available=bool(executable),
            supports_non_interactive=True,
            supports_split_prompts=True,
            executable=executable,
        )

    def plan(self, request: ProviderRequest) -> ProviderResponse:
        return _run_cli(request, self.capabilities(ProviderSelection(name="codex", model=request.model_name)))

    def implement(self, request: ProviderRequest) -> ProviderResponse:
        return _run_cli(request, self.capabilities(ProviderSelection(name="codex", model=request.model_name)))


def _run_cli(
    request: ProviderRequest,
    capabilities: ProviderCapabilities,
    env: dict[str, str] | None = None,
) -> ProviderResponse:
    start = time.time()
    if not capabilities.executable:
        return ProviderResponse(
            raw_text="",
            exit_code=1,
            duration_sec=0.0,
            error="executable not found",
        )
    logger.info(
        "Running provider=%s mode=%s model=%s iteration=%s",
        request.provider_name,
        request.mode,
        request.model_name,
        request.iteration,
    )
    result = run_command(
        [capabilities.executable, request.prompt_text],
        cwd=Path(request.project_root),
        timeout_sec=request.timeout_sec,
        env=env,
    )
    logger.info(
        "Provider=%s mode=%s finished exit_code=%s",
        request.provider_name,
        request.mode,
        result.exit_code,
    )
    return ProviderResponse(
        raw_text=result.stdout or result.stderr,
        exit_code=result.exit_code,
        duration_sec=time.time() - start,
        changed_files=[],
        error=None if result.exit_code == 0 else result.stderr.strip(),
    )
