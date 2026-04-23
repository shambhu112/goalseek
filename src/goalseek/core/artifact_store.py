from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from goalseek.models.results import HistoryRecord
from goalseek.utils.json import append_jsonl, dump_json_atomic, load_json, load_jsonl


class ArtifactStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.runs_dir = self.project_root / "runs"
        self.latest_dir = self.runs_dir / "latest"
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

    def refresh_latest_history(self) -> Path:
        history = [
            self._history_entry(record).model_dump(mode="python")
            for record in load_jsonl(self.logs_dir / "results.jsonl")
        ]
        target = self.latest_dir / "history.json"
        dump_json_atomic(target, history)
        return target

    def _history_entry(self, record: dict[str, Any]) -> HistoryRecord:
        run_dir_value = record.get("run_dir", "")
        run_dir = self.project_root / run_dir_value if isinstance(run_dir_value, str) else self.project_root
        iteration = record.get("iteration", 0)
        outcome = record.get("outcome", "baseline")
        return HistoryRecord(
            iteration=iteration,
            run_dir=run_dir_value if isinstance(run_dir_value, str) else "",
            hypothesis_summary=self._resolve_hypothesis_summary(record, run_dir),
            iteration_score=record.get("metric_value"),
            iteration_result=outcome,
        )

    def _resolve_hypothesis_summary(self, record: dict[str, Any], run_dir: Path) -> str:
        summary = record.get("hypothesis_summary")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
        result_payload = load_json(run_dir / "result.json", default={})
        if isinstance(result_payload, dict):
            persisted = result_payload.get("hypothesis_summary")
            if isinstance(persisted, str) and persisted.strip():
                return persisted.strip()
        if record.get("iteration") == 0 or record.get("outcome") == "baseline":
            return "Baseline"
        plan_path = run_dir / "plan.md"
        if plan_path.exists():
            plan_text = plan_path.read_text(encoding="utf-8")
            title = _extract_heading(plan_text)
            if title:
                return title
        iteration = record.get("iteration")
        if isinstance(iteration, int):
            return f"Iteration {iteration}"
        return "Iteration"


def _extract_heading(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
        return stripped
    return None
