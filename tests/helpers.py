from __future__ import annotations

from pathlib import Path

import yaml

from goalseek.gitops.repo import Repo


def write_fake_provider(project_root: Path, scenario_name: str) -> None:
    fixtures_dir = Path(__file__).parent / "fixtures"
    content = (fixtures_dir / scenario_name).read_text(encoding="utf-8")
    target = project_root / "config" / "fake_provider.yaml"
    target.write_text(content, encoding="utf-8")
    Repo(project_root).commit(["config/fake_provider.yaml"], "test: add fake provider scenario")


def write_fake_provider_data(project_root: Path, data: dict) -> None:
    target = project_root / "config" / "fake_provider.yaml"
    target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    Repo(project_root).commit(["config/fake_provider.yaml"], "test: add fake provider scenario")
