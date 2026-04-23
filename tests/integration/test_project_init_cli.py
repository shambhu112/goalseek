from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from goalseek.api import init_project
from goalseek.cli.app import cli


def test_project_init_prompts_before_replacing_existing_directory(tmp_path):
    project_root = Path(init_project("demo", path=str(tmp_path), provider="fake", model="fake-model"))
    marker = project_root / "marker.txt"
    marker.write_text("old", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "init", "demo", "--path", str(tmp_path)], input="y\n")

    assert result.exit_code == 0
    assert project_root.exists()
    assert not marker.exists()
    assert (project_root / "manifest.yaml").exists()


def test_project_init_aborts_when_user_declines_replacement(tmp_path):
    project_root = Path(init_project("demo", path=str(tmp_path), provider="fake", model="fake-model"))
    marker = project_root / "marker.txt"
    marker.write_text("old", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "init", "demo", "--path", str(tmp_path)], input="n\n")

    assert result.exit_code != 0
    assert marker.exists()
    assert project_root.exists()


def test_project_init_creates_isolated_repo_inside_parent_repo(tmp_path):
    parent = tmp_path / "parent"
    parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(parent), "init"], check=True, capture_output=True, text=True)

    project_root = Path(init_project("demo", path=str(parent), provider="fake", model="fake-model"))

    assert (project_root / ".git").exists()
    toplevel = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert toplevel == str(project_root)


def test_baseline_cli_exits_nonzero_when_verification_fails(tmp_path):
    project_root = Path(init_project("demo", path=str(tmp_path), provider="fake", model="fake-model"))
    (project_root / "validate_results.py").unlink()

    runner = CliRunner()
    result = runner.invoke(cli, ["baseline", str(project_root)])

    assert result.exit_code == 5
    assert "Baseline verification failed" in result.output
    assert "can't open file" in result.output
    assert (project_root / "runs" / "0000_baseline" / "verifier.log").exists()
    assert (project_root / "runs" / "0000_baseline" / "result.json").exists()


def test_run_cli_explains_how_to_initialize_baseline(tmp_path):
    project_root = Path(init_project("demo", path=str(tmp_path), provider="fake", model="fake-model"))

    runner = CliRunner()
    result = runner.invoke(cli, ["run", str(project_root), "--iterations", "1"])

    assert result.exit_code == 3
    assert "baseline must be run before the loop" in result.output
    assert "run `goalseek baseline" in result.output
    assert str(project_root) in result.output


def test_move_testpackage_auto_commits_into_clean_project_repo(tmp_path):
    project_root = Path(init_project("demo", path=str(tmp_path), provider="fake", model="fake-model"))
    repo_root = Path(__file__).resolve().parents[2]
    if not (repo_root / "test-package").exists():
        pytest.skip("test-package fixture is not present in this repository")

    subprocess.run(
        [str(repo_root / "move-testpackage.sh"), "--overwrite", str(project_root)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    status = subprocess.run(
        ["git", "-C", str(project_root), "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    )
    log = subprocess.run(
        ["git", "-C", str(project_root), "log", "--oneline", "-n", "1"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert status.stdout.strip() == ""
    assert "project: import test package" in log.stdout


def test_gittreeclean_commits_when_project_has_changes(tmp_path):
    project_root = Path(init_project("demo", path=str(tmp_path), provider="fake", model="fake-model"))
    experiment = project_root / "experiment.py"
    experiment.write_text(experiment.read_text(encoding="utf-8") + "\n# local change\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["gittreeclean", str(project_root)])

    assert result.exit_code == 0
    status = subprocess.run(
        ["git", "-C", str(project_root), "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    )
    log = subprocess.run(
        ["git", "-C", str(project_root), "log", "--oneline", "-n", "1"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert status.stdout.strip() == ""
    assert "chore: clean working tree" in log.stdout


def test_gittreeclean_noops_when_project_is_already_clean(tmp_path):
    project_root = Path(init_project("demo", path=str(tmp_path), provider="fake", model="fake-model"))

    head_before = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    runner = CliRunner()
    result = runner.invoke(cli, ["gittreeclean", str(project_root)])

    head_after = subprocess.run(
        ["git", "-C", str(project_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "-C", str(project_root), "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.exit_code == 0
    assert "already clean" in result.output.lower()
    assert head_before == head_after
    assert status.stdout.strip() == ""
