from __future__ import annotations

from pathlib import Path

from goalseek.models.config import ProviderSelection
from goalseek.providers.base import ProviderCapabilities, ProviderRequest
from goalseek.providers.codex import CodexProvider, _build_cli_command, _run_cli
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
            "--dangerously-bypass-approvals-and-sandbox",
            "exec",
            "--model",
            "gpt-5-codex",
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
            "--dangerously-bypass-approvals-and-sandbox",
            "exec",
            "--model",
            "gpt-5-codex",
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


def test_codex_cli_omits_model_when_config_uses_default(tmp_path):
    request = _request(tmp_path)
    request.model_name = "default"

    command = _build_cli_command(request, "/usr/bin/codex")

    assert command == [
        "/usr/bin/codex",
        "--dangerously-bypass-approvals-and-sandbox",
        "exec",
        "Plan a focused change.",
    ]


def test_codex_plan_passes_requested_model_to_cli(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)
    request = _request(tmp_path)
    request.model_name = "gpt-5-codex-custom"

    CodexProvider().plan(request)

    command = captured["command"]
    assert request.model_name in command


def test_codex_implement_passes_requested_model_to_cli(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)
    request = _request(tmp_path)
    request.mode = "implementation"
    request.model_name = "gpt-5-codex-custom"

    CodexProvider().implement(request)

    command = captured["command"]
    assert request.model_name in command


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


def test_codex_plan_rejects_dangerous_bypass_flag(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)

    provider = CodexProvider()
    provider.plan(_request(tmp_path))

    assert "--dangerously-bypass-approvals-and-sandbox" in captured["command"]


def test_codex_implement_rejects_dangerous_bypass_flag(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)

    provider = CodexProvider()
    request = _request(tmp_path)
    request.mode = "implementation"
    provider.implement(request)

    assert "--dangerously-bypass-approvals-and-sandbox" in captured["command"]


def test_codex_plan_passes_non_interactive_exec_command(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)

    request = _request(tmp_path)
    provider = CodexProvider()
    provider.plan(request)

    assert captured["command"] == [
        "/usr/bin/codex",
        "--dangerously-bypass-approvals-and-sandbox",
        "exec",
        "--model",
        "gpt-5-codex",
        request.prompt_text,
    ]
    assert captured["cwd"] == tmp_path
    assert captured["timeout_sec"] == request.timeout_sec
    assert captured["env"] is None


def test_codex_uses_default_model_without_explicit_model_flag(monkeypatch, tmp_path):
    captured = _capture_codex_command(monkeypatch)

    request = _request(tmp_path)
    request.model_name = "default"
    provider = CodexProvider()
    provider.plan(request)

    assert captured["command"] == [
        "/usr/bin/codex",
        "--dangerously-bypass-approvals-and-sandbox",
        "exec",
        request.prompt_text,
    ]
    assert "--model" not in captured["command"]


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
