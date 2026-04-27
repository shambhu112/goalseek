# Step-By-Step Explanation of Baseline and Iteration Runs

This document explains what `goalseek` does when you run a baseline and when you run one or more research iterations.

It follows the real control flow in the codebase, starting from the CLI and ending with the files written into `runs/` and `logs/`.

## High-Level Picture

The normal workflow is:

1. Create a project scaffold.
2. Add or import your project files.
3. Run `goalseek setup` to inspect the project and scope.
4. Run `goalseek baseline` to measure the current project without changing code.
5. Run `goalseek run --iterations N` to let the system plan, implement, verify, and judge candidate changes.

The baseline establishes the first retained metric.
Each later iteration tries one focused change and either:

- keeps it
- reverts it
- skips it

The loop is stateful, so it can pause and resume using `logs/state.json`.

## Important Concepts

Before the detailed flow, it helps to know the core concepts:

- `manifest.yaml` defines file scope, verification commands, and metric extraction.
- `runs/` stores per-run and per-iteration artifacts.
- `logs/results.jsonl` stores one JSON record per completed baseline or iteration.
- `logs/state.json` stores the resumable loop state.
- the project must be a git repository
- the working tree must be clean before the implementation phase starts

## Files and Scope

The manifest splits files into four modes:

- `read_only`: visible to the planner and implementation prompt, but not allowed to change
- `writable`: visible and allowed to change
- `generated`: for run artifacts like `runs/**` and `logs/**`
- `hidden`: not meant to be read or modified by the provider

When the loop evaluates a candidate change, it checks changed files against the manifest:

- writable files are allowed
- generated files are allowed
- anything else is treated as a scope violation and gets reverted

## Entry Points

There are two common commands involved here:

```bash
uv run goalseek baseline ./demo
uv run goalseek run ./demo --iterations 3
```

At the CLI level:

- `goalseek baseline` calls `goalseek.api.run_baseline()`
- `goalseek run` calls `goalseek.api.run_loop()`

The API is intentionally thin. The main logic lives in `LoopEngine`.

## Part 1: What Happens During `goalseek baseline`

Baseline means: run verification on the current project as-is, measure the metric, and store that as the starting point.

No provider is asked to change code during baseline.

### Step 1: The CLI starts the baseline

`src/goalseek/cli/commands/baseline.py` calls `invoke(...)`, which:

- prints a start message
- runs the API function
- renders a user-facing success table if everything succeeds
- converts project-specific exceptions into a nonzero CLI exit

### Step 2: The API hands off to `LoopEngine.run_baseline()`

`goalseek.api.run_baseline()` directly calls:

```python
LoopEngine().run_baseline(project_root, overrides)
```

From here on, the baseline logic is inside `src/goalseek/core/loop_engine.py`.

### Step 3: The project root is discovered

`ProjectService.discover_root()` resolves the incoming path.

It accepts either:

- the project directory itself
- a file inside the project

It walks upward until it finds `manifest.yaml`.

If it cannot find a manifest, it raises an error.

### Step 4: The manifest is loaded and validated

`ManifestService.validate()` does the following:

1. Loads `manifest.yaml`.
2. Validates the structure using the manifest models.
3. Normalizes path patterns.
4. Splits patterns into `read_only`, `writable`, `generated`, and `hidden`.
5. Rejects unsafe or overlapping patterns.
6. Verifies that a metric is declared.

The result is a `ManifestScope` object used throughout the rest of the workflow.

### Step 5: Effective config is loaded

`ProjectService.load_effective_config()` merges configuration in this order:

1. built-in defaults
2. `~/.config/goalseek/config.yaml` if it exists
3. `project_root/config/project.yaml` if it exists
4. any CLI/API overrides

This produces the final provider settings, model names, timeouts, and related execution config.

### Step 6: Package logging is configured

`ProjectService.configure_logging()` sets up runtime logging based on the effective config.

This affects package logs, not the research artifacts written into `runs/`.

### Step 7: Artifact and git helpers are created

The baseline creates:

- `ArtifactStore(root)` for writing run artifacts
- `Repo(root)` for git-related checks

The baseline then verifies that the project is a git repository.

If the project is not a repo, baseline fails with:

`baseline requires a git repository`

### Step 8: The baseline run directory is created

`ArtifactStore.baseline_dir()` ensures this directory exists:

`runs/0000_baseline`

This directory becomes the home for baseline artifacts.

### Step 9: An environment snapshot is captured

`ProjectService.environment_snapshot()` records metadata such as:

- OS name
- platform
- Python version
- project root path
- provider name
- model name
- full effective config
- command versions, such as `git` and the configured provider executable

This snapshot is written later as:

`runs/0000_baseline/env.json`

### Step 10: Verification commands run

`VerificationRunner.run()` executes every verification command listed in the manifest.

For each command it:

1. resolves the command working directory
2. runs the command with a timeout
3. passes these environment variables:
   - `GOALSEEK_RUN_DIR`
   - `GOALSEEK_PROJECT_ROOT`
4. captures stdout, stderr, exit code, duration, and cwd
5. appends a readable combined log

Verification stops on the first failing command.

The combined verifier output is written to:

`runs/0000_baseline/verifier.log`

### Step 11: Metric extraction happens if verification succeeded

If verification returns exit code `0`, the engine extracts the metric using the manifest config.

Supported extraction styles include:

- JSON file extraction
- regex from stdout
- regex from stderr

If extraction succeeds:

- the metric is written to `runs/0000_baseline/metrics.json`
- the value becomes the retained baseline metric

If extraction fails:

- a baseline result record is still written
- the baseline raises an error after logging that failure

### Step 12: A baseline result record is written

Regardless of whether metric extraction succeeded, the baseline writes:

- `runs/0000_baseline/result.json`
- one appended JSON line in `logs/results.jsonl`

The baseline record includes fields like:

- `iteration = 0`
- `mode = "baseline"`
- `outcome = "baseline"`
- provider and model
- verification exit code
- metric value if available
- notes if something failed

### Step 13: Baseline failure handling

If verification failed, the engine builds a user-facing error message that includes:

- the failing exit code
- the path to `verifier.log`
- sometimes the tail of the failing output

In that case:

- artifacts are preserved
- the baseline command exits with an error
- loop state is not initialized as a successful ready-to-run baseline

### Step 14: Loop state is initialized after a successful baseline

If baseline verification and metric extraction succeed, `StateStore.initialize()` writes:

`logs/state.json`

The initialized state contains:

- `status = "ready"`
- `current_iteration = 1`
- `current_phase = "READ_CONTEXT"`
- provider and model
- `retained_metric = <baseline metric>`
- `retained_changed_loc = 0`
- `last_outcome = "baseline"`

This is what makes the project ready for `goalseek run` or `goalseek step`.

### Step 15: The baseline returns a summary payload

The baseline returns a dictionary containing:

- the baseline record
- the extracted metric
- the baseline run directory

The CLI then renders a "Baseline Complete" table.

## Part 2: What Happens During `goalseek run --iterations N`

The run loop advances the project through iteration phases.

Each iteration is designed to produce one focused candidate change, evaluate it mechanically, and decide whether it should remain in git history.

### Step 1: The CLI starts the run

`src/goalseek/cli/commands/run.py`:

- accepts a project path
- optionally accepts `--iterations`
- optionally accepts `--time`
- chooses a start message
- calls the API

If you pass `--iterations 3`, the run aims to complete three full iterations, not just three phases.

### Step 2: The API calls `LoopEngine.run_loop()`

`goalseek.api.run_loop()` passes:

- `iterations`
- `forever`
- optional time limit
- any config overrides

### Step 3: The loop loads or initializes state

`LoopEngine.initialize_or_load_state()` does one of two things:

If `logs/state.json` already exists:

- it loads that state and resumes from wherever the project last paused

If no state exists yet:

- it looks for `logs/results.jsonl`
- if there are no results, it fails with `baseline must be run before the loop`
- if results exist, it reconstructs the retained metric and next iteration number from the history

This is why the loop is resumable even if the process stops between phases.

### Step 4: The loop enters the main while-loop

Inside `run_loop()`:

- state status becomes `RUNNING`
- one phase is executed at a time
- the updated state is immediately saved
- the loop decides whether a full iteration has completed
- it stops when the requested number of full iterations is done, the time limit expires, or the chosen mode says to stop

An iteration counts as complete when the engine has gone all the way back to:

- `current_phase = READ_CONTEXT`
- `iteration_data = {}` equivalent empty payload

That condition means the previous iteration fully finished logging and reset its transient state.

## The Iteration Phases

Each iteration passes through up to seven phases:

1. `READ_CONTEXT`
2. `PLAN`
3. `APPLY_CHANGE`
4. `COMMIT`
5. `VERIFY`
6. `DECIDE`
7. `LOG`

### Phase 1: `READ_CONTEXT`

Goal: gather the visible project context and prepare the run directory for this iteration.

#### What happens

The engine creates the iteration directory:

`runs/0001`, `runs/0002`, and so on.

Then `ContextReader.read()` gathers:

- all existing visible files from read-only and writable scope
- the last five entries from `logs/results.jsonl`
- active directions from `logs/directions.jsonl`
- recent git log
- git status and diff summary

Important detail:

- hidden files are not included in the visible file list
- generated files are not included in the visible file list
- only `read_only` and `writable` patterns are expanded into context files

The engine writes:

- `runs/<iteration>/git_before.txt`
- `runs/<iteration>/env.json`

It also fills `state.iteration_data` with:

- `run_dir`
- `git_before`
- `environment`
- a compact `context_summary`

Important nuance:

- the full context gathered here is not persisted into `state.iteration_data`
- only summary counts are stored there
- the full context is read again during `PLAN` when the planning prompt is built

Then it advances to:

`PLAN`

### Phase 2: `PLAN`

Goal: ask the planning provider to propose exactly one focused change.

#### What happens

The engine:

1. picks the hypothesis provider from config
2. looks at recent results
3. counts the streak of non-kept outcomes
4. builds the planning prompt

The planning prompt includes:

- readable scope
- writable scope
- generated scope
- hidden scope
- recent results
- active directions
- a note encouraging either a small change or, after repeated misses, a more radical one

The provider is asked to produce:

- `Plan`
- `Reasoning`
- `Expected Impact`

It is also asked to name intended files to modify.

#### Files written during planning

The engine writes:

- `runs/<iteration>/prompt.md`
- `runs/<iteration>/provider_output.md`

If planning succeeds, it also writes:

- `runs/<iteration>/plan.md`

#### State updates on success

The engine stores:

- the prompt text
- raw provider output
- full plan text
- plan title
- reasoning text
- planned files

Then it advances to:

`APPLY_CHANGE`

#### If planning fails

If the provider exits nonzero:

- `notes` is set
- `decision_outcome = "skipped_provider_failure"`
- the engine skips straight to `LOG`

### Phase 3: `APPLY_CHANGE`

Goal: ask the implementation provider to apply the approved plan.

#### First gate: the working tree must be clean

Before the implementation provider runs, the engine calls:

`repo.ensure_clean()`

If git status is not clean, the phase fails immediately with:

`working tree must be clean before applying a change`

This protects the experiment loop from mixing pre-existing edits with provider-made edits.

#### Implementation prompt contents

The implementation prompt includes:

- writable paths
- generated paths
- hidden paths
- strict constraints about what can be changed
- the plan markdown generated during `PLAN`

#### What happens next

The implementation provider runs and is expected to modify files in the working tree.

The engine appends its raw output to the previously stored planning output.

#### Branch A: provider implementation failure

If the provider exits nonzero:

- `notes` is set
- `decision_outcome = "skipped_provider_failure"`
- the engine jumps to `LOG`

#### Branch B: no file changes

If the provider exits successfully but git shows no changed files:

- `changed_files = []`
- `decision_outcome = "skipped_no_change"`
- the engine jumps to `LOG`

#### Branch C: out-of-scope file changes

If changed files include anything outside:

- writable scope
- generated scope

then the engine:

1. commits all changed files with message `experiment: scope violation`
2. immediately reverts that commit
3. records the original commit hash and rollback commit hash
4. stores a note listing the violating files
5. sets `decision_outcome = "reverted_scope_violation"`
6. jumps to `LOG`

This design preserves a trace of what happened while still undoing the invalid candidate.

#### Branch D: valid changes

If changed files are within allowed scope:

- `changed_files` is recorded
- the engine advances to `COMMIT`

### Phase 4: `COMMIT`

Goal: turn the valid working tree diff into a candidate git commit.

#### What happens

The engine records the parent commit hash first.

Then it commits the changed files with a message like:

`experiment: <plan title>`

After commit, it stores:

- `pending_commit`
- `commit_hash`
- `parent_commit_hash`
- `changed_loc`

`changed_loc` is computed by summing added and deleted lines from `git show --numstat`.

Then the engine advances to:

`VERIFY`

### Phase 5: `VERIFY`

Goal: measure the candidate change mechanically.

#### What happens

The verification commands from the manifest run again, just like in baseline, but now against the candidate commit.

The engine writes:

- `runs/<iteration>/verifier.log`

and records in state:

- verification log
- verification exit code
- verification command names

#### If verification fails

If any verification command exits nonzero:

- `decision_outcome = "skipped_verification_crash"`
- the engine jumps to `LOG`

Important detail:

At this point the candidate commit still exists in git history.
The current code treats this as a skipped iteration, not an automatic revert.

#### If verification succeeds

The engine extracts the metric and stores:

- `metric_value`

Then it advances to:

`DECIDE`

### Phase 6: `DECIDE`

Goal: compare the candidate metric to the retained metric and decide whether to keep or revert the candidate.

#### Step 6.1: Threshold check

First the engine applies `min_pass` and `max_pass` thresholds from the manifest.

If thresholds fail:

- the candidate commit is reverted
- `rollback_commit_hash` is stored
- `decision_outcome = "reverted_threshold_failure"`
- the engine advances to `LOG`

#### Step 6.2: First retained candidate case

If there is no retained metric yet:

- the candidate metric becomes the retained metric
- retained changed LOC is updated
- `decision_outcome = "kept"`

This case is uncommon after a successful baseline, because the baseline usually provides the first retained metric already.

#### Step 6.3: Compare with retained metric

If a retained metric exists, `compare(...)` uses:

- current metric
- retained metric
- metric direction (`maximize` or `minimize`)
- epsilon tolerance

Possible comparison outcomes are:

- `better`
- `equal`
- `worse`

#### Step 6.4: Tie-breaker

If the metric is equal within epsilon, the code uses the tie-breaker:

- smaller `changed_loc` wins

If the candidate has a smaller change size than the retained winner:

- the candidate is kept

Otherwise:

- the candidate is reverted
- `decision_outcome = "reverted_worse_metric"`

#### Result of the decision phase

After the comparison, the engine always advances to:

`LOG`

### Phase 7: `LOG`

Goal: persist a durable summary of what happened in the iteration.

#### What happens

The engine selects the git revision to snapshot:

- rollback commit if there was one
- otherwise the candidate commit
- otherwise `HEAD`

It writes:

- `runs/<iteration>/git_after.txt`
- `runs/<iteration>/provider_output.md` if provider output exists
- `runs/<iteration>/experiment.py` as a snapshot of the iteration's experiment file
- `runs/<iteration>/results_discussion.md`
- `runs/<iteration>/metrics.json` if a metric exists
- `runs/<iteration>/result.json`

It also appends the iteration record to:

`logs/results.jsonl`

The result discussion is a short markdown summary containing:

- outcome
- metric
- notes

#### State reset at the end of logging

After the record is written:

- `last_outcome` is updated
- `pending_commit` is cleared
- `rollback_state` becomes `needed` or `not_needed`
- `current_iteration` increments
- `current_phase` resets to `READ_CONTEXT`
- `iteration_data` resets to an empty payload
- `status` becomes `PAUSED`

That reset is what marks an iteration as complete.

## What Gets Written Where

### Baseline artifacts

In `runs/0000_baseline/` you should expect:

- `env.json`
- `verifier.log`
- `metrics.json` if extraction succeeded
- `result.json`

In `logs/` you should expect:

- `results.jsonl`
- `state.json` after a successful baseline

### Iteration artifacts

For a typical iteration directory like `runs/0002/`, you may see:

- `env.json`
- `git_before.txt`
- `prompt.md`
- `plan.md`
- `experiment.py`
- `provider_output.md`
- `verifier.log`
- `metrics.json`
- `git_after.txt`
- `results_discussion.md`
- `result.json`

In `logs/`, the loop updates:

- `results.jsonl`
- `state.json`
- `directions.jsonl` if you added user directions

## Common Outcomes and What They Mean

Here are the main iteration outcomes:

- `kept`: the candidate met thresholds and beat the retained result, or tied with fewer changed lines
- `reverted_worse_metric`: the candidate was valid but did not beat the retained result
- `reverted_threshold_failure`: the candidate violated metric thresholds
- `reverted_scope_violation`: the provider changed out-of-scope files
- `skipped_no_change`: the provider made no code changes
- `skipped_provider_failure`: planning or implementation provider failed
- `skipped_verification_crash`: verification command failed before a usable metric was produced

## Why Git Is Central

Git is used for several separate jobs:

- making sure baseline starts from a versioned project
- enforcing a clean working tree before implementation
- capturing recent history for context
- turning each valid candidate into a commit
- reverting losing or invalid candidates
- measuring change size for tie-breaking
- snapshotting `git_before` and `git_after`

The loop is not just "edit files and hope for the best".
It is "edit, commit, verify, compare, and either keep or revert".

## Mental Model for the Whole System

A good way to think about the system is:

1. Baseline measures the current project and stores the first retained score.
2. Each iteration reads context and proposes one focused experiment.
3. The provider applies that experiment to the working tree.
4. The system commits the candidate.
5. The verifier measures the candidate.
6. The decision logic compares it to the retained winner.
7. The system keeps the candidate or reverts it.
8. Everything is logged so the next iteration has history.

That cycle repeats until you stop the run or the requested number of iterations completes.

## Short Practical Summary

If everything goes well:

- `goalseek baseline` creates `runs/0000_baseline`, measures the starting metric, and initializes `logs/state.json`
- `goalseek run --iterations 3` performs three full experiment cycles
- each cycle produces one directory in `runs/`
- each cycle appends one record to `logs/results.jsonl`
- the project git history ends up containing only the kept changes plus any revert commits created for rejected candidates

If you want to inspect a specific iteration in detail, the best places to look are:

- `runs/<iteration>/prompt.md`
- `runs/<iteration>/provider_output.md`
- `runs/<iteration>/verifier.log`
- `runs/<iteration>/result.json`
- `logs/results.jsonl`
