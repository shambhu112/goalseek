from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from goalseek.utils.json import append_jsonl, load_jsonl


class DirectionService:
    def add(
        self,
        project_root: str | Path,
        message: str,
        applies_from_iteration: int,
        source: str = "cli",
    ) -> dict:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "message": message,
            "source": source,
            "applies_from_iteration": applies_from_iteration,
        }
        append_jsonl(Path(project_root) / "logs" / "directions.jsonl", record)
        return record

    def list(self, project_root: str | Path) -> list[dict]:
        return load_jsonl(Path(project_root) / "logs" / "directions.jsonl")

    def active_for_iteration(self, project_root: str | Path, iteration: int) -> list[dict]:
        return [
            item
            for item in self.list(project_root)
            if item.get("applies_from_iteration", 0) <= iteration
        ]
