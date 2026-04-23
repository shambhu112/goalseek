from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


ProviderName = Literal["codex", "claude_code", "opencode", "gemini", "fake"]


class ProviderSelection(BaseModel):
    name: ProviderName = "codex"
    model: str = "gpt-5-codex"
    non_interactive: bool = True
    timeout_sec: int = 1800
    executable: str | None = None
    extra_args: list[str] = Field(default_factory=list)


class ProviderModes(BaseModel):
    hypothesis: ProviderSelection = Field(default_factory=ProviderSelection)
    implementation: ProviderSelection = Field(default_factory=ProviderSelection)


class LoopConfig(BaseModel):
    repair_attempts: int = 1
    stagnation_window: int = 3


class OutputConfig(BaseModel):
    rich: bool = True


class LoggingHandlerBase(BaseModel):
    level: str | None = None


class StdoutLoggingHandler(LoggingHandlerBase):
    type: Literal["stdout", "sys.stdout"] = "stdout"


class FileLoggingHandler(LoggingHandlerBase):
    type: Literal["file"] = "file"
    path: str = "logs/goalseek.log"
    mode: Literal["a", "w"] = "a"


class CloudWatchLoggingHandler(LoggingHandlerBase):
    type: Literal["cloudwatch"] = "cloudwatch"
    log_group: str
    stream_name: str = "{project_name}"
    region_name: str | None = None
    create_log_group: bool = True


LoggingHandler = Annotated[
    StdoutLoggingHandler | FileLoggingHandler | CloudWatchLoggingHandler,
    Field(discriminator="type"),
]


class LoggingConfig(BaseModel):
    enabled: bool = False
    level: str = "INFO"
    format: str = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    datefmt: str | None = None
    handlers: list[LoggingHandler] = Field(default_factory=lambda: [StdoutLoggingHandler()])


class EffectiveConfig(BaseModel):
    provider: ProviderModes = Field(default_factory=ProviderModes)
    loop: LoopConfig = Field(default_factory=LoopConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
