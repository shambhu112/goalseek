from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LoopStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


class LoopPhase(str, Enum):
    READ_CONTEXT = "READ_CONTEXT"
    PLAN = "PLAN"
    APPLY_CHANGE = "APPLY_CHANGE"
    COMMIT = "COMMIT"
    VERIFY = "VERIFY"
    DECIDE = "DECIDE"
    LOG = "LOG"


class IterationPayload(BaseModel):
    run_dir: str | None = None
    plan_text: str | None = None
    prompt_text: str | None = None
    provider_output: str | None = None
    result_discussion: str | None = None
    planned_files: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    commit_hash: str | None = None
    parent_commit_hash: str | None = None
    rollback_commit_hash: str | None = None
    verification_exit_code: int | None = None
    verification_log: str | None = None
    verification_command_names: list[str] = Field(default_factory=list)
    metric_value: float | None = None
    repair_attempted: bool = False
    notes: str | None = None
    git_before: str | None = None
    git_after: str | None = None
    environment: dict[str, Any] = Field(default_factory=dict)
    context_summary: dict[str, Any] = Field(default_factory=dict)
    changed_loc: int | None = None
    plan_title: str | None = None
    decision_outcome: str | None = None


class LoopState(BaseModel):
    status: LoopStatus = LoopStatus.READY
    current_iteration: int = 1
    current_phase: LoopPhase = LoopPhase.READ_CONTEXT
    provider: str
    model: str
    pending_commit: str | None = None
    rollback_state: str = "not_needed"
    retained_metric: float | None = None
    retained_changed_loc: int | None = None
    last_outcome: str | None = None
    iteration_data: IterationPayload = Field(default_factory=IterationPayload)
