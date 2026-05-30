from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

import pytest

from goalseek.models.config import ProviderSelection
from goalseek.models.model_inventory import ModelInventory
from goalseek.providers.base import ProviderRequest
from goalseek.providers.codex import CodexProvider


CATALOG_MODEL = "iris-alpha"
SUCCESS_TEXT = "goalseek live model catalog ok"
MODEL_HEADER_RE = re.compile(r"(?m)^model:\s*(?P<model>\S+)")
MODEL_ERROR_RE = re.compile(r"The model `(?P<model>[^`]+)`")


def _catalog_path(project_root: Path) -> Path:
    catalog_path = project_root / "codex-model-catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "models": [
                    {"slug": model.slug, "display_name": model.display_name}
                    for model in ModelInventory().list_models("codex")
                ]
            }
        ),
        encoding="utf-8",
    )
    return catalog_path


def _request(project_root: Path, transport: str) -> ProviderRequest:
    catalog_path = _catalog_path(project_root)
    return ProviderRequest(
        project_root=project_root,
        provider_name="codex",
        model_name=CATALOG_MODEL,
        mode="hypothesis",
        prompt_text=f"Reply with exactly: {SUCCESS_TEXT}",
        writable_paths=["experiment.py"],
        generated_paths=["runs/**", "logs/**"],
        non_interactive=True,
        timeout_sec=180,
        iteration=1,
        metadata={
            "provider_config": ProviderSelection(
                name="codex",
                model=CATALOG_MODEL,
                model_catalog_json=str(catalog_path),
                transport=transport,
            )
        },
    )


def _require_live_sdk() -> None:
    if os.environ.get("GOALSEEK_LIVE_CODEX") != "1":
        pytest.skip("set GOALSEEK_LIVE_CODEX=1 to run live Codex model_catalog_json SDK test")
    if CATALOG_MODEL not in ModelInventory().slugs("codex"):
        pytest.skip(f"missing {CATALOG_MODEL} in ModelInventory Codex models")
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("set OPENAI_API_KEY to run live Codex model_catalog_json SDK test")
    try:
        import openai_codex  # noqa: F401
    except Exception as exc:
        pytest.skip(f"openai_codex unavailable: {exc}")


def _require_live_cli() -> None:
    if os.environ.get("GOALSEEK_LIVE_CODEX") != "1":
        pytest.skip("set GOALSEEK_LIVE_CODEX=1 to run live Codex model_catalog_json CLI test")
    if CATALOG_MODEL not in ModelInventory().slugs("codex"):
        pytest.skip(f"missing {CATALOG_MODEL} in ModelInventory Codex models")
    if shutil.which("codex") is None:
        pytest.skip("codex executable not found in PATH")


def _server_model_name(response) -> str:
    raw_output = "\n".join(
        str(part)
        for part in (
            response.metadata.get("server_model", ""),
            response.raw_text,
            response.error or "",
        )
        if part
    )
    for pattern in (MODEL_HEADER_RE, MODEL_ERROR_RE):
        match = pattern.search(raw_output)
        if match:
            return match.group("model")
    return "<server model not reported>"


@pytest.mark.live
def test_live_codex_provider_sdk_uses_model_catalog_json(tmp_path):
    _require_live_sdk()

    response = CodexProvider().plan(_request(tmp_path, "sdk"))
    print(f"Live Codex model in use: {_server_model_name(response)}")

    assert response.exit_code == 0, response.error
    assert response.error is None
    assert response.metadata["transport"] == "sdk"
    assert SUCCESS_TEXT in response.raw_text.lower()


@pytest.mark.live
def test_live_codex_provider_cli_uses_model_catalog_json(tmp_path):
    _require_live_cli()

    response = CodexProvider().plan(_request(tmp_path, "cli"))
    print(f"Live Codex model in use: {_server_model_name(response)}")

    assert response.exit_code == 0, response.error or response.raw_text
    assert response.error is None
    assert response.metadata["transport"] == "cli"
    assert SUCCESS_TEXT in response.raw_text.lower()
