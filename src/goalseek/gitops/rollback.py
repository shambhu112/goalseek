from __future__ import annotations

from goalseek.gitops.repo import Repo


def revert_commit(repo: Repo, commit_hash: str) -> str:
    return repo.revert(commit_hash)
