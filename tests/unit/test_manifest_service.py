from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from goalseek.core.manifest_service import ManifestService
from goalseek.errors import ManifestValidationError


def test_manifest_validation_rejects_overlap(project_factory):
    project_root = project_factory("overlap")
    manifest_path = Path(project_root) / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["files"].append({"path": "experiment.py", "mode": "read_only"})
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    with pytest.raises(ManifestValidationError):
        ManifestService().validate(project_root)


def test_manifest_validation_supports_hidden_mode_and_tracks_it(project_factory):
    project_root = project_factory("hidden-mode")
    scope = ManifestService().validate(project_root)

    assert "hidden/**" in scope.hidden_patterns
    assert "hidden/**" not in scope.read_only_patterns


def test_manifest_validation_rejects_hidden_overlap(project_factory):
    project_root = project_factory("hidden-overlap")
    manifest_path = Path(project_root) / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["files"].append({"path": "config/**", "mode": "hidden"})
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    with pytest.raises(ManifestValidationError):
        ManifestService().validate(project_root)


def test_manifest_validation_requires_metric(project_factory):
    project_root = project_factory("metric-missing")
    manifest_path = Path(project_root) / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("metric")
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    with pytest.raises(ManifestValidationError):
        ManifestService().validate(project_root)
