from __future__ import annotations

import inspect
import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from goalseek.models.config import ProviderSelection
from goalseek.providers.base import ProviderCapabilities, ProviderRequest, ProviderResponse
from goalseek.utils.subprocess import run_command


logger = logging.getLogger(__name__)


class CodexProvider:
    name = "codex"

    def __init__(self) -> None:
        self._sdk_thread_ids: dict[str, str] = {}

    def capabilities(self, config: ProviderSelection) -> ProviderCapabilities:
        executable = config.executable or shutil.which("codex")
        sdk = _load_sdk()
        if config.transport == "sdk":
            available = sdk.available
        elif config.transport == "cli":
            available = bool(executable)
        else:
            available = sdk.available or bool(executable)
        return ProviderCapabilities(
            available=available,
            supports_non_interactive=True,
            supports_split_prompts=True,
            executable=executable,
        )

    def plan(self, request: ProviderRequest) -> ProviderResponse:
        return self._run(request)

    def implement(self, request: ProviderRequest) -> ProviderResponse:
        return self._run(request)

    def _run(self, request: ProviderRequest) -> ProviderResponse:
        config = _selection_from_request(request)
        return _run_codex(request, config, self.capabilities(config), self._sdk_thread_ids)


def _run_cli(
    request: ProviderRequest,
    capabilities: ProviderCapabilities,
    env: dict[str, str] | None = None,
    metadata: dict[str, object] | None = None,
) -> ProviderResponse:
    start = time.time()
    if not capabilities.executable:
        return _log_provider_response(
            request,
            ProviderResponse(
                raw_text="",
                exit_code=1,
                duration_sec=0.0,
                error="executable not found",
                metadata=metadata or {},
            ),
            source="_run_cli",
        )
    logger.info(
        "Running provider=%s mode=%s model=%s iteration=%s",
        request.provider_name,
        request.mode,
        request.model_name,
        request.iteration,
    )
    result = run_command(
        _build_cli_command(request, capabilities.executable),
        cwd=Path(request.project_root),
        timeout_sec=request.timeout_sec,
        env=env,
    )
    logger.info(
        "Provider=%s mode=%s finished exit_code=%s",
        request.provider_name,
        request.mode,
        result.exit_code,
    )
    return _log_provider_response(
        request,
        ProviderResponse(
            raw_text=result.stdout or result.stderr,
            exit_code=result.exit_code,
            duration_sec=time.time() - start,
            changed_files=[],
            error=(
                None
                if result.exit_code == 0
                else result.stderr.strip() or f"{request.provider_name} exited with status {result.exit_code} without output"
            ),
            metadata=metadata or {},
        ),
        source="_run_cli",
    )


def _build_cli_command(request: ProviderRequest, executable: str) -> list[str]:
    if request.provider_name == "codex":
        config = _selection_from_request(request)
        command = [
            executable,
            "--yolo",
        ]
        if config.model_catalog_json:
            command.extend(["-c", f"model_catalog_json={config.model_catalog_json}"])
        model = _model_arg(config.model)
        if model:
            command.extend(["-m", model])
        command.append("exec")
        command.append(_prompt_for_codex(request, config))
        return command
    return [executable, request.prompt_text]


@dataclass
class _SdkLoadResult:
    codex: type | None = None
    app_server_config: type | None = None
    package_name: str | None = None
    error: str | None = None

    @property
    def available(self) -> bool:
        return self.codex is not None


def _run_codex(
    request: ProviderRequest,
    config: ProviderSelection,
    capabilities: ProviderCapabilities,
    thread_ids: dict[str, str],
) -> ProviderResponse:
    if config.transport == "cli":
        return _run_cli(request, capabilities, metadata={"transport": "cli"})
    sdk = _load_sdk()
    if sdk.available:
        return _run_sdk(request, config, sdk, thread_ids)
    if config.transport == "auto":
        response = _run_cli(request, capabilities, metadata={"transport": "cli", "sdk_error": sdk.error or ""})
        response.metadata.setdefault("transport_fallback", "sdk_unavailable")
        return response
    return _log_provider_response(
        request,
        ProviderResponse(
            raw_text="",
            exit_code=1,
            duration_sec=0.0,
            changed_files=[],
            error=f"Codex SDK unavailable: {sdk.error or 'package not importable'}",
            metadata={"transport": "sdk", "sdk_error": sdk.error or "package not importable"},
        ),
        source="_run_codex",
    )


def _run_sdk(
    request: ProviderRequest,
    config: ProviderSelection,
    sdk: _SdkLoadResult,
    thread_ids: dict[str, str],
) -> ProviderResponse:
    start = time.time()
    try:
        with _sdk_client(sdk, config) as codex:
            thread = _sdk_thread(codex, request, config, thread_ids)
            result = _call_with_supported_kwargs(
                thread.run,
                _prompt_for_codex(request, config),
                cwd=str(request.project_root),
                effort=config.reasoning_effort,
                model=_model_arg(config.model),
            )
            thread_id = _thread_id(thread)
            if config.reuse_thread and thread_id:
                thread_ids[_thread_key(request, config)] = thread_id
            final_response = getattr(result, "final_response", None) or ""
            turn_error = getattr(result, "error", None)
            metadata = {
                "transport": "sdk",
                "sdk_package": sdk.package_name or "",
                "thread_id": thread_id or "",
                "turn_id": str(getattr(result, "id", "") or ""),
                "turn_status": _stringify_metadata(getattr(result, "status", None)),
                "duration_ms": getattr(result, "duration_ms", None),
                "final_response": final_response,
                "usage": _metadata_value(getattr(result, "usage", None)),
            }
            return _log_provider_response(
                request,
                ProviderResponse(
                    raw_text=final_response,
                    exit_code=0 if turn_error is None else 1,
                    duration_sec=time.time() - start,
                    changed_files=[],
                    error=None if turn_error is None else _stringify_metadata(turn_error),
                    metadata={key: value for key, value in metadata.items() if value is not None},
                ),
                source="_run_sdk",
            )
    except TimeoutError as exc:
        return _log_provider_response(
            request,
            ProviderResponse(
                raw_text="",
                exit_code=124,
                duration_sec=time.time() - start,
                changed_files=[],
                error=str(exc),
                metadata={"transport": "sdk", "sdk_package": sdk.package_name or ""},
            ),
            source="_run_sdk",
        )
    except Exception as exc:
        return _log_provider_response(
            request,
            ProviderResponse(
                raw_text="",
                exit_code=1,
                duration_sec=time.time() - start,
                changed_files=[],
                error=str(exc),
                metadata={"transport": "sdk", "sdk_package": sdk.package_name or ""},
            ),
            source="_run_sdk",
        )


def _sdk_client(sdk: _SdkLoadResult, config: ProviderSelection):
    kwargs: dict[str, object] = {}
    if config.executable and sdk.app_server_config is not None:
        kwargs["config"] = sdk.app_server_config(codex_bin=config.executable)
    return sdk.codex(**kwargs) if kwargs else sdk.codex()


def _sdk_thread(codex, request: ProviderRequest, config: ProviderSelection, thread_ids: dict[str, str]):
    key = _thread_key(request, config)
    thread_id = thread_ids.get(key)
    thread_config = _sdk_thread_config(config)
    start_kwargs = {
        "model": _model_arg(config.model),
        "cwd": str(request.project_root),
        "config": thread_config,
    }
    if config.reuse_thread and thread_id and hasattr(codex, "thread_resume"):
        try:
            return _call_with_supported_kwargs(codex.thread_resume, thread_id, **start_kwargs)
        except Exception:
            logger.info("Failed to resume Codex SDK thread; starting a new one", exc_info=True)
            thread_ids.pop(key, None)
    return _call_with_supported_kwargs(codex.thread_start, **start_kwargs)


def _load_sdk() -> _SdkLoadResult:
    try:
        import openai_codex

        return _SdkLoadResult(
            codex=openai_codex.Codex,
            app_server_config=getattr(openai_codex, "AppServerConfig", None),
            package_name="openai_codex",
        )
    except Exception as openai_codex_error:
        try:
            import codex_app_server

            return _SdkLoadResult(
                codex=codex_app_server.Codex,
                app_server_config=getattr(codex_app_server, "AppServerConfig", None),
                package_name="codex_app_server",
            )
        except Exception as codex_app_server_error:
            return _SdkLoadResult(
                error=f"openai_codex: {openai_codex_error}; codex_app_server: {codex_app_server_error}"
            )


def _selection_from_request(request: ProviderRequest) -> ProviderSelection:
    raw_config = request.metadata.get("provider_config")
    if isinstance(raw_config, ProviderSelection):
        return raw_config
    if isinstance(raw_config, dict):
        return ProviderSelection.model_validate(raw_config)
    return ProviderSelection(name="codex", model=request.model_name)


def _prompt_for_codex(request: ProviderRequest, config: ProviderSelection) -> str:
    notes: list[str] = []
    if request.mode in {"hypothesis", "plan"} and config.parallel_runs.enabled:
        notes.append(
            "Generate "
            f"{config.parallel_runs.candidates} independent candidate hypotheses before selecting one final plan. "
            f"Selection policy: {config.parallel_runs.selection}."
        )
        if config.parallel_runs.isolate_worktrees:
            notes.append("Keep candidate work isolated conceptually; do not edit files during planning.")
    if request.mode in {"hypothesis", "plan"} and config.deep_research.enabled:
        notes.append(
            "Use available Deep Research or MCP/web research tools before planning. "
            f"Research model preference: {config.deep_research.model}; "
            f"max sources: {config.deep_research.max_sources}; "
            f"include web: {config.deep_research.include_web}; include MCP: {config.deep_research.include_mcp}."
        )
    if config.plugins.enabled and config.plugins.requested:
        notes.append("Use available Codex plugins when helpful: " + ", ".join(config.plugins.requested) + ".")
    if config.mcp.allowed_servers:
        notes.append(
            f"Use MCP config at {config.mcp.config_path}; allowed MCP servers: "
            + ", ".join(config.mcp.allowed_servers)
            + "."
        )
    if not notes:
        return request.prompt_text
    return request.prompt_text.rstrip() + "\n\nCodex runtime options:\n" + "\n".join(f"- {item}" for item in notes)


def _sdk_thread_config(config: ProviderSelection) -> dict[str, str] | None:
    thread_config: dict[str, str] = {}
    if config.reasoning_effort:
        thread_config["model_reasoning_effort"] = config.reasoning_effort
    if config.model_catalog_json:
        thread_config["model_catalog_json"] = config.model_catalog_json
    if not thread_config:
        return None
    return thread_config


def _model_arg(model_name: str) -> str | None:
    if not model_name or model_name in {"default", "auto"}:
        return None
    return model_name


def _thread_key(request: ProviderRequest, config: ProviderSelection) -> str:
    return "|".join(
        [
            str(Path(request.project_root).resolve()),
            request.provider_name,
            config.model,
        ]
    )


def _thread_id(thread) -> str | None:
    value = getattr(thread, "id", None)
    if value is None:
        value = getattr(thread, "thread_id", None)
    return str(value) if value else None


def _log_provider_response(request: ProviderRequest, response: ProviderResponse, *, source: str) -> ProviderResponse:
    logger.debug(
        "Created Codex provider response source=%s mode=%s iteration=%s exit_code=%s error=%s metadata=%s raw_text=%r",
        source,
        request.mode,
        request.iteration,
        response.exit_code,
        response.error,
        response.metadata,
        response.raw_text,
    )
    return response


def _call_with_supported_kwargs(func: Callable[..., Any], *args, **kwargs):
    filtered = {key: value for key, value in kwargs.items() if value is not None}
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        return func(*args, **filtered)
    if any(parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in signature.parameters.values()):
        return func(*args, **filtered)
    supported = {key: value for key, value in filtered.items() if key in signature.parameters}
    return func(*args, **supported)


def _metadata_value(value):
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="python")
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return str(value)


def _stringify_metadata(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)
