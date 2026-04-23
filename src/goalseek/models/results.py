from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Outcome = Literal[
    "baseline",
    "kept",
    "reverted_worse_metric",
    "reverted_threshold_failure",
    "reverted_scope_violation",
    "skipped_provider_failure",
    "skipped_verification_crash",
    "skipped_no_change",
]


class VerificationCommandResult(BaseModel):
    name: str
    exit_code: int
    duration_sec: float
    stdout: str
    stderr: str
    cwd: str


class MetricResult(BaseModel):
    name: str
    value: float
    direction: str
    thresholds_passed: bool = True
    delta: float | None = None
    extractor_type: str


class ResultRecord(BaseModel):
    timestamp: str
    iteration: int
    run_dir: str
    commit_hash: str | None = None
    parent_commit_hash: str | None = None
    provider: str
    model: str
    mode: str
    planned_files: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    outcome: Outcome
    verification_exit_code: int
    verification_command_names: list[str] = Field(default_factory=list)
    repair_attempted: bool = False
    rollback_commit_hash: str | None = None
    notes: str | None = None
    result_discussion: str | None = None
    hypothesis_summary: str | None = None
    metric_value: float | None = None
    changed_loc: int | None = None


class HistoryRecord(BaseModel):
    iteration: int
    run_dir: str
    hypothesis_summary: str
    iteration_score: float | None = None
    iteration_result: str
