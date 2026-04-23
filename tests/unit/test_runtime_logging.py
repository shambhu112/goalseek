from __future__ import annotations

import types

import pytest

from goalseek.errors import ConfigError
from goalseek.models.config import EffectiveConfig
from goalseek.runtime_logging import configure_package_logging


def test_configure_package_logging_writes_to_stdout_and_file(tmp_path, capsys):
    config = EffectiveConfig.model_validate(
        {
            "logging": {
                "enabled": True,
                "level": "INFO",
                "handlers": [
                    {"type": "stdout"},
                    {"type": "file", "path": "logs/runtime.log"},
                ],
            }
        }
    )

    configure_package_logging(config, tmp_path)

    import logging

    logging.getLogger("goalseek.test").info("hello logging")

    output = capsys.readouterr().out
    assert "hello logging" in output
    assert "hello logging" in (tmp_path / "logs" / "runtime.log").read_text(encoding="utf-8")


def test_cloudwatch_logging_requires_optional_dependencies(monkeypatch, tmp_path):
    config = EffectiveConfig.model_validate(
        {
            "logging": {
                "enabled": True,
                "handlers": [
                    {
                        "type": "cloudwatch",
                        "log_group": "/goalseek/tests",
                    }
                ],
            }
        }
    )

    def fake_import_module(name: str):
        if name in {"boto3", "watchtower"}:
            raise ImportError(name)
        return types.SimpleNamespace()

    monkeypatch.setattr("goalseek.runtime_logging.importlib.import_module", fake_import_module)

    with pytest.raises(ConfigError, match="cloudwatch logging requires optional dependencies"):
        configure_package_logging(config, tmp_path)
