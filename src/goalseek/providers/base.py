from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from goalseek.models.config import ProviderSelection


@dataclass
class ProviderCapabilities:
    available: bool
    supports_non_interactive: bool
    supports_split_prompts: bool
    executable: str | None = None


@dataclass
class ProviderRequest:
    project_root: Path
    provider_name: str
    model_name: str
    mode: str
    prompt_text: str
    writable_paths: list[str]
    generated_paths: list[str]
    non_interactive: bool
    timeout_sec: int
    iteration: int
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class ProviderResponse:
    raw_text: str
    exit_code: int
    duration_sec: float
    changed_files: list[str] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


class ProviderAdapter(Protocol):
    name: str

    def capabilities(self, config: ProviderSelection) -> ProviderCapabilities: ...

    def plan(self, request: ProviderRequest) -> ProviderResponse: ...

    def implement(self, request: ProviderRequest) -> ProviderResponse: ...
