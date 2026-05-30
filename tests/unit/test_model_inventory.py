from __future__ import annotations

from goalseek.models.model_inventory import ModelInventory, ModelInventoryEntry


def test_model_inventory_returns_codex_models():
    inventory = ModelInventory()

    assert inventory.list_models("Codex Provider") == [
        ModelInventoryEntry(provider="codex", slug="gpt-5.5", display_name="GPT-5.5"),
        ModelInventoryEntry(provider="codex", slug="gpt-5.4", display_name="gpt-5.4"),
        ModelInventoryEntry(provider="codex", slug="gpt-5.4-mini", display_name="GPT-5.4-Mini"),
        ModelInventoryEntry(provider="codex", slug="gpt-5.3-codex", display_name="gpt-5.3-codex"),
        ModelInventoryEntry(provider="codex", slug="gpt-5.2", display_name="gpt-5.2"),
        ModelInventoryEntry(provider="codex", slug="codex-auto-review", display_name="Codex Auto Review"),
        ModelInventoryEntry(provider="codex", slug="iris-alpha", display_name="iris-alpha"),
    ]
    assert inventory.slugs("codex") == [
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.3-codex",
        "gpt-5.2",
        "codex-auto-review",
        "iris-alpha",
    ]
    assert inventory.get_display_name("codex", "iris-alpha") == "iris-alpha"
    assert inventory.get_slug("codex", "iris-alpha") == "iris-alpha"


def test_model_inventory_returns_anthropic_models():
    inventory = ModelInventory()

    assert inventory.get_display_name("anthropic", "claude-opus-4-7") == "Claude Opus 4.7"
    assert inventory.get_display_name("claude_code", "claude-sonnet-4-6") == "Claude Sonnet 4.6"
    assert inventory.get_display_name("Anthopic Provider", "claude-opus-4-6") == "Claude Opus 4.6"
    assert inventory.get_slug("claude", "Claude Haiku 4.5") == "claude-haiku-4-5-20251001"
    assert "claude-opus-4-6" in inventory.slugs("anthropic")
    assert "Claude Sonnet 4.5" in inventory.display_names("anthropic")


def test_model_inventory_returns_empty_for_unknown_provider():
    assert ModelInventory().list_models("unknown") == []
