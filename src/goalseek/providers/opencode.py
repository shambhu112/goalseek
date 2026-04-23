from __future__ import annotations

import shutil

from goalseek.models.config import ProviderSelection
from goalseek.providers.base import ProviderCapabilities
from goalseek.providers.codex import _run_cli


class OpenCodeProvider:
    name = "opencode"

    def capabilities(self, config: ProviderSelection) -> ProviderCapabilities:
        executable = config.executable or shutil.which("opencode")
        return ProviderCapabilities(
            available=bool(executable),
            supports_non_interactive=True,
            supports_split_prompts=True,
            executable=executable,
        )

    def plan(self, request):
        return _run_cli(request, self.capabilities(ProviderSelection(name="opencode", model=request.model_name)))

    def implement(self, request):
        return _run_cli(request, self.capabilities(ProviderSelection(name="opencode", model=request.model_name)))
