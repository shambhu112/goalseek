from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

from goalseek.models.config import ProviderSelection
from goalseek.providers.base import ProviderCapabilities, ProviderRequest
from goalseek.providers.codex import CodexProvider, _SdkLoadResult, _build_cli_command, _run_cli
from goalseek.utils.subprocess import CommandResult


def _request(project_root: Path) -> ProviderRequest:
    return ProviderRequest(
        project_root=project_root,
        provider_name="codex",
        model_name="gpt-5-codex",
        mode="hypothesis",
        prompt_text="Plan a focused change.",
        writable_paths=["experiment.py"],
        generated_paths=["runs/**", "logs/**"],
        non_interactive=True,
        timeout_sec=30,
        iteration=1,
        metadata={
            "provider_config": ProviderSelection(name="codex", model="gpt-5-codex", transport="cli"),
        },
    )


def test_codex_capabilities_prefers_configured_executable():
    provider = CodexProvider()

    capabilities = provider.capabilities(
        ProviderSelection(name="codex", model="gpt-5-codex", executable="/tmp/custom-codex")
    )

    assert capabilities == ProviderCapabilities(
        available=True,
        supports_non_interactive=True,
        supports_split_prompts=True,
        executable="/tmp/custom-codex",
    )


def test_codex_capabilities_uses_path_lookup(monkeypatch):
    _disable_sdk(monkeypatch)
    monkeypatch.setattr("goalseek.providers.codex.shutil.which", lambda executable: "/usr/bin/codex")

    provider = CodexProvider()
    capabilities = provider.capabilities(ProviderSelection(name="codex", model="gpt-5-codex"))

    assert capabilities == ProviderCapabilities(
        available=True,
        supports_non_interactive=True,
        supports_split_prompts=True,
        executable="/usr/bin/codex",
    )


def test_codex_capabilities_reports_unavailable_when_executable_missing(monkeypatch):
    _disable_sdk(monkeypatch)
    monkeypatch.setattr("goalseek.providers.codex.shutil.which", lambda executable: None)

    provider = CodexProvider()
    capabilities = provider.capabilities(ProviderSelection(name="codex", model="gpt-5-codex"))

    assert capabilities == ProviderCapabilities(
        available=False,
        supports_non_interactive=True,
        supports_split_prompts=True,
        executable=None,
    )


def test_codex_plan_invokes_run_command(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["timeout_sec"] = timeout_sec
        captured["env"] = env
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="plan ready",
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.codex.run_command", fake_run_command)
    monkeypatch.setattr(
        CodexProvider,
        "capabilities",
        lambda self, config: ProviderCapabilities(
            available=True,
            supports_non_interactive=True,
            supports_split_prompts=True,
            executable="/usr/bin/codex",
        ),
    )

    provider = CodexProvider()
    response = provider.plan(_request(tmp_path))

    assert response.exit_code == 0
    assert response.raw_text == "plan ready"
    assert response.error is None
    assert captured == {
        "command": [
            "/usr/bin/codex",
            "--yolo",
            "-m",
            "gpt-5-codex",
            "exec",
            "Plan a focused change.",
        ],
        "cwd": tmp_path,
        "timeout_sec": 30,
        "env": None,
    }


def test_codex_implement_invokes_run_command(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["timeout_sec"] = timeout_sec
        captured["env"] = env
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="implementation complete",
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.codex.run_command", fake_run_command)
    monkeypatch.setattr(
        CodexProvider,
        "capabilities",
        lambda self, config: ProviderCapabilities(
            available=True,
            supports_non_interactive=True,
            supports_split_prompts=True,
            executable="/usr/bin/codex",
        ),
    )

    provider = CodexProvider()
    request = _request(tmp_path)
    request.mode = "implementation"
    response = provider.implement(request)

    assert response.exit_code == 0
    assert response.raw_text == "implementation complete"
    assert response.error is None
    assert captured == {
        "command": [
            "/usr/bin/codex",
            "--yolo",
            "-m",
            "gpt-5-codex",
            "exec",
            "Plan a focused change.",
        ],
        "cwd": tmp_path,
        "timeout_sec": 30,
        "env": None,
    }


def test_run_cli_returns_error_when_executable_missing(tmp_path):
    response = _run_cli(
        _request(tmp_path),
        ProviderCapabilities(
            available=False,
            supports_non_interactive=True,
            supports_split_prompts=True,
            executable=None,
        ),
    )

    assert response.exit_code == 1
    assert response.raw_text == ""
    assert response.error == "executable not found"


def test_run_cli_returns_stderr_on_failure(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=2,
            stdout="",
            stderr="codex failed",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.codex.run_command", fake_run_command)

    response = _run_cli(
        _request(tmp_path),
        ProviderCapabilities(
            available=True,
            supports_non_interactive=True,
            supports_split_prompts=True,
            executable="/usr/bin/codex",
        ),
    )

    assert response.exit_code == 2
    assert response.raw_text == "codex failed"
    assert response.error == "codex failed"


def test_run_cli_prefers_stdout_on_success(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="codex output",
            stderr="warning text",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.codex.run_command", fake_run_command)

    response = _run_cli(
        _request(tmp_path),
        ProviderCapabilities(
            available=True,
            supports_non_interactive=True,
            supports_split_prompts=True,
            executable="/usr/bin/codex",
        ),
    )

    assert response.exit_code == 0
    assert response.raw_text == "codex output"
    assert response.error is None


def test_codex_cli_logs_debug_response(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.DEBUG, logger="goalseek.providers.codex")

    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="plan ready",
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.codex.run_command", fake_run_command)

    _run_cli(_request(tmp_path), _available_codex_capabilities())

    assert "Created Codex provider response source=_run_cli" in caplog.text
    assert "mode=hypothesis" in caplog.text
    assert "raw_text='plan ready'" in caplog.text


def test_codex_cli_omits_model_when_config_uses_default(tmp_path):
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="default", transport="cli")

    command = _build_cli_command(request, "/usr/bin/codex")

    assert command == [
        "/usr/bin/codex",
        "--yolo",
        "exec",
        "Plan a focused change.",
    ]


def test_codex_cli_passes_model_catalog_json_config(tmp_path):
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(
        name="codex",
        model="gpt-5-codex",
        transport="cli",
        model_catalog_json="hidden/models-with-iris-alpha.json",
    )

    command = _build_cli_command(request, "/usr/bin/codex")

    assert command == [
        "/usr/bin/codex",
        "--yolo",
        "-c",
        "model_catalog_json=hidden/models-with-iris-alpha.json",
        "-m",
        "gpt-5-codex",
        "exec",
        "Plan a focused change.",
    ]


def test_codex_plan_passes_project_config_model_to_cli(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)
    request = _request(tmp_path)
    request.model_name = "ignored-request-model"
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="gpt-5-codex-custom", transport="cli")

    CodexProvider().plan(request)

    command = captured["command"]
    assert "-m" in command
    assert "gpt-5-codex-custom" in command
    assert request.model_name not in command


def test_codex_implement_passes_project_config_model_to_cli(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)
    request = _request(tmp_path)
    request.mode = "implementation"
    request.model_name = "ignored-request-model"
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="gpt-5-codex-custom", transport="cli")

    CodexProvider().implement(request)

    command = captured["command"]
    assert "-m" in command
    assert "gpt-5-codex-custom" in command
    assert request.model_name not in command


def _available_codex_capabilities() -> ProviderCapabilities:
    return ProviderCapabilities(
        available=True,
        supports_non_interactive=True,
        supports_split_prompts=True,
        executable="/usr/bin/codex",
    )


def _capture_codex_command(monkeypatch, exit_code=0, stdout="codex output", stderr=""):
    captured: dict[str, object] = {}

    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["timeout_sec"] = timeout_sec
        captured["env"] = env
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.codex.run_command", fake_run_command)
    monkeypatch.setattr(
        CodexProvider,
        "capabilities",
        lambda self, config: _available_codex_capabilities(),
    )
    return captured


def test_codex_plan_uses_yolo_flag(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)

    provider = CodexProvider()
    provider.plan(_request(tmp_path))

    assert "--yolo" in captured["command"]


def test_codex_implement_uses_yolo_flag(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)

    provider = CodexProvider()
    request = _request(tmp_path)
    request.mode = "implementation"
    provider.implement(request)

    assert "--yolo" in captured["command"]


def test_codex_plan_passes_non_interactive_exec_command(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)

    request = _request(tmp_path)
    provider = CodexProvider()
    provider.plan(request)

    assert captured["command"] == [
        "/usr/bin/codex",
        "--yolo",
        "-m",
        "gpt-5-codex",
        "exec",
        request.prompt_text,
    ]
    assert captured["cwd"] == tmp_path
    assert captured["timeout_sec"] == request.timeout_sec
    assert captured["env"] is None


def test_codex_uses_default_model_without_explicit_model_flag(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)

    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="default", transport="cli")
    provider = CodexProvider()
    provider.plan(request)

    assert captured["command"] == [
        "/usr/bin/codex",
        "--yolo",
        "exec",
        request.prompt_text,
    ]
    assert "-m" not in captured["command"]


def test_codex_propagates_empty_stdout_and_stderr_failure_message(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "goalseek.providers.codex.run_command",
        lambda command, cwd, timeout_sec=1800, env=None, stream_callback=None: CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=2,
            stdout="",
            stderr="",
            duration_sec=0.01,
        ),
    )

    response = _run_cli(_request(tmp_path), _available_codex_capabilities())

    assert response.exit_code == 2
    assert response.raw_text == ""
    assert response.error == "codex exited with status 2 without output"


def test_codex_forced_sdk_runs_thread(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    class FakeAppServerConfig:
        def __init__(self, codex_bin):
            self.codex_bin = codex_bin

    class FakeResult:
        id = "turn-1"
        status = "completed"
        error = None
        duration_ms = 25
        final_response = "sdk plan ready"
        usage = None

    class FakeThread:
        id = "thread-1"

        def run(self, prompt, **kwargs):
            captured["prompt"] = prompt
            captured["run_kwargs"] = kwargs
            return FakeResult()

    class FakeCodex:
        def __init__(self, config=None):
            captured["codex_bin"] = config.codex_bin

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def thread_start(self, **kwargs):
            captured["thread_start_kwargs"] = kwargs
            return FakeThread()

    monkeypatch.setattr(
        "goalseek.providers.codex._load_sdk",
        lambda: _SdkLoadResult(
            codex=FakeCodex,
            app_server_config=FakeAppServerConfig,
            package_name="openai_codex",
        ),
    )
    request = _request(tmp_path)
    request.model_name = "ignored-request-model"
    request.metadata["provider_config"] = ProviderSelection(
        name="codex",
        model="gpt-5-codex",
        executable="/tmp/codex",
        transport="sdk",
        reasoning_effort="high",
    )

    response = CodexProvider().plan(request)

    assert response.exit_code == 0
    assert response.raw_text == "sdk plan ready"
    assert response.error is None
    assert response.metadata["transport"] == "sdk"
    assert response.metadata["thread_id"] == "thread-1"
    assert captured["codex_bin"] == "/tmp/codex"
    assert captured["thread_start_kwargs"] == {
        "model": "gpt-5-codex",
        "cwd": str(tmp_path),
        "config": {"model_reasoning_effort": "high"},
    }
    assert captured["run_kwargs"] == {
        "cwd": str(tmp_path),
        "effort": "high",
        "model": "gpt-5-codex",
    }


def test_codex_forced_sdk_passes_model_catalog_json_config(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    class FakeThread:
        id = "thread-1"

        def run(self, prompt, **kwargs):
            captured["run_kwargs"] = kwargs

            class FakeResult:
                id = "turn-1"
                status = "completed"
                error = None
                duration_ms = 25
                final_response = "sdk plan ready"
                usage = None

            return FakeResult()

    class FakeCodex:
        def __init__(self, config=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def thread_start(self, **kwargs):
            captured["thread_start_kwargs"] = kwargs
            return FakeThread()

    monkeypatch.setattr(
        "goalseek.providers.codex._load_sdk",
        lambda: _SdkLoadResult(codex=FakeCodex, package_name="openai_codex"),
    )
    request = _request(tmp_path)
    request.model_name = "ignored-request-model"
    request.metadata["provider_config"] = ProviderSelection(
        name="codex",
        model="gpt-5-codex",
        transport="sdk",
        model_catalog_json="hidden/models-with-iris-alpha.json",
    )

    response = CodexProvider().plan(request)

    assert response.exit_code == 0
    assert captured["thread_start_kwargs"] == {
        "model": "gpt-5-codex",
        "cwd": str(tmp_path),
        "config": {"model_catalog_json": "hidden/models-with-iris-alpha.json"},
    }
    assert captured["run_kwargs"] == {
        "cwd": str(tmp_path),
        "model": "gpt-5-codex",
    }


def test_codex_sdk_reuses_thread_across_plan_and_implementation(monkeypatch, tmp_path):
    captured: dict[str, object] = {"resume_ids": []}

    class FakeResult:
        id = "turn-1"
        status = "completed"
        error = None
        duration_ms = 10
        final_response = "done"
        usage = None

    class FakeThread:
        def __init__(self, thread_id):
            self.id = thread_id

        def run(self, prompt, **kwargs):
            return FakeResult()

    class FakeCodex:
        def __init__(self, config=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def thread_start(self, **kwargs):
            captured["started"] = True
            return FakeThread("thread-1")

        def thread_resume(self, thread_id, **kwargs):
            captured["resume_ids"].append(thread_id)
            return FakeThread(thread_id)

    monkeypatch.setattr(
        "goalseek.providers.codex._load_sdk",
        lambda: _SdkLoadResult(codex=FakeCodex, package_name="openai_codex"),
    )
    config = ProviderSelection(name="codex", model="gpt-5-codex", transport="sdk", reuse_thread=True)
    plan_request = _request(tmp_path)
    plan_request.metadata["provider_config"] = config
    implement_request = _request(tmp_path)
    implement_request.mode = "implementation"
    implement_request.metadata["provider_config"] = config
    provider = CodexProvider()

    provider.plan(plan_request)
    provider.implement(implement_request)

    assert captured["started"] is True
    assert captured["resume_ids"] == ["thread-1"]


def test_codex_sdk_resume_failure_starts_new_thread(monkeypatch, tmp_path):
    captured: dict[str, object] = {"starts": 0, "resumes": 0}

    class FakeResult:
        id = "turn-1"
        status = "completed"
        error = None
        duration_ms = 10
        final_response = "done"
        usage = None

    class FakeThread:
        id = "new-thread"

        def run(self, prompt, **kwargs):
            return FakeResult()

    class FakeCodex:
        def __init__(self, config=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def thread_resume(self, thread_id, **kwargs):
            captured["resumes"] += 1
            raise RuntimeError("stale thread")

        def thread_start(self, **kwargs):
            captured["starts"] += 1
            return FakeThread()

    monkeypatch.setattr(
        "goalseek.providers.codex._load_sdk",
        lambda: _SdkLoadResult(codex=FakeCodex, package_name="openai_codex"),
    )
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="gpt-5-codex", transport="sdk")
    provider = CodexProvider()
    provider._sdk_thread_ids[str(tmp_path.resolve()) + "|codex|gpt-5-codex"] = "stale-thread"

    response = provider.plan(request)

    assert response.exit_code == 0
    assert response.raw_text == "done"
    assert response.metadata["thread_id"] == "new-thread"
    assert captured == {"starts": 1, "resumes": 1}


def test_codex_sdk_treats_turn_error_as_provider_failure(monkeypatch, tmp_path):
    class FakeTurnError:
        value = "rate_limited"

    class FakeResult:
        id = "turn-1"
        status = "failed"
        error = FakeTurnError()
        duration_ms = 10
        final_response = "partial text"
        usage = None

    class FakeThread:
        id = "thread-1"

        def run(self, prompt, **kwargs):
            return FakeResult()

    class FakeCodex:
        def __init__(self, config=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def thread_start(self, **kwargs):
            return FakeThread()

    monkeypatch.setattr(
        "goalseek.providers.codex._load_sdk",
        lambda: _SdkLoadResult(codex=FakeCodex, package_name="openai_codex"),
    )
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="gpt-5-codex", transport="sdk")

    response = CodexProvider().plan(request)

    assert response.exit_code == 1
    assert response.raw_text == "partial text"
    assert response.error == "rate_limited"
    assert response.metadata["turn_status"] == "failed"


def test_codex_sdk_empty_final_response_is_successful_empty_output(monkeypatch, tmp_path):
    class FakeResult:
        id = "turn-1"
        status = "completed"
        error = None
        duration_ms = 10
        final_response = None
        usage = None

    class FakeThread:
        id = "thread-1"

        def run(self, prompt, **kwargs):
            return FakeResult()

    class FakeCodex:
        def __init__(self, config=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def thread_start(self, **kwargs):
            return FakeThread()

    monkeypatch.setattr(
        "goalseek.providers.codex._load_sdk",
        lambda: _SdkLoadResult(codex=FakeCodex, package_name="openai_codex"),
    )
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="gpt-5-codex", transport="sdk")

    response = CodexProvider().plan(request)

    assert response.exit_code == 0
    assert response.raw_text == ""
    assert response.error is None
    assert response.metadata["final_response"] == ""


def test_codex_sdk_logs_debug_response(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.DEBUG, logger="goalseek.providers.codex")

    class FakeResult:
        id = "turn-1"
        status = "completed"
        error = None
        duration_ms = 10
        final_response = "sdk debug text"
        usage = None

    class FakeThread:
        id = "thread-1"

        def run(self, prompt, **kwargs):
            return FakeResult()

    class FakeCodex:
        def __init__(self, config=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def thread_start(self, **kwargs):
            return FakeThread()

    monkeypatch.setattr(
        "goalseek.providers.codex._load_sdk",
        lambda: _SdkLoadResult(codex=FakeCodex, package_name="openai_codex"),
    )
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="gpt-5-codex", transport="sdk")

    CodexProvider().plan(request)

    assert "Created Codex provider response source=_run_sdk" in caplog.text
    assert "sdk debug text" in caplog.text
    assert "'transport': 'sdk'" in caplog.text


def test_codex_sdk_timeout_maps_to_124(monkeypatch, tmp_path):
    class FakeThread:
        id = "thread-1"

        def run(self, prompt, **kwargs):
            raise TimeoutError("codex timed out")

    class FakeCodex:
        def __init__(self, config=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def thread_start(self, **kwargs):
            return FakeThread()

    monkeypatch.setattr(
        "goalseek.providers.codex._load_sdk",
        lambda: _SdkLoadResult(codex=FakeCodex, package_name="openai_codex"),
    )
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="gpt-5-codex", transport="sdk")

    response = CodexProvider().plan(request)

    assert response.exit_code == 124
    assert response.raw_text == ""
    assert response.error == "codex timed out"


def test_codex_cli_fallback_reports_missing_executable_when_no_sdk_or_cli(monkeypatch, tmp_path):
    _disable_sdk(monkeypatch)
    monkeypatch.setattr("goalseek.providers.codex.shutil.which", lambda executable: None)
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="gpt-5-codex", transport="auto")

    response = CodexProvider().plan(request)

    assert response.exit_code == 1
    assert response.raw_text == ""
    assert response.error == "executable not found"
    assert response.metadata["transport"] == "cli"
    assert response.metadata["transport_fallback"] == "sdk_unavailable"


def test_codex_cli_extreme_prompt_preserves_newlines_and_unicode(tmp_path):
    request = _request(tmp_path)
    request.prompt_text = "Plan:\n- café\n- emoji 🦴\n" + ("x" * 10_000)
    request.metadata["provider_config"] = ProviderSelection(
        name="codex",
        model="gpt-5-codex",
        transport="cli",
        plugins={"enabled": True, "requested": ["github"]},
    )

    command = _build_cli_command(request, "/usr/bin/codex")

    assert command[-1].startswith("Plan:\n- café\n- emoji 🦴\n")
    assert "x" * 10_000 in command[-1]
    assert "Use available Codex plugins when helpful: github." in command[-1]


def test_codex_auto_falls_back_to_cli_when_sdk_missing(monkeypatch, tmp_path):
    _disable_sdk(monkeypatch)
    captured = _capture_codex_command(monkeypatch)
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="gpt-5-codex", transport="auto")

    response = CodexProvider().plan(request)

    assert response.exit_code == 0
    assert response.metadata["transport"] == "cli"
    assert response.metadata["transport_fallback"] == "sdk_unavailable"
    assert captured["command"][0] == "/usr/bin/codex"


def test_codex_forced_sdk_errors_when_sdk_missing(monkeypatch, tmp_path):
    _disable_sdk(monkeypatch)
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection(name="codex", model="gpt-5-codex", transport="sdk")

    response = CodexProvider().plan(request)

    assert response.exit_code == 1
    assert response.raw_text == ""
    assert response.metadata["transport"] == "sdk"
    assert response.error.startswith("Codex SDK unavailable")


def test_codex_cli_prompt_includes_runtime_options(tmp_path):
    request = _request(tmp_path)
    request.metadata["provider_config"] = ProviderSelection.model_validate(
        {
            "name": "codex",
            "model": "gpt-5-codex",
            "transport": "cli",
            "parallel_runs": {"enabled": True, "candidates": 2},
            "deep_research": {"enabled": True, "model": "o4-mini-deep-research"},
            "plugins": {"enabled": True, "requested": ["github", "openai-docs"]},
            "mcp": {"allowed_servers": ["projectTools"]},
        }
    )

    command = _build_cli_command(request, "/usr/bin/codex")

    prompt = command[-1]
    assert "Codex runtime options:" in prompt
    assert "2 independent candidate hypotheses" in prompt
    assert "o4-mini-deep-research" in prompt
    assert "github, openai-docs" in prompt
    assert "projectTools" in prompt


def _disable_sdk(monkeypatch):
    monkeypatch.setattr("goalseek.providers.codex._load_sdk", lambda: _SdkLoadResult(error="missing sdk"))


@pytest.mark.live
def test_live_codex_sdk_smoke(tmp_path):
    if os.environ.get("GOALSEEK_LIVE_CODEX") != "1":
        pytest.skip("set GOALSEEK_LIVE_CODEX=1 to run live Codex SDK smoke test")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("set OPENAI_API_KEY to run live Codex SDK smoke test")
    try:
        from openai_codex import Codex
    except Exception as exc:
        pytest.skip(f"openai_codex unavailable: {exc}")

    with Codex() as codex:
        codex.login_api_key(api_key)
        thread = codex.thread_start(model=os.environ.get("GOALSEEK_LIVE_CODEX_MODEL", "gpt-5-codex"), cwd=str(tmp_path))
        result = thread.run("Reply with exactly: goalseek live codex ok", cwd=str(tmp_path))

    assert result.error is None
    assert result.final_response
    assert "goalseek live codex ok" in result.final_response.lower()


@pytest.mark.live
def test_live_codex_provider_sdk_plan_smoke(tmp_path):
    if os.environ.get("GOALSEEK_LIVE_CODEX") != "1":
        pytest.skip("set GOALSEEK_LIVE_CODEX=1 to run live Codex provider SDK smoke test")
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("set OPENAI_API_KEY to run live Codex provider SDK smoke test")
    try:
        import openai_codex  # noqa: F401
    except Exception as exc:
        pytest.skip(f"openai_codex unavailable: {exc}")

    request = _request(tmp_path)
    request.timeout_sec = 120
    request.prompt_text = "Reply with exactly: goalseek live provider sdk ok"
    request.model_name = os.environ.get("GOALSEEK_LIVE_CODEX_MODEL", "gpt-5-codex")
    request.metadata["provider_config"] = ProviderSelection(
        name="codex",
        model=request.model_name,
        transport="sdk",
    )

    response = CodexProvider().plan(request)

    assert response.exit_code == 0, response.error
    assert response.error is None
    assert response.metadata["transport"] == "sdk"
    assert "goalseek live provider sdk ok" in response.raw_text.lower()


@pytest.mark.live
def test_live_codex_provider_sdk_reuses_thread(tmp_path):
    if os.environ.get("GOALSEEK_LIVE_CODEX") != "1":
        pytest.skip("set GOALSEEK_LIVE_CODEX=1 to run live Codex provider SDK reuse test")
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("set OPENAI_API_KEY to run live Codex provider SDK reuse test")
    try:
        import openai_codex  # noqa: F401
    except Exception as exc:
        pytest.skip(f"openai_codex unavailable: {exc}")

    model = os.environ.get("GOALSEEK_LIVE_CODEX_MODEL", "gpt-5-codex")
    config = ProviderSelection(name="codex", model=model, transport="sdk", reuse_thread=True)
    provider = CodexProvider()
    plan_request = _request(tmp_path)
    plan_request.timeout_sec = 120
    plan_request.model_name = model
    plan_request.prompt_text = "Remember the token GOALSEEK-LIVE-THREAD and reply: stored"
    plan_request.metadata["provider_config"] = config
    implement_request = _request(tmp_path)
    implement_request.mode = "implementation"
    implement_request.timeout_sec = 120
    implement_request.model_name = model
    implement_request.prompt_text = "What exact token did I ask you to remember? Reply with only that token."
    implement_request.metadata["provider_config"] = config

    plan_response = provider.plan(plan_request)
    implement_response = provider.implement(implement_request)

    assert plan_response.exit_code == 0, plan_response.error
    assert implement_response.exit_code == 0, implement_response.error
    assert plan_response.metadata["thread_id"]
    assert implement_response.metadata["thread_id"] == plan_response.metadata["thread_id"]
    assert "GOALSEEK-LIVE-THREAD" in implement_response.raw_text


def _require_live_codex_provider_sdk(test_name: str) -> None:
    if os.environ.get("GOALSEEK_LIVE_CODEX") != "1":
        pytest.skip(f"set GOALSEEK_LIVE_CODEX=1 to run {test_name}")
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip(f"set OPENAI_API_KEY to run {test_name}")
    try:
        import openai_codex  # noqa: F401
    except Exception as exc:
        pytest.skip(f"openai_codex unavailable: {exc}")


@pytest.mark.live
def test_live_codex_provider_sdk_fails_with_missing_executable(tmp_path):
    _require_live_codex_provider_sdk("live Codex provider SDK missing executable test")
    request = _request(tmp_path)
    request.timeout_sec = 120
    request.prompt_text = "This should never run because the SDK binary path is invalid."
    request.model_name = os.environ.get("GOALSEEK_LIVE_CODEX_MODEL", "gpt-5-codex")
    request.metadata["provider_config"] = ProviderSelection(
        name="codex",
        model=request.model_name,
        transport="sdk",
        executable=str(tmp_path / "missing-codex-binary"),
    )

    response = CodexProvider().plan(request)

    assert response.exit_code != 0
    assert response.error
    assert response.raw_text == ""
    assert response.metadata["transport"] == "sdk"


@pytest.mark.live
def test_live_codex_provider_sdk_fails_with_invalid_model(tmp_path):
    _require_live_codex_provider_sdk("live Codex provider SDK invalid model test")
    request = _request(tmp_path)
    request.timeout_sec = 120
    request.prompt_text = "Reply with exactly: this invalid model should fail"
    request.model_name = "goalseek-live-invalid-codex-model"
    request.metadata["provider_config"] = ProviderSelection(
        name="codex",
        model=request.model_name,
        transport="sdk",
    )

    response = CodexProvider().plan(request)

    assert response.exit_code != 0
    assert response.error
    assert response.metadata["transport"] == "sdk"


@pytest.mark.live
def test_live_codex_provider_sdk_fails_with_broken_executable(tmp_path):
    _require_live_codex_provider_sdk("live Codex provider SDK broken executable test")
    broken_codex = tmp_path / "codex"
    broken_codex.write_text("#!/bin/sh\nexit 42\n")
    broken_codex.chmod(0o755)
    request = _request(tmp_path)
    request.timeout_sec = 120
    request.prompt_text = "This should never run because the SDK app-server exits immediately."
    request.model_name = os.environ.get("GOALSEEK_LIVE_CODEX_MODEL", "gpt-5-codex")
    request.metadata["provider_config"] = ProviderSelection(
        name="codex",
        model=request.model_name,
        transport="sdk",
        executable=str(broken_codex),
    )

    response = CodexProvider().plan(request)

    assert response.exit_code != 0
    assert response.error
    assert response.raw_text == ""
    assert response.metadata["transport"] == "sdk"
