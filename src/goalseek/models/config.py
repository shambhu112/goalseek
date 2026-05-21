from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


ProviderName = Literal["codex", "claude_code", "opencode", "gemini", "fake"]
CodexTransport = Literal["auto", "sdk", "cli"]


class CodexParallelRunsConfig(BaseModel):
    enabled: bool = False
    candidates: int = 3
    selection: str = "best_expected_metric"
    isolate_worktrees: bool = True


class CodexDeepResearchConfig(BaseModel):
    enabled: bool = False
    model: str = "o4-mini-deep-research"
    max_sources: int = 8
    include_web: bool = True
    include_mcp: bool = True


class CodexPluginsConfig(BaseModel):
    enabled: bool = False
    requested: list[str] = Field(default_factory=list)


class CodexMcpConfig(BaseModel):
    config_path: str = ".codex/config.toml"
    allowed_servers: list[str] = Field(default_factory=list)


class ProviderSelection(BaseModel):
    name: ProviderName = "codex"
    model: str = "default"
    non_interactive: bool = True
    timeout_sec: int = 1800
    executable: str | None = None
    extra_args: list[str] = Field(default_factory=list)
    transport: CodexTransport = "auto"
    reuse_thread: bool = True
    reasoning_effort: str | None = None
    parallel_runs: CodexParallelRunsConfig = Field(default_factory=CodexParallelRunsConfig)
    deep_research: CodexDeepResearchConfig = Field(default_factory=CodexDeepResearchConfig)
    plugins: CodexPluginsConfig = Field(default_factory=CodexPluginsConfig)
    mcp: CodexMcpConfig = Field(default_factory=CodexMcpConfig)


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
