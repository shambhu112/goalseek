from __future__ import annotations

from pathlib import Path

from goalseek.api import run_setup


def test_setup_writes_configured_file_log(project_factory):
    project_root = project_factory("logging-flow")
    project_config = Path(project_root) / "config" / "project.yaml"
    project_config.write_text(
        """
provider:
  hypothesis:
    name: fake
    model: fake-model
  implementation:
    name: fake
    model: fake-model

logging:
  enabled: true
  level: INFO
  handlers:
    - type: file
      path: logs/goalseek.log
""".strip()
        + "\n",
        encoding="utf-8",
    )

    run_setup(str(project_root))

    log_text = (Path(project_root) / "logs" / "goalseek.log").read_text(encoding="utf-8")
    assert "Starting setup for project" in log_text
    assert "Setup complete for project" in log_text
