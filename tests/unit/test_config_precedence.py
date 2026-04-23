from __future__ import annotations

from pathlib import Path

from goalseek.core.project_service import ProjectService


def test_config_precedence(monkeypatch, project_factory, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    global_config = home / ".config" / "goalseek" / "config.yaml"
    global_config.parent.mkdir(parents=True, exist_ok=True)
    global_config.write_text(
        """
provider:
  implementation:
    name: codex
    model: global-model
""".strip()
        + "\n",
        encoding="utf-8",
    )
    project_root = project_factory("config-precedence")
    project_config = Path(project_root) / "config" / "project.yaml"
    project_config.write_text(
        """
provider:
  implementation:
    name: fake
    model: project-model
""".strip()
        + "\n",
        encoding="utf-8",
    )
    config = ProjectService().load_effective_config(project_root, {"model": "cli-model"})
    assert config.provider.implementation.name == "fake"
    assert config.provider.implementation.model == "cli-model"


def test_logging_config_precedence(monkeypatch, project_factory, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    global_config = home / ".config" / "goalseek" / "config.yaml"
    global_config.parent.mkdir(parents=True, exist_ok=True)
    global_config.write_text(
        """
logging:
  enabled: true
  level: DEBUG
  handlers:
    - type: stdout
""".strip()
        + "\n",
        encoding="utf-8",
    )
    project_root = project_factory("logging-precedence")
    project_config = Path(project_root) / "config" / "project.yaml"
    project_config.write_text(
        """
logging:
  enabled: true
  level: INFO
  handlers:
    - type: file
      path: logs/project.log
""".strip()
        + "\n",
        encoding="utf-8",
    )

    config = ProjectService().load_effective_config(project_root)

    assert config.logging.enabled is True
    assert config.logging.level == "INFO"
    assert len(config.logging.handlers) == 1
    assert config.logging.handlers[0].type == "file"
