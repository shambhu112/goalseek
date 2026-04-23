from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class FileMode(str, Enum):
    READ_ONLY = "read_only"
    WRITABLE = "writable"
    GENERATED = "generated"
    HIDDEN = "hidden"


class FileRule(BaseModel):
    path: str
    mode: FileMode

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("file path cannot be empty")
        return value


class VerificationCommand(BaseModel):
    name: str
    run: str
    cwd: str = "."
    timeout_sec: int = 1800


class VerificationSection(BaseModel):
    commands: list[VerificationCommand] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_commands(self) -> "VerificationSection":
        if not self.commands:
            raise ValueError("at least one verification command is required")
        return self


class MetricExtractorType(str, Enum):
    JSON_FILE = "json_file"
    STDOUT_REGEX = "stdout_regex"
    STDERR_REGEX = "stderr_regex"


class MetricExtractor(BaseModel):
    type: MetricExtractorType
    path: str | None = None
    json_pointer: str | None = None
    regex: str | None = None

    @model_validator(mode="after")
    def ensure_required_fields(self) -> "MetricExtractor":
        if self.type == MetricExtractorType.JSON_FILE:
            if not self.path or not self.json_pointer:
                raise ValueError("json_file extraction requires path and json_pointer")
        else:
            if not self.regex:
                raise ValueError("regex extraction requires regex")
        return self


class MetricConfig(BaseModel):
    name: str = "score"
    direction: Literal["maximize", "minimize"]
    extractor: MetricExtractor
    epsilon: float = 0.0
    tie_breaker: Literal["changed_loc"] = "changed_loc"
    min_pass: float | None = None
    max_pass: float | None = None


class ManifestProject(BaseModel):
    name: str
    description: str = ""


class ExecutionConfig(BaseModel):
    target: Literal["local"] = "local"


class ProjectManifest(BaseModel):
    version: int
    project: ManifestProject
    files: list[FileRule]
    verification: VerificationSection
    metric: MetricConfig
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)

    @model_validator(mode="after")
    def validate_contract(self) -> "ProjectManifest":
        if self.version != 1:
            raise ValueError("unsupported manifest version")
        if not self.files:
            raise ValueError("manifest must define files")
        return self
