from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from goalseek.api import (
    add_direction,
    build_summary,
    get_status,
    run_baseline,
    run_loop,
    run_setup,
    run_step,
)
from goalseek.gitops.repo import Repo
from goalseek.utils.json import load_json, load_jsonl
from tests.helpers import write_fake_provider


def test_project_scaffold_and_baseline(project_factory):
    project_root = project_factory("baseline")
    assert (Path(project_root) / "manifest.yaml").exists()
    setup = run_setup(str(project_root))
    assert setup["summary"]["project_name"] == "baseline"
    assert setup["summary"]["hidden_paths"] == ["validate_results.py", "hidden/**"]
    assert setup["context_inventory"]["file_count"] == 5

    baseline = run_baseline(str(project_root))
    assert baseline["record"]["outcome"] == "baseline"
    assert (Path(project_root) / "runs" / "0000_baseline" / "result.json").exists()
    assert (Path(project_root) / "runs" / "0000_baseline" / "experiment.py").exists()
    history = load_json(Path(project_root) / "runs" / "latest" / "history.json")
    assert history == [
        {
            "hypothesis_summary": "Baseline",
            "iteration": 0,
            "iteration_result": "baseline",
            "iteration_score": 0.0,
            "run_dir": "runs/0000_baseline",
        }
    ]

    status = get_status(str(project_root))
    assert status["current_phase"] == "READ_CONTEXT"

    state = load_json(Path(project_root) / "logs" / "state.json")
    assert state["status"] == "ready"
    assert state["last_outcome"] == "baseline"

    stepped = run_step(str(project_root))
    assert stepped["current_iteration"] == 1
    assert stepped["current_phase"] == "PLAN"


def test_setup_executes_project_setup_script(project_factory):
    project_root = project_factory("setup-script")
    setup_script = Path(project_root) / "setup.py"
    setup_script.write_text(
        """
from pathlib import Path


def main() -> None:
    target = Path(__file__).parent / "data" / "setup-ran.txt"
    target.write_text("done\\n", encoding="utf-8")


if __name__ == "__main__":
    main()
""".lstrip(),
        encoding="utf-8",
    )

    run_setup(str(project_root))

    assert (Path(project_root) / "data" / "setup-ran.txt").read_text(encoding="utf-8") == "done\n"


def test_setup_hidden_test_artifact_is_ignored(project_factory):
    project_root = project_factory("setup-ignore-hidden-test")
    setup_script = Path(project_root) / "setup.py"
    setup_script.write_text(
        """
from pathlib import Path


def main() -> None:
    target = Path(__file__).parent / "hidden" / "test.csv"
    target.write_text("x,y\\n1,2\\n", encoding="utf-8")


if __name__ == "__main__":
    main()
""".lstrip(),
        encoding="utf-8",
    )
    Repo(project_root).commit(["setup.py"], "test: customize setup script")

    run_setup(str(project_root))

    status = subprocess.run(
        ["git", "-C", str(project_root), "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert status.stdout.strip() == ""


def test_three_iteration_run_with_revert_and_skip(project_factory):
    project_root = project_factory("loop")
    write_fake_provider(project_root, "fake_provider_mixed.yaml")
    run_baseline(str(project_root))

    result = run_loop(str(project_root), iterations=3)
    assert result["current_iteration"] == 4
    assert not (Path(project_root) / "runs" / "0001" / "reasoning.md").exists()
    assert (Path(project_root) / "runs" / "0001" / "experiment.py").exists()
    assert (Path(project_root) / "runs" / "0002" / "experiment.py").exists()
    assert (Path(project_root) / "runs" / "0003" / "experiment.py").exists()
    assert "# iteration 1" in (Path(project_root) / "runs" / "0001" / "experiment.py").read_text(encoding="utf-8")
    assert "# iteration 2" in (Path(project_root) / "runs" / "0002" / "experiment.py").read_text(encoding="utf-8")
    assert "# iteration 2" not in (Path(project_root) / "runs" / "0003" / "experiment.py").read_text(encoding="utf-8")

    records = load_jsonl(Path(project_root) / "logs" / "results.jsonl")
    outcomes = [item["outcome"] for item in records]
    assert outcomes == ["baseline", "kept", "reverted_worse_metric", "skipped_no_change"]
    history = load_json(Path(project_root) / "runs" / "latest" / "history.json")
    assert history == [
        {
            "hypothesis_summary": "Baseline",
            "iteration": 0,
            "iteration_result": "baseline",
            "iteration_score": 0.0,
            "run_dir": "runs/0000_baseline",
        },
        {
            "hypothesis_summary": "Increase metric",
            "iteration": 1,
            "iteration_result": "kept",
            "iteration_score": 5.0,
            "run_dir": "runs/0001",
        },
        {
            "hypothesis_summary": "Worsen metric",
            "iteration": 2,
            "iteration_result": "reverted_worse_metric",
            "iteration_score": 1.0,
            "run_dir": "runs/0002",
        },
        {
            "hypothesis_summary": "No-op",
            "iteration": 3,
            "iteration_result": "skipped_no_change",
            "iteration_score": None,
            "run_dir": "runs/0003",
        },
    ]

    summary = build_summary(str(project_root))
    assert summary["kept_iterations"] == 1
    assert summary["reverted_iterations"] == 1
    assert summary["skipped_iterations"] == 1


def test_step_mode_resume_and_direction_injection(project_factory):
    project_root = project_factory("step-integration")
    write_fake_provider(project_root, "fake_provider_single_improve.yaml")
    run_baseline(str(project_root))

    state = run_step(str(project_root))
    assert state["current_phase"] == "PLAN"

    direction = add_direction(str(project_root), "Prefer a smaller change first.")
    assert direction["applies_from_iteration"] == 1

    for _ in range(6):
        state = run_step(str(project_root))

    assert state["current_iteration"] == 2
    assert state["current_phase"] == "READ_CONTEXT"
    records = load_jsonl(Path(project_root) / "logs" / "results.jsonl")
    assert records[-1]["outcome"] == "kept"


def test_validate_results_includes_best_model_iteration_metadata(project_factory):
    project_root = project_factory("results-metadata")
    project_root = Path(project_root)

    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    (project_root / "runs" / "0002").mkdir(parents=True, exist_ok=True)
    (project_root / "runs" / "0003").mkdir(parents=True, exist_ok=True)
    (project_root / "runs" / "0002" / "experiment.py").write_text(
        "METRIC = 2\n",
        encoding="utf-8",
    )
    (project_root / "runs" / "0003" / "experiment.py").write_text(
        "METRIC = 5\n",
        encoding="utf-8",
    )
    (project_root / "experiment.py").write_text(
        "from __future__ import annotations\n\nMETRIC = 5\n\n\ndef run() -> dict[str, int]:\n    return {\"metric\": METRIC}\n\n\nif __name__ == \"__main__\":\n    print(run())\n",
        encoding="utf-8",
    )
    (project_root / "logs" / "results.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "iteration": 0,
                        "run_dir": "runs/0000_baseline",
                        "outcome": "baseline",
                        "metric_value": 1,
                    }
                ),
                json.dumps(
                    {
                        "iteration": 2,
                        "run_dir": "runs/0002",
                        "outcome": "kept",
                        "metric_value": 2,
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(project_root / "validate_results.py"),
            "--evaluate",
            "--output",
            "runs/latest/results.json",
        ],
        check=True,
        cwd=project_root,
        env={
            **os.environ,
            "GOALSEEK_RUN_DIR": str(project_root / "runs" / "0003"),
        },
        capture_output=True,
        text=True,
    )

    payload = load_json(project_root / "runs" / "latest" / "results.json")
    assert payload["metric"] == 5
    assert payload["best_model_iteration_num"] == 3
    assert payload["best_model_experiment_path"] == "runs/0003/experiment.py"
