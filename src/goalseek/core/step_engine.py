from __future__ import annotations

from pathlib import Path
from typing import Any

from goalseek.core.loop_engine import LoopEngine
from goalseek.core.state_store import StateStore


class StepEngine:
    def __init__(self) -> None:
        self.loop_engine = LoopEngine()

    def step(self, project_root: str | Path, overrides: dict[str, Any] | None = None, stream_callback=None) -> dict:
        root = Path(project_root).expanduser().resolve()
        state = self.loop_engine.initialize_or_load_state(root, overrides)
        updated = self.loop_engine.execute_phase(root, state, overrides, stream_callback=stream_callback)
        StateStore(root).save(updated)
        return updated.model_dump(mode="python")
