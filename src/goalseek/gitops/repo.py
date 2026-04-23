from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from goalseek.errors import GitOperationError, ProjectStateError


class Repo:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def is_git_available(self) -> bool:
        return shutil.which("git") is not None

    def is_repo(self) -> bool:
        if not self.is_git_available():
            raise GitOperationError("git is not available")
        result = self._run(["rev-parse", "--is-inside-work-tree"], check=False)
        return result.returncode == 0 and result.stdout.strip() == "true"

    def init(self) -> None:
        self._run(["init"])

    def ensure_clean(self) -> None:
        status = self.status_porcelain()
        if status:
            raise ProjectStateError("working tree must be clean before applying a change")

    def status_porcelain(self) -> list[str]:
        result = self._run(["status", "--porcelain"], check=False)
        return [line for line in result.stdout.splitlines() if line.strip()]

    def head(self) -> str | None:
        result = self._run(["rev-parse", "HEAD"], check=False)
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def recent_log(self, count: int = 20) -> str:
        result = self._run(["log", f"-n{count}", "--oneline", "--decorate"], check=False)
        return result.stdout

    def diff_summary(self) -> str:
        status = self._run(["status", "--short"], check=False).stdout
        diff = self._run(["diff", "--stat"], check=False).stdout
        return f"{status}\n{diff}".strip()

    def working_tree_changed_files(self) -> list[str]:
        result = self._run(["status", "--porcelain"], check=False)
        files: list[str] = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            files.append(line[3:].strip())
        return files

    def commit(self, paths: list[str], message: str) -> str:
        if not paths:
            raise GitOperationError("no paths provided for commit")
        self._run(["add", "--", *paths])
        self._run(["commit", "-m", message])
        head = self.head()
        if not head:
            raise GitOperationError("commit did not produce a new HEAD")
        return head

    def commit_all(self, message: str) -> str:
        self._run(["add", "."])
        self._run(["commit", "-m", message])
        head = self.head()
        if not head:
            raise GitOperationError("commit did not produce a new HEAD")
        return head

    def revert(self, commit_hash: str) -> str:
        self._run(["revert", "--no-edit", commit_hash])
        head = self.head()
        if not head:
            raise GitOperationError("revert did not produce a new HEAD")
        return head

    def show(self, rev: str) -> str:
        return self._run(["show", "--stat", "--summary", rev], check=False).stdout

    def changed_loc_for_commit(self, commit_hash: str) -> int:
        output = self._run(["show", "--numstat", "--format=", commit_hash], check=False).stdout
        total = 0
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            try:
                total += int(parts[0]) + int(parts[1])
            except ValueError:
                continue
        return total

    def _run(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
        command = [
            "git",
            "-c",
            "user.name=goalseek",
            "-c",
            "user.email=goalseek@example.invalid",
            *args,
        ]
        result = subprocess.run(
            command,
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            raise GitOperationError(result.stderr.strip() or result.stdout.strip() or "git command failed")
        return result
