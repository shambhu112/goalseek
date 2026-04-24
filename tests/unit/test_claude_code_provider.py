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


def test_claude_code_plan_with_empty_prompt(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="Empty prompt handled",
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    request = _request(tmp_path)
    request.prompt_text = ""
    response = provider.plan(request)

    assert response.exit_code == 1
    assert response.error is not None


def test_claude_code_plan_with_timeout_exceeded(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        raise TimeoutError("Command exceeded timeout")

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    response = provider.plan(_request(tmp_path))

    assert response.exit_code != 0
    assert response.error is not None


def test_claude_code_plan_with_subprocess_error(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=1,
            stdout="",
            stderr="Command failed with error",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    response = provider.plan(_request(tmp_path))

    assert response.exit_code == 1
    assert response.error is not None or response.raw_text == ""


def test_claude_code_implement_with_invalid_mode(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
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
    request.mode = "invalid_mode_xyz"
    response = provider.implement(request)

    assert response.exit_code != 0 or "invalid_mode_xyz" in str(response.raw_text).lower()


def test_claude_code_plan_strips_plan_file_references(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout=(
                "## Plan\n\n"
                "First step\n\n"
                "Plan file: /home/user/.claude/plans/2024-01-01_plan.md\n\n"
                "Second step\n\n"
                "Reference: /home/user/.claude/plans/step2.md and /tmp/.claude/plans/temp.md\n"
            ),
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    response = provider.plan(_request(tmp_path))

    assert response.exit_code == 0
    assert ".claude/plans/" not in response.raw_text
    assert "/tmp/.claude/plans/" not in response.raw_text
    assert "First step" in response.raw_text
    assert "Second step" in response.raw_text


def test_claude_code_evaluate_with_successful_response(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        captured["command"] = command
        captured["env"] = env
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="Evaluation result: passed",
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    request = _request(tmp_path)
    request.mode = "evaluation"
    response = provider.evaluate(request)

    assert response.exit_code == 0
    assert "passed" in response.raw_text


def test_claude_code_evaluate_with_error_response_field(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="",
            stderr="Evaluation failed",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    request = _request(tmp_path)
    request.mode = "evaluation"
    response = provider.evaluate(request)

    assert response.error is not None or response.exit_code != 0


def test_claude_code_evaluate_with_default_permission_mode(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        captured["command"] = command
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="evaluation result",
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    request = _request(tmp_path)
    request.mode = "evaluation"
    response = provider.evaluate(request)

    assert response.exit_code == 0
    assert "--permission-mode" in captured["command"]


def test_claude_code_evaluate_strips_internal_references(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout=(
                "Evaluation complete\n\n"
                "Internal reference: /home/niraj/.claude/plans/eval.md\n\n"
                "Result summary: passed all checks\n"
            ),
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    request = _request(tmp_path)
    request.mode = "evaluation"
    response = provider.evaluate(request)

    assert response.exit_code == 0
    assert ".claude/plans/" not in response.raw_text
    assert "passed all checks" in response.raw_text


def test_claude_code_evaluate_with_timeout(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        raise TimeoutError("Evaluation exceeded timeout")

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    request = _request(tmp_path)
    request.mode = "evaluation"
    response = provider.evaluate(request)

    assert response.exit_code != 0
    assert response.error is not None




def test_claude_code_plan_with_extreme_large_timeout(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        captured["timeout_sec"] = timeout_sec
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
    request.timeout_sec = 999999
    response = provider.plan(request)

    assert response.exit_code == 0
    assert captured["timeout_sec"] == 999999


def test_claude_code_implement_permission_mode_is_accept_edits(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        captured["command"] = command
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="implementation complete",
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    request = _request(tmp_path)
    request.mode = "implementation"
    response = provider.implement(request)

    assert response.exit_code == 0
    assert "--permission-mode" in captured["command"]
    permission_mode_idx = captured["command"].index("--permission-mode")
    assert captured["command"][permission_mode_idx + 1] == "acceptEdits"


def test_claude_code_plan_rejects_writable_paths_with_absolute_paths(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
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
    request.writable_paths = ["/absolute/path/to/file.py"]
    response = provider.plan(request)

    assert response.exit_code != 0
    assert response.error is not None


def test_claude_code_evaluate_with_empty_stdout_only(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="",
            stderr="some stderr output",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    request = _request(tmp_path)
    request.mode = "evaluation"
    response = provider.evaluate(request)

    assert response.exit_code == 0 or response.error is not None


def test_claude_code_evaluate_with_both_stdout_and_stderr_empty(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
        return CommandResult(
            args=command,
            cwd=str(cwd),
            exit_code=0,
            stdout="",
            stderr="",
            duration_sec=0.01,
        )

    monkeypatch.setattr("goalseek.providers.claude_code.run_command", fake_run_command)

    provider = ClaudeCodeProvider()
    request = _request(tmp_path)
    request.mode = "evaluation"
    response = provider.evaluate(request)

    assert response.exit_code != 0 or response.error is not None


def test_claude_code_plan_rejects_generated_paths_with_relative_path(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
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
    request.generated_paths = ["../parent_dir/**"]
    response = provider.plan(request)

    assert response.exit_code != 0
    assert response.error is not None


def test_claude_code_implement_rejects_generated_paths_with_empty_string(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
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
    request.generated_paths = ["runs/**", ""]
    response = provider.implement(request)

    assert response.exit_code != 0
    assert response.error is not None


def test_claude_code_plan_rejects_multiple_validation_failures(monkeypatch, tmp_path):
    def fake_run_command(command, cwd, timeout_sec=1800, env=None, stream_callback=None):
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
    request.model_name = ""
    request.timeout_sec = -5
    request.iteration = 0
    response = provider.plan(request)

    assert response.exit_code != 0
    assert response.error is not None
