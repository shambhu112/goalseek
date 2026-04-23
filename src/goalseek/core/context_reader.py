from __future__ import annotations

from pathlib import Path

from goalseek.core.direction_service import DirectionService
from goalseek.core.manifest_service import ManifestScope
from goalseek.gitops.repo import Repo
from goalseek.models.project import ContextBundle, ContextFile
from goalseek.utils.hashing import sha256_file
from goalseek.utils.json import load_jsonl


class ContextReader:
    def __init__(self, repo: Repo | None = None) -> None:
        self._repo = repo
        self._direction_service = DirectionService()

    def read(self, project_root: str | Path, scope: ManifestScope, iteration: int) -> ContextBundle:
        root = Path(project_root).expanduser().resolve()
        repo = self._repo or Repo(root)
        files: list[ContextFile] = []
        for path in scope.expand_existing_visible_files():
            files.append(
                ContextFile(
                    path=path.relative_to(root).as_posix(),
                    sha256=sha256_file(path),
                    size=path.stat().st_size,
                    content=path.read_text(encoding="utf-8", errors="replace"),
                )
            )
        results = load_jsonl(root / "logs" / "results.jsonl")
        return ContextBundle(
            files=files,
            latest_results=results[-5:],
            directions=self._direction_service.active_for_iteration(root, iteration),
            git_log=repo.recent_log(20),
            git_diff=repo.diff_summary(),
        )
