from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from goalseek.core.artifact_store import ArtifactStore
from goalseek.core.context_reader import ContextReader
from goalseek.core.direction_service import DirectionService
from goalseek.core.manifest_service import ManifestScope, ManifestService
from goalseek.core.project_service import ProjectService
from goalseek.core.state_store import StateStore
from goalseek.errors import GitOperationError, ProviderExecutionError, VerificationError
from goalseek.gitops.repo import Repo
from goalseek.gitops.rollback import revert_commit
from goalseek.models.results import ResultRecord
from goalseek.models.state import IterationPayload, LoopPhase, LoopState, LoopStatus
from goalseek.providers.base import ProviderRequest
from goalseek.providers.prompts import build_implementation_prompt, build_planning_prompt
from goalseek.providers.registry import ProviderRegistry
from goalseek.utils.json import load_jsonl
from goalseek.verification.metrics import (
    compare,
    extract_metric,
    thresholds_pass,
    tie_breaker_prefers_candidate,
)
from goalseek.verification.runner import VerificationRunner


logger = logging.getLogger(__name__)


class LoopEngine:
    def __init__(self) -> None:
        self.project_service = ProjectService()
        self.manifest_service = ManifestService()
        self.provider_registry = ProviderRegistry()
        self.direction_service = DirectionService()
        self.verifier = VerificationRunner()

    def run_baseline(self, project_root: str | Path, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        root = self.project_service.discover_root(project_root)
        scope = self.manifest_service.validate(root)
        config = self.project_service.load_effective_config(root, overrides)
        self.project_service.configure_logging(root, config)
        logger.info("Running baseline for %s", root)
        artifacts = ArtifactStore(root)
        repo = Repo(root)
        if not repo.is_repo():
            raise GitOperationError("baseline requires a git repository")
        run_dir = artifacts.baseline_dir()
        experiment_path = root / "experiment.py"
        if experiment_path.exists():
            artifacts.copy_file(run_dir, experiment_path, "experiment.py")
        env_snapshot = self.project_service.environment_snapshot(
            root,
            config,
            config.provider.implementation.name,
            config.provider.implementation.model,
        )
        verification = self.verifier.run(root, scope.manifest.verification.commands, run_dir)
        artifacts.write_text(run_dir, "verifier.log", verification.combined_log)
        artifacts.write_json(run_dir, "env.json", env_snapshot)
        metric = None
        notes = None
        if verification.exit_code == 0:
            try:
                metric = extract_metric(scope.manifest.metric, root, verification.command_results)
            except VerificationError as exc:
                notes = f"Baseline metric extraction failed. See {run_dir / 'verifier.log'}"
                record = ResultRecord(
                    timestamp=_timestamp(),
                    iteration=0,
                    run_dir=run_dir.relative_to(root).as_posix(),
                    provider=config.provider.implementation.name,
                    model=config.provider.implementation.model,
                    mode="baseline",
                    outcome="baseline",
                    verification_exit_code=verification.exit_code,
                    verification_command_names=[item.name for item in verification.command_results],
                    notes=notes,
                    hypothesis_summary="Baseline",
                    metric_value=None,
                    changed_loc=0,
                )
                artifacts.write_json(run_dir, "result.json", record.model_dump(mode="python"))
                artifacts.append_result(record.model_dump(mode="python"))
                artifacts.refresh_latest_history()
                raise VerificationError(notes) from exc
            artifacts.write_json(run_dir, "metrics.json", metric.model_dump(mode="python"))
        else:
            notes = self._format_baseline_failure_message(run_dir, verification)
        record = ResultRecord(
            timestamp=_timestamp(),
            iteration=0,
            run_dir=run_dir.relative_to(root).as_posix(),
            provider=config.provider.implementation.name,
            model=config.provider.implementation.model,
            mode="baseline",
            outcome="baseline",
            verification_exit_code=verification.exit_code,
            verification_command_names=[item.name for item in verification.command_results],
            notes=notes,
            hypothesis_summary="Baseline",
            metric_value=metric.value if metric else None,
            changed_loc=0,
        )
        artifacts.write_json(run_dir, "result.json", record.model_dump(mode="python"))
        artifacts.append_result(record.model_dump(mode="python"))
        artifacts.refresh_latest_history()
        if verification.exit_code != 0:
            logger.warning("Baseline verification failed for %s with exit_code=%s", root, verification.exit_code)
            raise VerificationError(notes or f"baseline verification failed; see {run_dir / 'verifier.log'}")
        StateStore(root).initialize(
            provider=config.provider.implementation.name,
            model=config.provider.implementation.model,
            retained_metric=metric.value if metric else None,
            retained_changed_loc=0,
            last_outcome="baseline",
        )
        logger.info("Baseline complete for %s with metric=%s", root, metric.value if metric else None)
        return {
            "record": record.model_dump(mode="python"),
            "metric": metric.model_dump(mode="python") if metric else None,
            "run_dir": str(run_dir),
        }

    def execute_phase(
        self,
        project_root: str | Path,
        state: LoopState,
        overrides: dict[str, Any] | None = None,
        stream_callback=None,
    ) -> LoopState:
        root = self.project_service.discover_root(project_root)
        scope = self.manifest_service.validate(root)
        config = self.project_service.load_effective_config(root, overrides)
        self.project_service.configure_logging(root, config)
        repo = Repo(root)
        artifacts = ArtifactStore(root)
        state.status = LoopStatus.PAUSED
        logger.info(
            "Executing phase=%s for project=%s iteration=%s",
            state.current_phase.value,
            root,
            state.current_iteration,
        )
        if state.current_phase == LoopPhase.READ_CONTEXT:
            return self._phase_read_context(root, scope, repo, artifacts, state, config)
        if state.current_phase == LoopPhase.PLAN:
            return self._phase_plan(root, scope, state, config, artifacts)
        if state.current_phase == LoopPhase.APPLY_CHANGE:
            return self._phase_apply(root, scope, repo, artifacts, state, config)
        if state.current_phase == LoopPhase.COMMIT:
            return self._phase_commit(root, repo, state)
        if state.current_phase == LoopPhase.VERIFY:
            return self._phase_verify(root, scope, artifacts, state, stream_callback)
        if state.current_phase == LoopPhase.DECIDE:
            return self._phase_decide(root, scope, repo, state)
        if state.current_phase == LoopPhase.LOG:
            return self._phase_log(root, scope, artifacts, repo, state)
        raise ProviderExecutionError(f"unknown phase: {state.current_phase}")

    def initialize_or_load_state(
        self,
        project_root: str | Path,
        overrides: dict[str, Any] | None = None,
    ) -> LoopState:
        root = self.project_service.discover_root(project_root)
        config = self.project_service.load_effective_config(root, overrides)
        self.project_service.configure_logging(root, config)
        store = StateStore(root)
        existing = store.load()
        if existing:
            logger.debug("Loaded existing loop state for %s at iteration=%s", root, existing.current_iteration)
            return existing
        results = load_jsonl(root / "logs" / "results.jsonl")
        if not results:
            raise GitOperationError(f"baseline must be run before the loop; run `goalseek baseline {root}` first")
        retained_metric = None
        retained_changed_loc = 0
        current_iteration = 1
        for item in results:
            if item.get("outcome") in {"baseline", "kept"} and item.get("metric_value") is not None:
                retained_metric = item["metric_value"]
                retained_changed_loc = item.get("changed_loc", retained_changed_loc)
            if item.get("iteration", 0) >= current_iteration:
                current_iteration = item["iteration"] + 1
        state = LoopState(
            status=LoopStatus.PAUSED,
            current_iteration=current_iteration,
            current_phase=LoopPhase.READ_CONTEXT,
            provider=config.provider.implementation.name,
            model=config.provider.implementation.model,
            retained_metric=retained_metric,
            retained_changed_loc=retained_changed_loc,
        )
        logger.info("Initialized loop state for %s at iteration=%s", root, current_iteration)
        return store.save(state)

    def run_loop(
        self,
        project_root: str | Path,
        iterations: int | None = None,
        forever: bool = False,
        time_limit_minutes: float | None = None,
        overrides: dict[str, Any] | None = None,
        stream_callback=None,
    ) -> dict[str, Any]:
        root = self.project_service.discover_root(project_root)
        store = StateStore(root)
        state = self.initialize_or_load_state(root, overrides)
        logger.info(
            "Starting loop for %s iterations=%s forever=%s time_limit_minutes=%s",
            root,
            iterations,
            forever,
            time_limit_minutes,
        )
        target_iteration = state.current_iteration + iterations - 1 if iterations else None
        deadline = None
        if time_limit_minutes is not None:
            import time

            deadline = time.time() + (time_limit_minutes * 60)
        completed_this_call = 0
        while True:
            state.status = LoopStatus.RUNNING
            state = self.execute_phase(root, state, overrides, stream_callback=stream_callback)
            store.save(state)
            if state.current_phase == LoopPhase.READ_CONTEXT and state.iteration_data == IterationPayload():
                completed_this_call += 1
            if iterations is not None and completed_this_call >= iterations:
                break
            if target_iteration is not None and state.current_iteration > target_iteration:
                break
            if deadline is not None:
                import time

                if time.time() >= deadline:
                    break
            if not forever and iterations is None and time_limit_minutes is None:
                break
        state.status = LoopStatus.PAUSED
        store.save(state)
        logger.info(
            "Loop paused for %s at iteration=%s phase=%s",
            root,
            state.current_iteration,
            state.current_phase.value,
        )
        return {
            "current_iteration": state.current_iteration,
            "current_phase": state.current_phase.value,
            "last_outcome": state.last_outcome,
        }

    def _phase_read_context(
        self,
        root: Path,
        scope: ManifestScope,
        repo: Repo,
        artifacts: ArtifactStore,
        state: LoopState,
        config,
    ) -> LoopState:
        run_dir = artifacts.iteration_dir(state.current_iteration)
        context = ContextReader(repo).read(root, scope, state.current_iteration)
        git_before = f"{context.git_log}\n\n{context.git_diff}".strip()
        env_snapshot = self.project_service.environment_snapshot(root, config, state.provider, state.model)
        artifacts.write_text(run_dir, "git_before.txt", git_before)
        artifacts.write_json(run_dir, "env.json", env_snapshot)
        state.iteration_data = IterationPayload(
            run_dir=run_dir.relative_to(root).as_posix(),
            git_before=git_before,
            environment=env_snapshot,
            context_summary={
                "file_count": len(context.files),
                "latest_results_count": len(context.latest_results),
                "active_directions_count": len(context.directions),
            },
        )
        state.current_phase = LoopPhase.PLAN
        logger.debug("Read context for iteration=%s with %s files", state.current_iteration, len(context.files))
        return state

    def _phase_plan(self, root: Path, scope: ManifestScope, state: LoopState, config, artifacts: ArtifactStore) -> LoopState:
        provider_config = config.provider.hypothesis
        provider = self.provider_registry.get(provider_config.name)
        recent_results = load_jsonl(root / "logs" / "results.jsonl")
        non_kept_streak = 0
        for item in reversed(recent_results):
            if item.get("outcome") in {"baseline", "kept"}:
                break
            non_kept_streak += 1
        prompt = build_planning_prompt(scope, ContextReader().read(root, scope, state.current_iteration), state.current_iteration, non_kept_streak >= 3)
        response = provider.plan(
            ProviderRequest(
                project_root=root,
                provider_name=provider_config.name,
                model_name=provider_config.model,
                mode="hypothesis",
                prompt_text=prompt,
                writable_paths=scope.writable_patterns,
                generated_paths=scope.generated_patterns,
                non_interactive=provider_config.non_interactive,
                timeout_sec=provider_config.timeout_sec,
                iteration=state.current_iteration,
            )
        )
        run_dir = root / (state.iteration_data.run_dir or f"runs/{state.current_iteration:04d}")
        artifacts.write_text(run_dir, "prompt.md", prompt)
        artifacts.write_text(run_dir, "provider_output.md", response.raw_text)
        if response.exit_code != 0:
            state.iteration_data.prompt_text = prompt
            state.iteration_data.provider_output = response.raw_text
            state.iteration_data.notes = response.error or "provider planning failed"
            state.iteration_data.decision_outcome = "skipped_provider_failure"
            state.current_phase = LoopPhase.LOG
            logger.warning("Planning failed for iteration=%s: %s", state.current_iteration, state.iteration_data.notes)
            return state
        state.iteration_data.prompt_text = prompt
        state.iteration_data.provider_output = response.raw_text
        state.iteration_data.plan_text = response.raw_text
        state.iteration_data.plan_title = str(response.metadata.get("title", f"iteration {state.current_iteration}"))
        planned_files = response.metadata.get("planned_files", [])
        state.iteration_data.planned_files = list(planned_files) if isinstance(planned_files, list) else []
        artifacts.write_text(run_dir, "plan.md", response.raw_text)
        state.current_phase = LoopPhase.APPLY_CHANGE
        logger.info("Planning complete for iteration=%s title=%s", state.current_iteration, state.iteration_data.plan_title)
        return state

    def _phase_apply(
        self,
        root: Path,
        scope: ManifestScope,
        repo: Repo,
        artifacts: ArtifactStore,
        state: LoopState,
        config,
    ) -> LoopState:
        repo.ensure_clean()
        provider_config = config.provider.implementation
        provider = self.provider_registry.get(provider_config.name)
        response = provider.implement(
            ProviderRequest(
                project_root=root,
                provider_name=provider_config.name,
                model_name=provider_config.model,
                mode="implementation",
                prompt_text=build_implementation_prompt(scope, state.iteration_data.plan_text or "", state.current_iteration),
                writable_paths=scope.writable_patterns,
                generated_paths=scope.generated_patterns,
                non_interactive=provider_config.non_interactive,
                timeout_sec=provider_config.timeout_sec,
                iteration=state.current_iteration,
            )
        )
        state.iteration_data.provider_output = (state.iteration_data.provider_output or "") + "\n\n" + response.raw_text
        if response.exit_code != 0:
            state.iteration_data.notes = response.error or "provider implementation failed"
            state.iteration_data.decision_outcome = "skipped_provider_failure"
            state.current_phase = LoopPhase.LOG
            logger.warning("Implementation failed for iteration=%s: %s", state.current_iteration, state.iteration_data.notes)
            return state
        changed_files = repo.working_tree_changed_files()
        if not changed_files:
            state.iteration_data.changed_files = []
            state.iteration_data.decision_outcome = "skipped_no_change"
            state.current_phase = LoopPhase.LOG
            logger.info("Implementation produced no file changes for iteration=%s", state.current_iteration)
            return state
        self._snapshot_experiment(root, artifacts, state)
        out_of_scope = [path for path in changed_files if not scope.is_writable(path) and not scope.is_generated(path)]
        if out_of_scope:
            commit_hash = repo.commit(changed_files, "experiment: scope violation")
            rollback_hash = revert_commit(repo, commit_hash)
            state.iteration_data.changed_files = changed_files
            state.iteration_data.commit_hash = commit_hash
            state.iteration_data.rollback_commit_hash = rollback_hash
            state.iteration_data.notes = f"scope violation: {', '.join(out_of_scope)}"
            state.iteration_data.decision_outcome = "reverted_scope_violation"
            state.current_phase = LoopPhase.LOG
            logger.warning("Scope violation for iteration=%s files=%s", state.current_iteration, ", ".join(out_of_scope))
            return state
        state.iteration_data.changed_files = changed_files
        state.current_phase = LoopPhase.COMMIT
        logger.info("Implementation changed %s file(s) for iteration=%s", len(changed_files), state.current_iteration)
        return state

    def _phase_commit(self, root: Path, repo: Repo, state: LoopState) -> LoopState:
        parent_commit = repo.head()
        commit_title = state.iteration_data.plan_title or f"iteration {state.current_iteration}"
        commit_hash = repo.commit(state.iteration_data.changed_files, f"experiment: {commit_title}")
        state.pending_commit = commit_hash
        state.iteration_data.commit_hash = commit_hash
        state.iteration_data.parent_commit_hash = parent_commit
        state.iteration_data.changed_loc = repo.changed_loc_for_commit(commit_hash)
        state.current_phase = LoopPhase.VERIFY
        logger.info("Committed iteration=%s as %s", state.current_iteration, commit_hash)
        return state

    def _phase_verify(
        self,
        root: Path,
        scope: ManifestScope,
        artifacts: ArtifactStore,
        state: LoopState,
        stream_callback=None,
    ) -> LoopState:
        run_dir = root / (state.iteration_data.run_dir or f"runs/{state.current_iteration:04d}")
        verification = self.verifier.run(root, scope.manifest.verification.commands, run_dir, stream_callback=stream_callback)
        artifacts.write_text(run_dir, "verifier.log", verification.combined_log)
        state.iteration_data.verification_log = verification.combined_log
        state.iteration_data.verification_exit_code = verification.exit_code
        state.iteration_data.verification_command_names = [item.name for item in verification.command_results]
        if verification.exit_code != 0:
            state.iteration_data.decision_outcome = "skipped_verification_crash"
            state.current_phase = LoopPhase.LOG
            logger.warning("Verification failed for iteration=%s exit_code=%s", state.current_iteration, verification.exit_code)
            return state
        metric = extract_metric(scope.manifest.metric, root, verification.command_results)
        state.iteration_data.metric_value = metric.value
        state.current_phase = LoopPhase.DECIDE
        logger.info("Verification complete for iteration=%s metric=%s", state.current_iteration, metric.value)
        return state

    def _phase_decide(self, root: Path, scope: ManifestScope, repo: Repo, state: LoopState) -> LoopState:
        current_metric = state.iteration_data.metric_value
        retained_metric = state.retained_metric
        if current_metric is None:
            state.iteration_data.decision_outcome = "skipped_verification_crash"
            state.current_phase = LoopPhase.LOG
            return state
        if not scope.manifest.metric or not scope.manifest.metric.extractor:
            raise ProviderExecutionError("metric configuration missing")
        thresholds_passed = thresholds_pass(scope.manifest.metric, current_metric)
        if not thresholds_passed:
            rollback_hash = revert_commit(repo, state.iteration_data.commit_hash or state.pending_commit or "")
            state.iteration_data.rollback_commit_hash = rollback_hash
            state.iteration_data.decision_outcome = "reverted_threshold_failure"
            state.current_phase = LoopPhase.LOG
            logger.info("Threshold check failed for iteration=%s metric=%s", state.current_iteration, current_metric)
            return state
        if retained_metric is None:
            state.retained_metric = current_metric
            state.retained_changed_loc = state.iteration_data.changed_loc
            state.iteration_data.decision_outcome = "kept"
            state.current_phase = LoopPhase.LOG
            logger.info("Keeping first candidate for iteration=%s metric=%s", state.current_iteration, current_metric)
            return state
        decision = compare(retained_metric, current_metric, scope.manifest.metric.direction, scope.manifest.metric.epsilon)
        if decision == "better":
            state.retained_metric = current_metric
            state.retained_changed_loc = state.iteration_data.changed_loc
            state.iteration_data.decision_outcome = "kept"
        elif decision == "equal" and tie_breaker_prefers_candidate(state.retained_changed_loc, state.iteration_data.changed_loc):
            state.retained_metric = current_metric
            state.retained_changed_loc = state.iteration_data.changed_loc
            state.iteration_data.decision_outcome = "kept"
        else:
            rollback_hash = revert_commit(repo, state.iteration_data.commit_hash or state.pending_commit or "")
            state.iteration_data.rollback_commit_hash = rollback_hash
            state.iteration_data.decision_outcome = "reverted_worse_metric"
        state.current_phase = LoopPhase.LOG
        logger.info(
            "Decision complete for iteration=%s outcome=%s metric=%s retained_metric=%s",
            state.current_iteration,
            state.iteration_data.decision_outcome,
            current_metric,
            state.retained_metric,
        )
        return state

    def _phase_log(self, root: Path, scope: ManifestScope, artifacts: ArtifactStore, repo: Repo, state: LoopState) -> LoopState:
        run_dir = root / (state.iteration_data.run_dir or f"runs/{state.current_iteration:04d}")
        git_after_target = state.iteration_data.rollback_commit_hash or state.iteration_data.commit_hash or "HEAD"
        git_after = repo.show(git_after_target)
        artifacts.write_text(run_dir, "git_after.txt", git_after)
        self._snapshot_experiment(root, artifacts, state, overwrite=False)
        if state.iteration_data.provider_output is not None:
            artifacts.write_text(run_dir, "provider_output.md", state.iteration_data.provider_output)
        result_discussion = self._build_result_discussion(state)
        artifacts.write_text(run_dir, "results_discussion.md", result_discussion)
        if state.iteration_data.metric_value is not None:
            artifacts.write_json(
                run_dir,
                "metrics.json",
                {
                    "name": scope.manifest.metric.name,
                    "value": state.iteration_data.metric_value,
                    "direction": scope.manifest.metric.direction,
                },
            )
        record = ResultRecord(
            timestamp=_timestamp(),
            iteration=state.current_iteration,
            run_dir=run_dir.relative_to(root).as_posix(),
            commit_hash=state.iteration_data.commit_hash,
            parent_commit_hash=state.iteration_data.parent_commit_hash,
            provider=state.provider,
            model=state.model,
            mode="implementation",
            planned_files=state.iteration_data.planned_files,
            changed_files=state.iteration_data.changed_files,
            outcome=state.iteration_data.decision_outcome or "skipped_provider_failure",
            verification_exit_code=state.iteration_data.verification_exit_code or 0,
            verification_command_names=state.iteration_data.verification_command_names,
            repair_attempted=state.iteration_data.repair_attempted,
            rollback_commit_hash=state.iteration_data.rollback_commit_hash,
            notes=state.iteration_data.notes,
            result_discussion="results_discussion.md",
            hypothesis_summary=self._build_hypothesis_summary(state),
            metric_value=state.iteration_data.metric_value,
            changed_loc=state.iteration_data.changed_loc,
        )
        artifacts.write_json(run_dir, "result.json", record.model_dump(mode="python"))
        artifacts.append_result(record.model_dump(mode="python"))
        artifacts.refresh_latest_history()
        state.last_outcome = record.outcome
        state.pending_commit = None
        state.rollback_state = "needed" if state.iteration_data.rollback_commit_hash else "not_needed"
        state.current_iteration += 1
        state.current_phase = LoopPhase.READ_CONTEXT
        state.iteration_data = IterationPayload()
        state.status = LoopStatus.PAUSED
        logger.info("Recorded result for iteration=%s outcome=%s", record.iteration, record.outcome)
        return state

    def _build_result_discussion(self, state: LoopState) -> str:
        return (
            f"# Iteration {state.current_iteration} result\n\n"
            f"Outcome: `{state.iteration_data.decision_outcome}`\n\n"
            f"Metric: `{state.iteration_data.metric_value}`\n\n"
            f"Notes: {state.iteration_data.notes or 'No additional notes.'}\n"
        )

    def _build_hypothesis_summary(self, state: LoopState) -> str:
        if state.iteration_data.plan_title:
            return state.iteration_data.plan_title
        if state.iteration_data.plan_text:
            title = _extract_markdown_title(state.iteration_data.plan_text)
            if title:
                return title
        return f"Iteration {state.current_iteration}"

    def _snapshot_experiment(
        self,
        root: Path,
        artifacts: ArtifactStore,
        state: LoopState,
        *,
        overwrite: bool = True,
    ) -> None:
        source = root / "experiment.py"
        if not source.exists():
            return
        run_dir = root / (state.iteration_data.run_dir or f"runs/{state.current_iteration:04d}")
        target = run_dir / "experiment.py"
        if target.exists() and not overwrite:
            return
        artifacts.copy_file(run_dir, source, "experiment.py")

    def _format_baseline_failure_message(self, run_dir: Path, verification) -> str:
        log_path = run_dir / "verifier.log"
        excerpt = ""
        if verification.command_results:
            last = verification.command_results[-1]
            text = (last.stderr or last.stdout or "").strip()
            if text:
                lines = text.splitlines()
                excerpt = "\n".join(lines[-3:])
        message = (
            f"Baseline verification failed with exit code {verification.exit_code}. "
            f"Verifier log: {log_path}"
        )
        if excerpt:
            message += f"\nVerifier output:\n{excerpt}"
        return message


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _extract_markdown_title(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
        return stripped
    return None
