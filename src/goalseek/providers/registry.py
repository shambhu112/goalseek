from __future__ import annotations

from goalseek.errors import ConfigError
from goalseek.providers.claude_code import ClaudeCodeProvider
from goalseek.providers.codex import CodexProvider
from goalseek.providers.fake import FakeProvider
from goalseek.providers.gemini import GeminiProvider
from goalseek.providers.opencode import OpenCodeProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers = {
            "codex": CodexProvider(),
            "claude_code": ClaudeCodeProvider(),
            "opencode": OpenCodeProvider(),
            "gemini": GeminiProvider(),
            "fake": FakeProvider(),
        }

    def get(self, name: str):
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ConfigError(f"unknown provider: {name}") from exc
