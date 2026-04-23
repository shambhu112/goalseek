# goalseek - Agent-Ready Implementation Specification


Version: 1.0  
Date: April 12, 2026  
Audience: Codex, Claude Code, or another coding agent implementing the package.


This document converts the product requirements into an implementation specification. It is intentionally concrete, prescriptive, and optimized for agentic coding workflows.
---


## 1. Objective

Build a Python package named `goalseek` that manages isolated research projects, runs a disciplined experiment loop, integrates external coding-agent providers, verifies each change mechanically, and keeps only changes that improve the declared metric.
The MVP is local-only and CLI-first.

The package must:
- scaffold and manage project workspaces;
- validate a machine-readable manifest;
- run a setup phase that reads all in-scope context before any write;
- run a baseline iteration;
- execute a repeatable plan -> change -> commit -> verify -> keep-or-revert loop;Note : Plan and change are executed by the coding agent, not by the user. The user only provides the initial prompt and the coding agent generates the plan and change.
- store structured local artifacts for every iteration;
- expose equivalent core controls via a Python API.
---


## 2. Non-negotiable rules

These rules are product invariants. Do not weaken them in implementation.
1. A project is the top-level execution and audit boundary.
2. Read before write: all manifest-scoped files must be read before the system attempts any modification.
3. One focused change per iteration.
4. Keep-or-revert decisions must use only objective, mechanical verification.
5. Failed or worse attempts must be reverted with `git revert`, not destructive reset.
6. When metric outcomes are equal, prefer the mechanically simpler implementation.
7. Git history is part of the product memory.
8. When progress stalls, the system must broaden search rather than repeating the same move.
---

## 3. MVP scope
### In scope
- Python 3.11+
- local filesystem project isolation
- local subprocess execution
- git-backed experiment history
- CLI implemented with Click and Rich
- provider configuration for Claude Code, Codex, Opencode, and Gemini
- append-only iteration logs and project-local artifacts
- step mode and run mode
- Python API for project init, setup, baseline, run, step, status, summary, and direction updates


### Out of scope for MVP
- remote compute targets
- GPU/cloud sandbox execution
- GUI or web UI
- distributed execution
- human-judged scoring
- destructive history rewriting
- auto-merging or auto-pushing to remotes
Out-of-scope items may have extension points but must not be implemented beyond basic placeholders.
---

## 4. Implementation decisions for the MVP

These choices resolve ambiguity from the requirements and should be treated as part of the build spec.
1. Use a `src/` package layout for the library implementation.
2. Use `pyproject.toml` for package metadata and dependencies. And, use uv for package management and python execution.
3. Use `PyYAML` for YAML parsing.
4. Use `pydantic` v2 models for manifest and config validation.
5. Use the system `git` CLI through subprocess calls, not GitPython.
6. Use JSON and JSONL for machine-readable records.
7. Ignore run artifacts in git by default so rollbacks preserve local experiment artifacts.
8. Treat provider integrations as wrappers around external CLIs or executables in the MVP.
9. Use a persistent loop state file so `goalseek step` and `goalseek run` can pause and resume deterministically.
10. Add a fake provider adapter used only by tests and local development fixtures.
---

## 5. Repository layout to implement

Implement the package repository like this:

```text
.
  pyproject.toml
  README.md
  src/
    goalseek/
      __init__.py
      cli/
        app.py
        common.py
        commands/
          project.py
          manifest.py
          setup.py
          baseline.py
          run.py
          step.py
          direct.py
          status.py
          summary.py
      core/
        project_service.py
        manifest_service.py
        setup_phase.py
        loop_engine.py
        step_engine.py
        direction_service.py
        state_store.py
        summary_service.py
        context_reader.py
        artifact_store.py
      providers/
        base.py
        registry.py
        codex.py
        claude_code.py
        opencode.py
        gemini.py
        prompts.py
        fake.py
      gitops/
        repo.py
        rollback.py
      verification/
        runner.py
        metrics.py
      models/
        manifest.py
        config.py
        results.py
        state.py
        project.py
      utils/
        paths.py
        hashing.py
        subprocess.py
        json.py
      templates/
        manifest.yaml.j2
        program.md.j2
        workflow_setup.py.j2
        experiment.py.j2
        project_config.yaml.j2
        gitignore.j2
      api.py
  tests/
    unit/
    integration/
    fixtures/
```


Notes:
- `src/goalseek/api.py` is the public Python API entry point.
- Templates generate the user project scaffold, not package internals.
- Test fixtures must include at least one toy project and one fake provider scenario.
- The project folder for research will be a different folder outside of this project structure
---

## 6. Generated project scaffold


`goalseek project init <name>` must create this project layout:


```text
<project_name>/
  .git/
  .gitignore
  manifest.yaml
  program.md
  setup.py
  experiment.py
  knowledge/
  context/
  hidden/
  config/
    project.yaml
  runs/
    .gitkeep
  logs/
    .gitkeep
```

### Scaffold rules
- The scaffold must initialize git if the target directory is not already a repository.
- `setup.py` here is a workflow script for the research project. It is not package metadata.
-  program.md is the research plan that the coding agent will execute and update post each iteration. the hypothesis coding agent will update this file to reflect the current hypothesis and the reasoning behind it.
- `experiment.py` is the default writable file that the coding agent will update based on the hypothesis and the research plan in program.md. The implementation coding agent will update this file to reflect the current implementation and the reasoning behind it.
- `runs/` and `logs/` must be git-ignored by default.
- `knowledge/`, and `context/`, and `hidden/` may be empty at creation time.
- `hidden/` is a directory that is not visible to the coding agent.It is used to store sensitive information such as API keys and passwords.It is also used to ground truth that should is used only at the time of verification of results else the agent can game the system. it should have a file like `validate_results.py` which will be used to verify the results of the experiment. Note manifest file points to the validation file

### Default `.gitignore`
Ignore at minimum:

```text
runs/
logs/
__pycache__/
*.pyc
.venv/
```
---

## 7. Data contracts
### 7.1 Manifest schema
The manifest is required and lives at `<project_root>/manifest.yaml`.

Use this shape:


```yaml
version: 1
project:
  name: goalseek_demo
  description: Short description of the research target.

files:
  - path: manifest.yaml
    mode: read_only
  - path: program.md
    mode: read_only
  - path: setup.py
    mode: read_only
  - path: experiment.py
    mode: writable
  - path: knowledge/**
    mode: read_only
  - path: context/**
    mode: read_only
  - path: hidden/**
    mode: read_only
  - path: config/**
    mode: read_only
  - path: runs/**
    mode: generated
  - path: logs/**
    mode: generated


verification:
  commands:
    - name: evaluate
      run: python validate_results.py --evaluate --output runs/latest/results.json
      cwd: .
      timeout_sec: 1800


provider:
  mode: hypothesis
    name: codex
    model: gpt-5-codex
    non_interactive: true
  model: implementation
    name: codex
    model: gpt-5-codex
    non_interactive: true


execution:
  target: local
```


### 7.2 Manifest validation rules


Validation must fail if any of the following is true:


- manifest file is missing;
- schema version is missing or unsupported;
- no `files` entries are defined;
- a file entry is missing `path` or `mode`;
- `mode` inside `files` is not one of `read_only`, `writable`, `generated`;
- no verification command is defined;
- any path escapes project root;
- any writable path overlaps a read-only path;
- any generated path is also declared writable or read-only.


### 7.3 Config model and precedence

Support three config layers:

1. global config: `~/.config/goalseek/config.yaml`
2. project config: `<project_root>/config/project.yaml`
3. CLI overrides


Precedence is lowest to highest in that order.
Project config may override provider defaults, model, timeouts, loop behavior, and output formatting, but may not redefine manifest file scope. Scope lives in the manifest only.


### 7.4 Direction record format

Store operator directions append-only in `logs/directions.jsonl`.

Each record:

```json
{
  "timestamp": "2026-04-12T12:00:00Z",
  "message": "Try reducing complexity in experiment.py before changing other files.",
  "source": "cli",
  "applies_from_iteration": 3
}
```


Do not mutate protected source files when direction changes.


### 7.5 Loop state format


Store resumable loop state in `logs/state.json`.


Example:


```json
{
  "status": "paused",
  "current_iteration": 2,
  "current_phase": "VERIFY",
  "provider": "codex",
  "model": "gpt-5-codex",
  "pending_commit": "abc1234",
  "rollback_state": "not_needed"
}
```


### 7.6 Result record format


Append one JSON object per iteration to `logs/results.jsonl`.


Example:


```json
{
  "timestamp": "2026-04-12T12:05:00Z",
  "iteration": 2,
  "run_dir": "runs/0002",
  "commit_hash": "abc1234",
  "parent_commit_hash": "def5678",
  "provider": "codex",
  "model": "gpt-5-codex",
  "mode": "implementation",
  "planned_files": ["experiment.py"],
  "changed_files": ["experiment.py"],
  "outcome": "kept",
  "verification_exit_code": 0,
  "verification_command_names": ["evaluate"],
  "repair_attempted": false,
  "rollback_commit_hash": null,
  "notes": "Single-file improvement retained."
  "result_discussion": "results_discussion.md"
}
```


Allowed outcomes:


- `baseline`
- `kept`
- `reverted_worse_metric`
- `reverted_threshold_failure`
- `reverted_scope_violation`
- `skipped_provider_failure`
- `skipped_verification_crash`
- `skipped_no_change`


### 7.7 Environment snapshot format


Each run directory must contain `env.json` with:


- OS name
- platform string
- Python version
- current working directory
- provider name
- model name
- effective configuration snapshot
- command versions when available for `git` and the selected provider


Do not log secrets or full environment variable values.


---


## 8. Artifact layout per run


Use zero-padded run directories.


- baseline: `runs/0000_baseline/`
- iterations: `runs/0001/`, `runs/0002/`, etc.


Each iteration directory must contain:


```text
runs/000N/
  plan.md
  prompt.md
  provider_output.md
  results_discussion.md
  verifier.log
  metrics.json
  result.json
  env.json
  git_before.txt
  git_after.txt
```


### Artifact semantics


- `plan.md`: the chosen single-change plan for the iteration
- `prompt.md`: exact prompt or instruction payload sent to the provider
- `provider_output.md`: captured provider response or summarized response when raw transcript is unavailable
- `results_discussion.md`: discussion of the results of the iteration. Used in the next loop iteration to create hypothesis.
- `verifier.log`: streamed verification stdout and stderr
- `metrics.json`: normalized metric output used for decision making
- `result.json`: structured copy of the result record for that run
- `git_before.txt`: git log and diff context captured before change
- `git_after.txt`: git show and working tree summary after verification and any revert


The baseline directory may omit `plan.md` and `provider_output.md`, but it must still have `verifier.log`, `metrics.json`, `result.json`, and `env.json`.


---


## 9. Public Python API


Implement a public API in `src/goalseek/api.py`.


Minimum functions:


```python
def init_project(name: str, path: str | None = None, **overrides) -> str: ...
def validate_manifest(project_root: str) -> None: ...
def run_setup(project_root: str, **overrides) -> dict: ...
def run_baseline(project_root: str, **overrides) -> dict: ...
def run_loop(project_root: str, iterations: int | None = None, forever: bool = False, **overrides) -> dict: ...
def run_step(project_root: str, **overrides) -> dict: ...
def add_direction(project_root: str, message: str, applies_from_iteration: int | None = None) -> dict: ...
def get_status(project_root: str) -> dict: ...
def build_summary(project_root: str) -> dict: ...
```


Rules:


- CLI commands must call the same service layer used by the Python API.
- Do not duplicate business logic inside CLI command handlers.


---


## 10. CLI contract


Implement a root command `gs` with subcommands below.


### 10.1 `goalseek project init <name>`


Behavior:


- create scaffold
- render template files
- initialize git if needed
- optionally create initial commit `project: initialize scaffold`
- print created paths and next steps


Options:


- `--path PATH`
- `--provider {codex,claude_code,opencode,gemini}`
- `--model TEXT`
- `--no-git-init`


### 10.2 `goalseek manifest validate <project>`


Behavior:


- load manifest
- validate schema and path rules
- print success or human-readable validation errors
- exit non-zero on failure


### 10.3 `goalseek setup <project>`


Behavior:


- resolve effective config
- read all manifest-scoped files
- build context inventory
- validate provider capability
- print summary of writable files, read-only files, generated paths, provider, model, verification commands, metric definition, and execution target
- persist setup snapshot under `logs/`


### 10.4 `goalseek baseline <project>`


Behavior:

- require valid manifest
- run verification against current project state
- extract metric
- write baseline artifacts to `runs/0000_baseline/`
- append a baseline record to `logs/results.jsonl`
- initialize loop state as ready for iteration 1 in phase `READ_CONTEXT`


### 10.5 `goalseek run <project> --iterations N`

Behavior:
- run the loop for exactly `N` completed iterations after baseline
- after each iteration, persist state and allow checkpoint callbacks internally
- print live progress with Rich
- emit summary when complete

### 10.6 `goalseek run <project> --time mins`

Behavior:
- run until interrupted or when minutes are over
- on interrupt, persist state cleanly and print latest status


### 10.7 `goalseek step <project>`

Behavior:
- advance exactly one loop phase from persisted state
- phases are:
  - `READ_CONTEXT`
  - `PLAN`
  - `APPLY_CHANGE`
  - `COMMIT`
  - `VERIFY`
  - `DECIDE`
  - `LOG`
- after executing one phase, persist state and stop
- if no state exists, initialize the next pending iteration and begin with `READ_CONTEXT`


### 10.8 `goalseek direct <project> --message "..."`

Behavior:
- append a new direction record to `logs/directions.jsonl`
- do not modify protected files
- default `applies_from_iteration` is next iteration

### 10.9 `goalseek status <project>`
Behavior:
- read `logs/state.json` and `logs/results.jsonl`
- print current iteration, current phase, active provider/model, latest metric, pending commit, rollback state, and latest outcome


### 10.10 `goalseek summary <project>`
Behavior:
- summarize all recorded results
- print best retained metric, kept iterations, reverted attempts, skipped attempts, and recommendations


### 10.11 Exit codes


Use these exit codes consistently:


- `0`: success
- `2`: validation/config error
- `3`: git error
- `4`: provider execution error
- `5`: verification error
- `130`: interrupted by user


---


## 11. Core services and responsibilities


### 11.1 `ProjectService`


Responsibilities:


- discover project root
- create scaffold
- load project paths
- ensure required directories exist
- enforce project-root write confinement


### 11.2 `ManifestService`


Responsibilities:
- load manifest YAML
- validate schema
- expand and normalize relative paths/globs
- determine read-only, writable, and generated path sets
- reject overlaps and root escapes


### 11.3 `ContextReader`
Responsibilities:
- read all manifest-scoped files before writes
- produce a context bundle containing file contents, hashes, and metadata
- capture recent git log and working tree diff
- capture latest results and direction records


### 11.4 `SetupPhase`
Responsibilities:
- resolve config precedence
- validate provider capability against requested mode
- render a summary object for CLI display
- persist setup snapshot


### 11.5 `LoopEngine`
Responsibilities:
- coordinate iteration lifecycle
- call hypothesis planning prompt (program.md)
- call implementation python class (experiment.py)
- commit changes
- run verification
- compare metric to current retained state
- keep or revert
- write artifacts and result record


### 11.6 `StepEngine`

Responsibilities:
- persist phase-level state transitions
- support `goalseek step`, pause, resume, and run-loop checkpoints


### 11.7 `DirectionService`

Responsibilities:
- append and read direction notes
- resolve active directions for a given iteration


### 11.8 `ArtifactStore`

Responsibilities:
- create per-run directories
- write structured and human-readable artifacts atomically
- preserve append-only logs


### 11.9 `Repo`


Responsibilities:
- wrap git CLI operations
- init repository
- verify clean working tree where required
- create commits
- create revert commits
- produce logs and diffs for artifacts


### 11.10 `VerificationRunner`


Responsibilities:


- run verification commands with live streaming
- capture stdout, stderr, exit code, duration
- normalize metric extraction input


### 11.11 `Metrics`


Responsibilities:


- extract declared primary metric
- compare previous and current values based on metric direction and epsilon
- evaluate thresholds and tie-breakers


### 11.12 `SummaryService`


Responsibilities:


- compute best retained result
- aggregate keep, revert, and skip counts
- identify stagnation patterns and near-misses


---


## 12. Provider abstraction


### 12.1 Provider interface


Define a common provider interface in `providers/base.py`.


Suggested shape:


```python
class ProviderAdapter(Protocol):
    name: str


    def capabilities(self) -> dict: ...


    def plan(self, request: ProviderRequest) -> ProviderResponse: ...


    def implement(self, request: ProviderRequest) -> ProviderResponse: ...
```


`ProviderRequest` must contain at least:


- project root
- provider name
- model name
- mode (`hypothesis` or `implementation`)
- prompt text
- writable paths
- generated paths
- non-interactive flag
- timeout


`ProviderResponse` must contain at least:


- raw_text
- exit_code
- duration_sec
- changed_files if detectable
- error if any


### 12.2 Provider capability rules


Each provider adapter must declare:


- whether non-interactive execution is supported
- whether separate plan and implementation prompts are supported
- executable/binary lookup strategy


If requested config cannot be satisfied, setup must fail fast.


### 12.3 MVP provider execution model


For the MVP, adapters should shell out to local provider CLIs or binaries.


Do not integrate remote APIs directly unless required as a fallback for one provider and the implementation still preserves the same abstraction boundary.


### 12.4 Fake provider


Implement a fake provider that:


- returns scripted plan text
- applies deterministic file edits from fixture files
- simulates success, no-op, and failure scenarios


This provider is required for integration tests.


---


## 13. Prompt contracts for coding agents
- program.md is the master prompt. 
- Store reusable prompt templates in `providers/prompts.py`.


### 13.1 Planning prompt requirements
The planning prompt must (Program.md) instruct the provider to:
- read the supplied context with links to other documents in program.md; program.md will have {{$prompt_file}} for linking to various files . All prompt_files will be in context\ folder
- propose exactly one focused change;
- name the intended files to modify; typically iteration_{{num}}_plan.md
- run Coding agent against the plan file iteration_{{num}}_plan.md. This should update `experiment.py` and add new files as needed by the coding agent
- explain why this change should improve the metric;
- avoid editing files outside writable scope; New files outside of the ones mentoned in manifest can be created as need be by coding agent
- output a plan in Markdown. Typically iteration_{{num}}_plan.md

The loop must write the planning output into `iteration_{{num}}_plan.md` . This should include three sections; one for Plan, second for Resoning and third for expected impact

### 13.2 Implementation prompt requirements


The implementation prompt must instruct the provider to:


- implement only the approved plan;
- modify only writable files;
- create files only inside generated paths;
- keep changes minimal and coherent;
- avoid broad refactors unless explicitly justified by the plan;
- stop after the code change is complete.


### 13.3 Scope enforcement


After provider execution, the system must verify that changed files are within writable scope. Any out-of-scope source change is a scope violation and the iteration must be reverted or skipped.


---


## 14. Verification subsystem


### 14.1 Verification commands


The manifest may declare one or more verification commands.


For each command support:


- `name`
- `run`
- `cwd`
- `timeout_sec`


The runner executes commands in order.


### 14.2 Streaming behavior


During verification:


- stream stdout and stderr live to the CLI;
- simultaneously write a combined log to `verifier.log`;
- capture exit code and duration.


### 14.3 Metric extraction methods


Support these extraction types in the MVP:


1. `json_file`
   - read a JSON file and extract by JSON Pointer
2. `stdout_regex`
   - parse stdout with a regex containing one numeric capture group
3. `stderr_regex`
   - parse stderr with a regex containing one numeric capture group


If extraction fails, treat verification as failed.


### 14.4 Threshold evaluation


Support optional threshold checks:


- `min_pass`
- `max_pass`


If thresholds fail, the iteration outcome is `reverted_threshold_failure` even if the primary metric appears improved.


### 14.5 Tie-breaker for equal metrics


When metric delta is equal within epsilon:


- compute changed LOC over tracked source files changed in the iteration;
- if tie-breaker is `changed_loc` and lower is better, keep only if LOC decreases or remains strictly smaller than the current retained state;
- otherwise revert.


This is the mechanical implementation of "simplicity wins" for the MVP.


---


## 15. Git behavior


### 15.1 Repository preconditions


Before baseline or loop execution:


- project must be inside a git repository;
- if not initialized and user did not disable git init, initialize it;
- fail if git is unavailable.


### 15.2 Cleanliness policy


Before `APPLY_CHANGE`, the working tree must be clean except for ignored generated artifacts.


If non-generated tracked files are already dirty, abort with a clear error.


### 15.3 Commit policy


Before verification, create a normal git commit with subject:


```text
experiment: <short description>
```


The description should be derived from the plan title or first heading.


### 15.4 Rollback policy


If verification worsens the metric, fails thresholds, or detects scope violations:


- create a revert commit using `git revert --no-edit <experiment_commit>`;
- record both experiment and revert hashes in result artifacts;
- do not reset, amend, or squash.


### 15.5 Visibility of failed ideas


Failed experiments must remain visible in git history as the original `experiment:` commit followed by a revert commit.


---


## 16. Setup flow behavior


`goalseek setup` must perform these steps in order:


1. locate project root
2. load manifest
3. validate manifest
4. resolve config precedence
5. read all manifest-scoped files and compute hashes
6. resolve provider adapter and validate capabilities
7. inspect git state
8. render setup summary
9. write setup snapshot under `logs/setup_snapshot.json`


The setup summary must display at least:


- project name
- primary metric and direction
- verification commands
- provider and model
- writable files
- read-only files
- generated paths
- non-interactive mode state
- execution target


If the manifest lacks a mechanical metric, setup must fail and loop start must be blocked.


---


## 17. Baseline flow behavior


`goalseek baseline` must perform these steps:


1. require successful manifest validation
2. create `runs/0000_baseline/`
3. snapshot environment
4. run verification commands
5. extract primary metric
6. write `metrics.json`, `verifier.log`, `result.json`, and `env.json`
7. append a `baseline` record to `logs/results.jsonl`
8. initialize `logs/state.json` for iteration 1 in phase `READ_CONTEXT`


The baseline does not modify source files.


---


## 18. Iteration loop behavior


Each full iteration must follow this exact sequence:


1. `READ_CONTEXT`
   - read manifest-scoped files
   - read current source state
   - read recent results
   - read direction records relevant to this iteration
   - capture `git log -n 20` and current diff summary
   - write `git_before.txt`


2. `PLAN`
   - invoke provider in hypothesis/planning mode
   - require output naming one focused change and intended files
   - persist `plan.md` and `prompt.md`


3. `APPLY_CHANGE`
   - invoke provider in implementation mode using the approved plan
   - enforce writable scope
   - detect changed files
   - if no source changes occurred, mark `skipped_no_change`


4. `COMMIT`
   - stage non-generated changed source files only
   - create `experiment:` commit
   - record commit hash


5. `VERIFY`
   - run mechanical verification
   - capture log, exit code, duration, and extracted metric


6. `DECIDE`
   - compare metric to current retained state
   - evaluate thresholds
   - apply tie-breaker if metric is equal within epsilon
   - keep or revert


7. `LOG`
   - write `metrics.json`, `result.json`, `git_after.txt`, `provider_output.md`, `env.json`
   - append record to `logs/results.jsonl`
   - update `logs/state.json` to next iteration


### 18.1 Decision rules


Assume the retained state before the iteration is the comparison baseline.


For a metric with direction `maximize`:


- better if `current > previous + epsilon`
- equal if `abs(current - previous) <= epsilon`
- worse otherwise


For `minimize`, reverse the comparison.


Decision table:


- better + thresholds pass -> keep
- equal + tie-breaker says simpler -> keep
- equal + tie-breaker not simpler -> revert
- worse -> revert
- verification crash -> attempt one repair or skip, then log failure
- scope violation -> revert or skip and log failure


### 18.2 Limited repair behavior


If verification crashes due to an implementation error:


- allow at most one repair attempt within the same iteration;
- the repair attempt must still stay within writable scope;
- if repair fails, revert or skip and log `skipped_verification_crash`.


### 18.3 Stagnation detection


A stagnation event occurs when there are at least 3 consecutive non-kept iterations.


When stagnation is detected, the next planning prompt must include:


- recent failed hypotheses
- near-miss metrics
- instruction to consider a more radical but still single-idea change


Record stagnation status in the iteration reasoning artifact.


---


## 19. Step mode and checkpoints


Step mode is phase-based, not iteration-based.


### Requirements


- `goalseek step` executes exactly one phase and stops.
- `goalseek run` may internally use the same step engine to advance through phases.
- after every phase, persist state to `logs/state.json`.
- operator direction can be injected between phases using `goalseek direct`.


This is the mechanism that satisfies hand-held operation.


---


## 20. Status and summary behavior


### 20.1 Status


`goalseek status` must report:


- project root
- current iteration
- current phase
- provider and model
- latest retained metric
- pending commit hash, if any
- rollback state
- most recent outcome


### 20.2 Summary


`goalseek summary` must compute:


- baseline metric
- best retained metric and iteration
- number of kept iterations
- number of reverted iterations
- number of skipped iterations
- latest active direction
- stagnation indicators
- recommendations for next moves


Recommendations may be heuristic, but they must be derived only from recorded results and recent directions.


---


## 21. Write confinement and path safety


Enforce these safety rules everywhere:


- all writes must stay inside the project root;
- generated files may only be created under declared generated paths;
- source edits may only occur under declared writable paths;
- symlink traversal that escapes the project root must be rejected;
- normalized real paths must be used for confinement checks.


---


## 22. Error handling requirements


The system must fail predictably and visibly.


### Required error classes


Implement typed exceptions for at least:


- `ManifestValidationError`
- `ConfigError`
- `ProjectStateError`
- `ProviderExecutionError`
- `VerificationError`
- `MetricExtractionError`
- `GitOperationError`
- `ScopeViolationError`


### Error behavior


- CLI must render concise human-readable errors.
- machine-readable artifacts should still be written when enough context exists.
- never leave loop state ambiguous; update `logs/state.json` on failure paths where possible.


---


## 23. Logging requirements


### Human-readable


Use Markdown for:


- plans
- reasoning
- provider output capture
- summary report


### Machine-readable


Use JSON or JSONL for:


- setup snapshot
- state
- results
- metrics
- environment snapshots


### Append-only rule


`logs/results.jsonl` and `logs/directions.jsonl` must be append-only. Do not rewrite earlier records.


---


## 24. Testing requirements


Implement the following test categories.


### 24.1 Unit tests


At minimum cover:


- manifest parsing and validation
- path expansion and overlap detection
- config precedence
- metric comparison for maximize and minimize
- threshold evaluation
- tie-breaker logic
- state transitions in step mode
- write confinement checks
- git wrapper command construction


### 24.2 Integration tests


At minimum cover:


1. project scaffold creation
2. baseline creation on a toy project
3. three-iteration run with fake provider
4. revert on worse metric
5. skip on no-op iteration
6. step mode pause and resume
7. direction injection between phases
8. summary generation after mixed outcomes


### 24.3 Fixtures


Provide:


- a toy project whose metric is easy to improve or worsen deterministically;
- a fake provider script that can apply scripted edits;
- fixture data for better, worse, equal-but-simpler, equal-but-not-simpler, and crash scenarios.


### 24.4 Test command


The repository must support a single command that runs the test suite, for example:


```bash
pytest
```


---


## 25. Implementation order for the coding agent


Implement in this order.


### Phase 1: project and manifest foundations


- package skeleton
- scaffold templates
- project service
- manifest models and validation
- config loading
- basic CLI wiring


### Phase 2: verification and git foundations


- git wrapper
- verification runner
- metric extraction and comparison
- baseline command


### Phase 3: loop engine


- context reader
- provider base and fake provider
- loop state model
- iteration artifacts
- keep/revert decision logic


### Phase 4: interactive control


- step engine
- direction service
- status command
- summary service


### Phase 5: real provider adapters


- codex adapter
- claude_code adapter
- opencode adapter
- gemini adapter
- provider capability validation


### Phase 6: polish and tests


- integration tests
- Rich live output improvements
- docs cleanup
- error message refinement


After each phase, run tests and keep the codebase working.


---


## 26. Definition of done


The implementation is done when all of the following are true:


1. `goalseek project init <name>` creates the expected scaffold.
2. manifest validation blocks loop start when metric configuration is missing.
3. `goalseek setup` reads all scoped files and produces a persisted setup snapshot.
4. `goalseek baseline` records iteration 0 and writes baseline artifacts.
5. a three-iteration run with the fake provider produces plan files, commits, verifier logs, and a final summary.
6. worse metric outcomes produce revert commits instead of resets.
7. `goalseek step` advances one phase at a time and can be resumed.
8. `goalseek direct` changes future iteration context without mutating protected files.
9. project-local artifacts remain inside the project root.
10. equivalent core controls are available through the Python API.
11. automated tests cover the core paths above.


---


## 27. Explicit instructions to the coding agent


When implementing this spec:
- make the coding agent run in 100% automated mode, no human intervention required.
- The coding agent should not pause for human approval when in loop mode.
- prefer small, testable modules;
- keep all business logic out of CLI command functions;
- do not implement remote execution yet;
- do not add speculative abstractions unrelated to the documented extension points;
- keep file and data formats stable and human-inspectable;
- use typed models for contracts and structured errors for failure paths;
- make the fake provider and integration fixtures first-class so the loop can be tested without external services;
- preserve append-only logs and git history semantics;
- optimize for correctness, debuggability, and auditability over cleverness.



