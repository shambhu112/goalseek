# Developer Shell Scripts

This file explains the shell scripts in the repository root.

## `pytest-stub.sh`

Runs the test suite without live Codex network calls.

Use this for normal local development.

```bash
./pytest-stub.sh
```

What it does:

- Creates `.venv` if missing.
- Installs development dependencies with `uv sync --extra dev`.
- Unsets `GOALSEEK_LIVE_CODEX`.
- Runs `uv run pytest -m "not live"`.
- Passes any extra arguments through to pytest.

Example:

```bash
./pytest-stub.sh tests/unit/test_codex_provider.py -q
```

## `pytest-live.sh`

Runs only live Codex pytest tests.

Use this when testing real Codex SDK behavior against the network.

```bash
./pytest-live.sh
```

What it does:

- Loads keys from `.env`.
- Creates `.venv` if missing.
- Requires a local `codex` CLI on `PATH`, unless `CODEX_BIN` is set.
- Installs development dependencies with `uv sync --extra dev`.
- Installs `openai-codex` without its bundled binary dependency.
- Adds a local `codex_cli_bin` shim pointing the SDK at the installed `codex` CLI.
- Requires `OPENAI_API_KEY`.
- Sets `GOALSEEK_LIVE_CODEX=1` by default.
- Sets `GOALSEEK_LIVE_CODEX_MODEL=gpt-5-codex` by default.
- Runs `uv run --no-sync pytest -m live`.
- Passes any extra arguments through to pytest.

Expected `.env` key:

```bash
OPENAI_API_KEY=your_key_here
```

Optional overrides:

```bash
CODEX_BIN=/path/to/codex ./pytest-live.sh
GOALSEEK_LIVE_CODEX_MODEL=gpt-5.1-codex ./pytest-live.sh
```

Example:

```bash
./pytest-live.sh tests/unit/test_codex_provider.py -q
```

## `make-package.sh`

Builds a clean source and wheel package into `dist/`.

```bash
./make-package.sh
```

What it does:

- Runs from the repository root.
- Creates `.venv` if missing.
- Installs development dependencies with `uv sync --extra dev`.
- Deletes old `build/`, `dist/*.tar.gz`, and `dist/*.whl`.
- Stages only package inputs into a temp directory.
- Copies `pyproject.toml`, `README.md`, `LICENSE`, and `src/goalseek/`.
- Excludes Python cache files.
- Builds with `uv run --no-sync python -m build`.
- Updates `dist/version-info.json` with production version, source archive name, and build date.
- Lists built files.

Requires `uv`.

## `make-incremental-package.sh`

Bumps the patch version, then builds a package.

```bash
./make-incremental-package.sh
```

What it does:

- Creates `.venv` if missing.
- Installs development dependencies with `uv sync --extra dev`.
- Reads `project.version` from `pyproject.toml`.
- Requires version format `MAJOR.MINOR.PATCH`.
- Increments only the patch number.
- Updates `pyproject.toml`.
- Updates `src/goalseek/__init__.py`.
- Runs `make-package.sh`.

Example version bump:

```text
0.1.2 -> 0.1.3
```

## `new-branch.sh`

Creates and switches to a new git branch.

```bash
./new-branch.sh
```

With explicit branch name:

```bash
./new-branch.sh my-branch-name
```

What it does:

- Requires a clean git working tree.
- Accepts zero or one argument.
- If a branch name is provided, uses it.
- If no branch name is provided, reads the current version from `pyproject.toml`.
- Builds default branch name as `v<next-patch-version>-<ddmm>`.
- Validates branch name with `git check-ref-format`.
- Fails if the local branch already exists.
- Runs `git switch -c <branch>`.

Example generated branch:

```text
v0.1.3-2105
```
