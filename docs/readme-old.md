# goalseek

`goalseek` is a local-first Python package for running disciplined, git-backed research loops with coding-agent providers.

The project is CLI-first and exposes the same core controls through `goalseek.api`.

## Requirements

- Python 3.11+
- `git`
- `uv` recommended for environment and command management

## Install

With `uv`:

```bash
uv venv
uv pip install -e ".[dev]"
```

With standard `venv`:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Run

Show CLI help:

```bash
uv run goalseek --help
```

Create a project scaffold:

```bash
uv run goalseek project init demo --provider claude_code --model claude-haiku-4-5-20251001
```


If `./demo` already exists, `goalseek project init demo` will ask whether it should delete the directory and recreate the project from scratch. Declining leaves the existing directory unchanged.

Move the test scenario files into ./demo

```bash
./move-testpackage.sh ./demo2 --overwrite
```

When the target directory is already a clean git-backed project scaffold, the helper also records the import as `project: import test package` so baseline and loop runs can start immediately.

Validate the manifest and inspect setup:
```bash
uv run goalseek manifest validate ./demo3
uv run goalseek setup ./demo3
```

Run the baseline:

```bash
uv run goalseek baseline ./demo3
```

Run three iterations:

```bash
uv run goalseek run ./demo3 --iterations 3
```

Advance one phase at a time:

```bash
uv run goalseek step ./demo3
```

Add a direction for the next iteration:

```bash
uv run goalseek direct ./demo3 --message "Try a smaller change first."
```

Inspect status and summary:

```bash
uv run goalseek status ./demo
uv run goalseek summary ./demo
```

Force-clean a project git tree by committing local changes:

```bash
uv run goalseek gittreeclean ./demo3
```

## Manifest Modes

Manifest file entries support four modes:

- `read_only`: visible to the agent, but not writable
- `writable`: visible to the agent and allowed to be modified
- `generated`: reserved for generated artifacts such as `runs/` and `logs/`
- `hidden`: protected from agent-visible context and prompts

The scaffolded manifest uses `hidden/**` as `mode: hidden`, which is intended for items like verification helpers, secrets, or protected ground-truth files.

## CLI Output

The CLI uses Rich for user-facing progress and results:

- in-progress and successful stages are rendered in blue
- failures are rendered in red
- setup, baseline, run, step, status, and summary commands render structured tables instead of raw JSON

`goalseek setup` also shows hidden paths separately from read-only, writable, and generated scope.

## Loop State

`logs/state.json` stores the resumable state for the research loop. It lets `goalseek run`, `goalseek step`, and `goalseek status` know which iteration is active, which phase should run next, and what data has already been collected for the in-progress iteration.

Top-level fields:

- `status`: overall loop status such as `paused` or `running`
- `current_iteration`: the iteration number that will continue next
- `current_phase`: the next phase to execute: `READ_CONTEXT`, `PLAN`, `APPLY_CHANGE`, `COMMIT`, `VERIFY`, `DECIDE`, or `LOG`
- `provider`: implementation provider recorded for the loop, such as `claude_code`
- `model`: model name recorded for the loop
- `pending_commit`: commit created for the current iteration but not yet finalized by the decision step; usually `null` outside `VERIFY` and `DECIDE`
- `rollback_state`: whether the latest iteration needed a revert, typically `not_needed` or `needed`
- `retained_metric`: the best retained metric value so far, usually copied from the baseline or latest kept iteration
- `retained_changed_loc`: the retained change size used for tie-breaking when metrics are equal
- `last_outcome`: outcome recorded for the most recently completed iteration, such as `kept` or `reverted_worse_metric`
- `iteration_data`: per-iteration working state for the current in-progress iteration

`iteration_data` fields:

- `run_dir`: run directory for the current iteration, such as `runs/0001`
- `plan_title`: short title for the proposed change
- `plan_text`: planner output describing the intended change
- `prompt_text`: prompt sent to the planning provider
- `provider_output`: raw provider output accumulated across planning and implementation
- `result_discussion`: summary text for the run result; this is persisted into the run artifacts during logging
- `planned_files`: files the planner expected to modify
- `changed_files`: files actually changed by the implementation step
- `commit_hash`: commit created for the candidate change
- `parent_commit_hash`: repo `HEAD` before the candidate commit
- `rollback_commit_hash`: revert commit hash when a candidate is rolled back
- `verification_exit_code`: exit code from the verification runner
- `verification_log`: combined verification log text
- `verification_command_names`: verification command names that were executed
- `metric_value`: metric extracted from verification output
- `repair_attempted`: whether an automatic repair flow was attempted
- `notes`: extra notes about failures, skips, or scope violations
- `git_before`: git snapshot captured before the iteration starts
- `git_after`: git snapshot captured after logging the result
- `environment`: environment snapshot for the iteration
- `context_summary`: compact counters from context loading, currently `file_count`, `latest_results_count`, and `active_directions_count`
- `changed_loc`: lines-of-code delta for the candidate commit
- `decision_outcome`: decision recorded for the iteration, such as `kept`, `skipped_no_change`, `reverted_scope_violation`, or `reverted_threshold_failure`

In your current [`demo2/logs/state.json`](/home/niraj/projects/goalseek/demo2/logs/state.json:1), the loop is paused at iteration `1` and the next phase is `READ_CONTEXT`. That means `iteration_data` has not been populated for the next iteration yet, so most of its fields are still `null`, empty lists, empty objects, or `false`.

## Python API

```python
from goalseek.api import init_project, run_setup, run_baseline, run_loop

project_root = init_project("demo", provider="fake", model="fake-model")
run_setup(project_root)
run_baseline(project_root)
run_loop(project_root, iterations=3)
```

## Test

Run the full test suite with `uv`:

```bash
uv run pytest
```

If you are using the local virtualenv created above:

```bash
.venv/bin/python -m pytest -q
```

## Notes

- Generated project verification uses `python3` by default.
- The fake provider is included for local development and integration tests.
- Package code lives under `src/goalseek/`.
- The default scaffold declares `hidden/**` separately from normal read-only scope.
