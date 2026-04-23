from __future__ import annotations

from pathlib import Path

import pytest

from goalseek.api import init_project


@pytest.fixture()
def project_factory(tmp_path):
    def factory(name: str = "demo") -> Path:
        root = Path(init_project(name, path=str(tmp_path), provider="fake", model="fake-model"))
        return root

    return factory
