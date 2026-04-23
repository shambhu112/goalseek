from __future__ import annotations

from pathlib import Path

from goalseek.core.direction_service import DirectionService
from goalseek.core.loop_engine import LoopEngine
from goalseek.core.manifest_service import ManifestService
from goalseek.core.project_service import ProjectService
from goalseek.core.setup_phase import SetupPhase
from goalseek.core.state_store import StateStore
from goalseek.core.summary_service import SummaryService
from goalseek.core.step_engine import StepEngine
from goalseek.errors import GitOperationError
from goalseek.gitops.repo import Repo
from goalseek.utils.json import load_jsonl


def init_project(name: str, path: str | None = None, **overrides) -> str:
    root = ProjectService().create_scaffold(
        name=name,
        path=path,
        provider=overrides.get("provider", "codex"),
        model=overrides.get("model", "gpt-5-codex"),
        git_init=not overrides.get("no_git_init", False),
        overwrite_existing=overrides.get("overwrite_existing", False),
    )
    return str(root)


def validate_manifest(project_root: str) -> None:
    ManifestService().validate(project_root)


def run_setup(project_root: str, **overrides) -> dict:
    return SetupPhase().run(project_root, overrides)


def run_baseline(project_root: str, **overrides) -> dict:
    return LoopEngine().run_baseline(project_root, overrides)


def run_loop(project_root: str, iterations: int | None = None, forever: bool = False, **overrides) -> dict:
    time_limit_minutes = overrides.pop("time_limit_minutes", None)
    return LoopEngine().run_loop(
        project_root,
        iterations=iterations,
        forever=forever,
        time_limit_minutes=time_limit_minutes,
        overrides=overrides,
    )


def run_step(project_root: str, **overrides) -> dict:
    return StepEngine().step(project_root, overrides)


def add_direction(project_root: str, message: str, applies_from_iteration: int | None = None) -> dict:
    root = Path(project_root).expanduser().resolve()
    if applies_from_iteration is None:
        state = StateStore(root).load()
        if state:
            applies_from_iteration = state.current_iteration
        else:
            results = load_jsonl(root / "logs" / "results.jsonl")
            applies_from_iteration = (results[-1].get("iteration", 0) + 1) if results else 1
    return DirectionService().add(root, message, applies_from_iteration)


def get_status(project_root: str) -> dict:
    root = Path(project_root).expanduser().resolve()
    state = StateStore(root).load()
    results = load_jsonl(root / "logs" / "results.jsonl")
    latest = results[-1] if results else {}
    return {
        "project_root": str(root),
        "current_iteration": state.current_iteration if state else None,
        "current_phase": state.current_phase.value if state else None,
        "provider": state.provider if state else None,
        "model": state.model if state else None,
        "latest_retained_metric": state.retained_metric if state else None,
        "pending_commit_hash": state.pending_commit if state else None,
        "rollback_state": state.rollback_state if state else None,
        "latest_outcome": latest.get("outcome"),
    }


def build_summary(project_root: str) -> dict:
    return SummaryService().build(project_root)


def clean_git_tree(project_root: str, message: str = "chore: clean working tree") -> dict:
    root = ProjectService().discover_root(project_root)
    repo = Repo(root)
    if not repo.is_repo():
        raise GitOperationError(f"project is not inside a git repository: {root}")
    changed_files = repo.working_tree_changed_files()
    if not changed_files:
        return {
            "project_root": str(root),
            "status": "already_clean",
            "commit_hash": None,
            "commit_message": None,
            "changed_files": [],
        }
    commit_hash = repo.commit_all(message)
    return {
        "project_root": str(root),
        "status": "committed",
        "commit_hash": commit_hash,
        "commit_message": message,
        "changed_files": changed_files,
    }
