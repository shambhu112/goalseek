from __future__ import annotations

from pathlib import Path

from goalseek.core.direction_service import DirectionService
from goalseek.utils.json import load_jsonl


class SummaryService:
    def build(self, project_root: str | Path) -> dict:
        root = Path(project_root).expanduser().resolve()
        results = load_jsonl(root / "logs" / "results.jsonl")
        directions = DirectionService().list(root)
        baseline = next((item for item in results if item.get("outcome") == "baseline"), None)
        kept = [item for item in results if item.get("outcome") == "kept"]
        reverted = [item for item in results if item.get("outcome", "").startswith("reverted")]
        skipped = [item for item in results if item.get("outcome", "").startswith("skipped")]
        best = None
        for item in [baseline, *kept]:
            if not item or item.get("metric_value") is None:
                continue
            if best is None or item["metric_value"] > best["metric_value"]:
                best = item
        non_kept_streak = _non_kept_streak(results)
        recommendations: list[str] = []
        if non_kept_streak >= 3:
            recommendations.append("Recent attempts stalled. Broaden the next single-change hypothesis.")
        if directions:
            recommendations.append(f"Latest direction: {directions[-1]['message']}")
        if not recommendations:
            recommendations.append("Continue with the next focused change.")
        return {
            "baseline_metric": baseline.get("metric_value") if baseline else None,
            "best_retained_metric": best.get("metric_value") if best else None,
            "best_iteration": best.get("iteration") if best else None,
            "kept_iterations": len(kept),
            "reverted_iterations": len(reverted),
            "skipped_iterations": len(skipped),
            "latest_active_direction": directions[-1] if directions else None,
            "stagnation_indicators": {"non_kept_streak": non_kept_streak},
            "recommendations": recommendations,
        }


def _non_kept_streak(results: list[dict]) -> int:
    streak = 0
    for item in reversed(results):
        if item.get("outcome") == "baseline":
            break
        if item.get("outcome") == "kept":
            break
        streak += 1
    return streak
