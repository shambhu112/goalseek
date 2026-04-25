from __future__ import annotations

from pathlib import Path

import pytest

from goalseek.errors import GitOperationError
from goalseek.gitops.repo import Repo


def test_repo_can_commit_and_measure_changed_loc(project_factory):
    project_root = project_factory("repo")
    repo = Repo(project_root)
    experiment = Path(project_root) / "experiment.py"
    experiment.write_text(experiment.read_text(encoding="utf-8") + "\n# change\n", encoding="utf-8")
    commit_hash = repo.commit(["experiment.py"], "test: repo commit")
    assert commit_hash
    assert repo.changed_loc_for_commit(commit_hash) > 0


def test_repo_commit_then_commit_same_file_again(project_factory):
    project_root = project_factory("repo")
    repo = Repo(project_root)
    experiment = Path(project_root) / "experiment.py"

    # First commit: add a line
    experiment.write_text(experiment.read_text(encoding="utf-8") + "\n# first change\n", encoding="utf-8")
    commit_hash_1 = repo.commit(["experiment.py"], "test: first commit")
    assert commit_hash_1
    loc_1 = repo.changed_loc_for_commit(commit_hash_1)
    assert loc_1 > 0

    # Second commit: modify the same file again
    experiment.write_text(experiment.read_text(encoding="utf-8") + "\n# second change\n", encoding="utf-8")
    commit_hash_2 = repo.commit(["experiment.py"], "test: second commit")
    assert commit_hash_2
    loc_2 = repo.changed_loc_for_commit(commit_hash_2)
    assert loc_2 > 0

    # Verify both hashes are different and LOC values are valid
    assert commit_hash_1 != commit_hash_2
    assert loc_1 > 0 and loc_2 > 0


def test_repo_commit_with_empty_file_list(project_factory):
    project_root = project_factory("repo")
    repo = Repo(project_root)
    with pytest.raises(GitOperationError):
        repo.commit([], "test: empty file list")


def test_repo_changed_loc_for_very_old_commit(project_factory):
    project_root = project_factory("repo")
    repo = Repo(project_root)
    experiment = Path(project_root) / "experiment.py"

    # Create multiple commits to build history
    commit_hashes = []
    for i in range(5):
        experiment.write_text(experiment.read_text(encoding="utf-8") + f"\n# change {i}\n", encoding="utf-8")
        commit_hash = repo.commit(["experiment.py"], f"test: commit {i}")
        commit_hashes.append(commit_hash)

    # Verify we can correctly measure LOC for the first (oldest) commit
    loc_old = repo.changed_loc_for_commit(commit_hashes[0])
    assert loc_old > 0

    # Verify we can measure the most recent commit
    loc_recent = repo.changed_loc_for_commit(commit_hashes[-1])
    assert loc_recent > 0


def test_repo_handles_file_with_special_chars_in_path(project_factory):
    project_root = project_factory("repo")
    repo = Repo(project_root)

    # Create files with special characters in the name
    special_file = Path(project_root) / "test-file_with-special.py"
    special_file.write_text("# special file content\n")

    # Commit the special file
    commit_hash = repo.commit(["test-file_with-special.py"], "test: special chars in filename")
    assert commit_hash

    # Verify LOC can be measured
    loc = repo.changed_loc_for_commit(commit_hash)
    assert loc > 0


def test_repo_commit_after_reset_state(project_factory):
    project_root = project_factory("repo")
    repo = Repo(project_root)
    experiment = Path(project_root) / "experiment.py"

    # Initial commit
    experiment.write_text(experiment.read_text(encoding="utf-8") + "\n# initial\n", encoding="utf-8")
    commit_hash_1 = repo.commit(["experiment.py"], "test: initial commit")
    assert commit_hash_1

    # Reset the repo object (create a new one)
    repo = Repo(project_root)

    # Verify we can still work with the new repo object
    experiment.write_text(experiment.read_text(encoding="utf-8") + "\n# after reset\n", encoding="utf-8")
    commit_hash_2 = repo.commit(["experiment.py"], "test: after reset")
    assert commit_hash_2

    # Verify both commits are still measurable
    loc_1 = repo.changed_loc_for_commit(commit_hash_1)
    loc_2 = repo.changed_loc_for_commit(commit_hash_2)
    assert loc_1 > 0 and loc_2 > 0
