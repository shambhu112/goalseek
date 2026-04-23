from __future__ import annotations

from pathlib import Path

from goalseek.models.state import LoopPhase, LoopState, LoopStatus
from goalseek.utils.json import dump_json_atomic, load_json


class StateStore:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).expanduser().resolve()
        self.path = self.project_root / "logs" / "state.json"

    def load(self) -> LoopState | None:
        data = load_json(self.path)
        if not data:
            return None
        return LoopState.model_validate(data)

    def save(self, state: LoopState) -> LoopState:
        dump_json_atomic(self.path, state.model_dump(mode="python"))
        return state

    def initialize(
        self,
        provider: str,
        model: str,
        retained_metric: float | None = None,
        retained_changed_loc: int | None = 0,
        last_outcome: str | None = None,
    ) -> LoopState:
        state = LoopState(
            status=LoopStatus.READY,
            current_iteration=1,
            current_phase=LoopPhase.READ_CONTEXT,
            provider=provider,
            model=model,
            retained_metric=retained_metric,
            retained_changed_loc=retained_changed_loc,
            last_outcome=last_outcome,
        )
        return self.save(state)
