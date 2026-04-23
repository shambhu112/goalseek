from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProjectPaths(BaseModel):
    root: Path
    manifest: Path
    program: Path
    setup_script: Path
    experiment: Path
    config_dir: Path
    runs_dir: Path
    logs_dir: Path


class ContextFile(BaseModel):
    path: str
    sha256: str
    size: int
    content: str


class ContextBundle(BaseModel):
    files: list[ContextFile] = Field(default_factory=list)
    latest_results: list[dict[str, Any]] = Field(default_factory=list)
    directions: list[dict[str, Any]] = Field(default_factory=list)
    git_log: str = ""
    git_diff: str = ""


class SetupSummary(BaseModel):
    project_root: str
    project_name: str
    provider: str
    model: str
    writable_files: list[str]
    read_only_files: list[str]
    generated_paths: list[str]
    hidden_paths: list[str]
    verification_commands: list[str]
    metric_name: str
    metric_direction: str
    execution_target: str
    non_interactive: bool


class EnvironmentSnapshot(BaseModel):
    os_name: str
    platform: str
    python_version: str
    cwd: str
    provider_name: str
    model_name: str
    effective_config: dict[str, Any]
    command_versions: dict[str, str | None]
