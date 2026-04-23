from __future__ import annotations

from pathlib import Path

from goalseek.gitops.repo import Repo


def test_repo_can_commit_and_measure_changed_loc(project_factory):
    project_root = project_factory("repo")
    repo = Repo(project_root)
    experiment = Path(project_root) / "experiment.py"
    experiment.write_text(experiment.read_text(encoding="utf-8") + "\n# change\n", encoding="utf-8")
    commit_hash = repo.commit(["experiment.py"], "test: repo commit")
    assert commit_hash
    assert repo.changed_loc_for_commit(commit_hash) > 0
