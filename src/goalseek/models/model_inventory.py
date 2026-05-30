from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelInventoryEntry:
    provider: str
    slug: str
    display_name: str


class ModelInventory:
    _CODEX_MODELS: tuple[tuple[str, str], ...] = (
        ("gpt-5.5", "GPT-5.5"),
        ("gpt-5.4", "gpt-5.4"),
        ("gpt-5.4-mini", "GPT-5.4-Mini"),
        ("gpt-5.3-codex", "gpt-5.3-codex"),
        ("gpt-5.2", "gpt-5.2"),
        ("codex-auto-review", "Codex Auto Review"),
        ("iris-alpha", "iris-alpha"),
    )
    _ANTHROPIC_MODELS: tuple[tuple[str, str], ...] = (
        ("claude-opus-4-7", "Claude Opus 4.7"),
        ("claude-opus-4-6", "Claude Opus 4.6"),
        ("claude-opus-4-5-20251101", "Claude Opus 4.5"),
        ("claude-opus-4-1-20250805", "Claude Opus 4.1"),
        ("claude-sonnet-4-6", "Claude Sonnet 4.6"),
        ("claude-sonnet-4-5-20250929", "Claude Sonnet 4.5"),
        ("claude-haiku-4-5-20251001", "Claude Haiku 4.5"),
        ("claude-haiku-4-5", "Claude Haiku 4.5"),
    )

    def list_models(self, provider: str) -> list[ModelInventoryEntry]:
        normalized_provider = self._normalize_provider(provider)
        if normalized_provider == "codex":
            return self._codex_models()
        if normalized_provider == "anthropic":
            return [
                ModelInventoryEntry(provider=normalized_provider, slug=slug, display_name=display_name)
                for slug, display_name in self._ANTHROPIC_MODELS
            ]
        return []

    def slugs(self, provider: str) -> list[str]:
        return [model.slug for model in self.list_models(provider)]

    def display_names(self, provider: str) -> list[str]:
        return [model.display_name for model in self.list_models(provider)]

    def get(self, provider: str, slug: str) -> ModelInventoryEntry | None:
        return next((model for model in self.list_models(provider) if model.slug == slug), None)

    def get_slug(self, provider: str, display_name: str) -> str | None:
        match = next((model for model in self.list_models(provider) if model.display_name == display_name), None)
        return match.slug if match else None

    def get_display_name(self, provider: str, slug: str) -> str | None:
        match = self.get(provider, slug)
        return match.display_name if match else None

    def _codex_models(self) -> list[ModelInventoryEntry]:
        return [
            ModelInventoryEntry(provider="codex", slug=slug, display_name=display_name)
            for slug, display_name in self._CODEX_MODELS
        ]

    @staticmethod
    def _normalize_provider(provider: str) -> str:
        normalized = provider.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized.endswith("_provider"):
            normalized = normalized.removesuffix("_provider")
        if normalized in {"anthropic", "anthopic", "claude", "claude_code"}:
            return "anthropic"
        return normalized
