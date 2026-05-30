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


def test_codex_provider_advanced_config(project_factory):
    project_root = project_factory("codex-advanced-config")
    project_config = Path(project_root) / "config" / "project.yaml"
    project_config.write_text(
        """
provider:
  hypothesis:
    name: codex
    model: gpt-5-codex
    model_catalog_json: hidden/models-with-iris-alpha.json
    transport: sdk
    reuse_thread: true
    reasoning_effort: high
    parallel_runs:
      enabled: true
      candidates: 3
      selection: best_expected_metric
      isolate_worktrees: true
    deep_research:
      enabled: true
      model: o4-mini-deep-research
      max_sources: 8
      include_web: true
      include_mcp: true
    plugins:
      enabled: true
      requested:
        - github
        - openai-docs
    mcp:
      config_path: .codex/config.toml
      allowed_servers:
        - openaiDeveloperDocs
        - projectTools
  implementation:
    name: codex
    model: gpt-5-codex
    transport: cli
    reuse_thread: false
    reasoning_effort: medium
""".strip()
        + "\n",
        encoding="utf-8",
    )

    config = ProjectService().load_effective_config(project_root)

    assert config.provider.hypothesis.transport == "sdk"
    assert config.provider.hypothesis.model_catalog_json == "hidden/models-with-iris-alpha.json"
    assert config.provider.hypothesis.parallel_runs.enabled is True
    assert config.provider.hypothesis.parallel_runs.candidates == 3
    assert config.provider.hypothesis.deep_research.model == "o4-mini-deep-research"
    assert config.provider.hypothesis.plugins.requested == ["github", "openai-docs"]
    assert config.provider.hypothesis.mcp.allowed_servers == ["openaiDeveloperDocs", "projectTools"]
    assert config.provider.implementation.transport == "cli"
    assert config.provider.implementation.reuse_thread is False
