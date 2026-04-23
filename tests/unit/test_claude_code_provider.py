from __future__ import annotations

from pathlib import Path

from goalseek.providers.base import ProviderRequest
from goalseek.providers.claude_code import ClaudeCodeProvider
from goalseek.utils.subprocess import CommandResult


def _request(project_root: Path) -> ProviderRequest:
    return ProviderRequest(
        project_root=project_root,
        provider_name="claude_code",
        model_name="claude-test-model",
        mode="hypothesis",
        prompt_text="Plan a focused change.",
        writable_paths=["experiment.py"],
        generated_paths=["runs/**", "logs/**"],
        non_interactive=True,
        timeout_sec=30,
        iteration=1,
    )


def test_claude_code_plan_sets_noninteractive_env(monkeypatch, tmp_path):
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
            stdout="ok",
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    response = provider.plan(_request(tmp_path))

    assert response.exit_code == 0
    assert captured["env"] == {
        "CLAUDE_AUTO_APPROVE": "true",
        "CLAUDE_SKIP_CONFIRMATIONS": "true",
    }
    assert captured["command"] == [
        captured["command"][0],
        "--print",
        "--model",
        "claude-test-model",
        "--permission-mode",
        "default",
        "--add-dir",
        str(tmp_path),
        "--",
        "Plan a focused change.",
    ]


def test_claude_code_plan_strips_external_plan_reference(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout=(
                "## Plan\n\n"
                "Use a smaller change.\n\n"
                "The plan is ready at `/home/niraj/.claude/plans/example.md`. Shall I proceed with implementation?\n"
            ),
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    response = provider.plan(_request(tmp_path))

    assert response.exit_code == 0
    assert ".claude/plans/" not in response.raw_text
    assert "Use a smaller change." in response.raw_text


def test_claude_code_implement_sets_noninteractive_env(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        captured["command"] = command
        captured["env"] = env
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="ok",
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    request = _request(tmp_path)
    request.mode = "implementation"
    response = provider.implement(request)

    assert response.exit_code == 0
    assert captured["env"] == {
        "CLAUDE_AUTO_APPROVE": "true",
        "CLAUDE_SKIP_CONFIRMATIONS": "true",
    }
    assert captured["command"] == [
        captured["command"][0],
        "--print",
        "--model",
        "claude-test-model",
        "--permission-mode",
        "acceptEdits",
        "--add-dir",
        str(tmp_path),
        "--",
        "Plan a focused change.",
    ]
