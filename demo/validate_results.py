"""
Validation script for the Irrigation Need baseline model.

Responsibilities:
  - Load the trained pipeline from demo/runs/model.pkl
  - Evaluate it against the held-out test set at demo/hidden/test.csv
  - Train the model automatically if it does not exist yet
  - Expose test_report() for programmatic use (returns a structured dict)
  - Keep the --evaluate / --output CLI interface expected by the harness

Usage:
    # Train first (if model not already saved):
    python3 experiment.py

    # Then validate:
    python3 validate_results.py

    # Harness-compatible invocation:
    python3 validate_results.py --evaluate --output runs/latest/results.json
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
from typing import Any

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

try:
    from experiment import (
        ALL_FEATURES,
        LABEL_ORDER,
        MODEL_PATH,
        TARGET,
        train as train_model,
    )
except ModuleNotFoundError:  # Backward compatibility for older project layouts.
    from base_model import (
        ALL_FEATURES,
        LABEL_ORDER,
        MODEL_PATH,
        TARGET,
        train as train_model,
    )

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = pathlib.Path(__file__).parent
HIDDEN_TEST_PATH = BASE_DIR / "hidden" / "test.csv"


def _parse_iteration_from_run_dir(run_dir: pathlib.Path) -> int | None:
    name = run_dir.name
    if name == "0000_baseline":
        return 0
    if re.fullmatch(r"\d{4}", name):
        return int(name)
    return None


def resolve_best_model_metadata(project_root: pathlib.Path, current_metric: float) -> dict[str, Any]:
    results_path = project_root / "logs" / "results.jsonl"
    best_iteration_num: int | None = None
    best_metric = float("-inf")
    best_experiment_path: str | None = None

    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("outcome") not in {"baseline", "kept"}:
                continue
            metric_value = record.get("metric_value")
            iteration = record.get("iteration")
            run_dir = record.get("run_dir")
            if not isinstance(metric_value, (int, float)) or not isinstance(iteration, int):
                continue
            if not isinstance(run_dir, str):
                continue
            experiment_path = project_root / run_dir / "experiment.py"
            experiment_relpath = (
                experiment_path.relative_to(project_root).as_posix()
                if experiment_path.exists()
                else None
            )
            if metric_value > best_metric or (
                metric_value == best_metric and (best_iteration_num is None or iteration > best_iteration_num)
            ):
                best_metric = float(metric_value)
                best_iteration_num = iteration
                best_experiment_path = experiment_relpath

    current_run_dir_value = os.environ.get("FAST_RESEARCH_RUN_DIR")
    if current_run_dir_value:
        current_run_dir = pathlib.Path(current_run_dir_value).resolve()
        try:
            current_run_dir.relative_to(project_root)
        except ValueError:
            current_run_dir = None
        if current_run_dir is not None:
            current_iteration_num = _parse_iteration_from_run_dir(current_run_dir)
            current_experiment_path = current_run_dir / "experiment.py"
            current_experiment_relpath = (
                current_experiment_path.relative_to(project_root).as_posix()
                if current_experiment_path.exists()
                else None
            )
            if current_metric >= best_metric and current_iteration_num is not None:
                best_iteration_num = current_iteration_num
                best_experiment_path = current_experiment_relpath

    if best_iteration_num is None and (project_root / "experiment.py").exists():
        best_experiment_path = "experiment.py"

    return {
        "best_model_iteration_num": best_iteration_num,
        "best_model_experiment_path": best_experiment_path,
    }


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------
def test_report(
    model_path: pathlib.Path = MODEL_PATH,
    test_path: pathlib.Path = HIDDEN_TEST_PATH,
    force_retrain: bool = False,
) -> dict[str, Any]:
    """
    Load the saved model, run it on *test_path*, and return a report dict.

    Returns
    -------
    dict with keys:
        accuracy        : float
        classification_report : str  (human-readable table)
        confusion_matrix : dict  {label: {label: count}}
        per_class_accuracy : dict  {label: float}
        support         : dict  {label: int}
        model_path      : str
        test_path       : str
    """
    if force_retrain:
        print(f"Retraining model from current experiment.py into {model_path} ...")
        train_model(model_path=model_path)
    elif not model_path.exists():
        print(f"Model not found at {model_path}. Training baseline model first ...")
        train_model(model_path=model_path)

    print(f"Loading model from {model_path} ...")
    pipeline = joblib.load(model_path)

    print(f"Loading test data from {test_path} ...")
    test_df = pd.read_csv(test_path)
    print(f"  Rows: {len(test_df):,}")

    X_test = test_df[ALL_FEATURES]
    y_test = test_df[TARGET]

    # Predict
    y_pred = pipeline.predict(X_test)

    # --- Metrics ---
    accuracy = accuracy_score(y_test, y_pred)

    cls_report_str = classification_report(
        y_test, y_pred, labels=LABEL_ORDER, digits=4
    )

    cm = confusion_matrix(y_test, y_pred, labels=LABEL_ORDER)
    cm_dict = {
        actual: {pred: int(cm[i][j]) for j, pred in enumerate(LABEL_ORDER)}
        for i, actual in enumerate(LABEL_ORDER)
    }

    per_class_acc = {}
    support = {}
    for i, label in enumerate(LABEL_ORDER):
        row_sum = int(cm[i].sum())
        support[label] = row_sum
        per_class_acc[label] = (
            round(int(cm[i][i]) / row_sum, 4) if row_sum > 0 else 0.0
        )

    report = {
        "accuracy": round(accuracy, 4),
        "classification_report": cls_report_str,
        "confusion_matrix": cm_dict,
        "per_class_accuracy": per_class_acc,
        "support": support,
        "model_path": str(model_path),
        "test_path": str(test_path),
    }

    _print_report(report)
    return report


def _print_report(report: dict[str, Any]) -> None:
    """Pretty-print the validation report to stdout."""
    sep = "=" * 62
    print(f"\n{sep}")
    print("VALIDATION REPORT — Hidden Test Set")
    print(sep)
    print(f"Model : {report['model_path']}")
    print(f"Data  : {report['test_path']}")
    print(sep)
    print(f"Accuracy : {report['accuracy']:.4f}  ({report['accuracy'] * 100:.2f}%)")
    print("\nClassification Report:")
    print(report["classification_report"])

    print("Confusion Matrix (rows=actual, cols=predicted):")
    header = f"{'':10s}" + "".join(f"{lbl:>10s}" for lbl in LABEL_ORDER)
    print(header)
    for actual in LABEL_ORDER:
        row_str = f"{actual:10s}" + "".join(
            f"{report['confusion_matrix'][actual][pred]:>10d}" for pred in LABEL_ORDER
        )
        print(row_str)

    print("\nPer-class accuracy:")
    for label in LABEL_ORDER:
        acc = report["per_class_accuracy"][label]
        sup = report["support"][label]
        print(f"  {label:8s}: {acc:.4f}  (n={sup:,})")

    print(sep)
    print(f"Final METRIC (accuracy): {report['accuracy']:.4f}")
    print(sep)


# ---------------------------------------------------------------------------
# CLI / harness entry point
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the irrigation need model.")
    parser.add_argument("--evaluate", action="store_true", help="Run evaluation.")
    parser.add_argument("--output", required=False, help="Path to write JSON results.")
    args = parser.parse_args()

    report = test_report(force_retrain=args.evaluate)
    metric = report["accuracy"]

    if args.output:
        output_path = BASE_DIR / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"metric": metric, **resolve_best_model_metadata(BASE_DIR, metric)}
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nResults written → {output_path}")


if __name__ == "__main__":
    main()
