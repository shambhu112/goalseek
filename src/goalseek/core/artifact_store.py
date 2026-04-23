from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from goalseek.utils.json import append_jsonl, dump_json_atomic


class ArtifactStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.runs_dir = self.project_root / "runs"
        self.logs_dir = self.project_root / "logs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def baseline_dir(self) -> Path:
        path = self.runs_dir / "0000_baseline"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def iteration_dir(self, iteration: int) -> Path:
        path = self.runs_dir / f"{iteration:04d}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_text(self, run_dir: Path, name: str, content: str) -> Path:
        target = run_dir / name
        target.write_text(content, encoding="utf-8")
        return target

    def write_json(self, run_dir: Path, name: str, payload: Any) -> Path:
        target = run_dir / name
        dump_json_atomic(target, payload)
        return target

    def copy_file(self, run_dir: Path, source: Path, name: str | None = None) -> Path:
        target = run_dir / (name or source.name)
        shutil.copy2(source, target)
        return target

    def append_result(self, payload: dict[str, Any]) -> None:
        append_jsonl(self.logs_dir / "results.jsonl", payload)

    def append_direction(self, payload: dict[str, Any]) -> None:
        append_jsonl(self.logs_dir / "directions.jsonl", payload)
