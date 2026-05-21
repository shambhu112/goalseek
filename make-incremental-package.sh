#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found." >&2
  exit 1
fi

if [[ ! -d "$SCRIPT_DIR/.venv" ]]; then
  uv venv .venv
fi

uv sync --extra dev

if [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
  PYTHON_ARGS=(uv run --no-sync python)
else
  echo ".venv python not found." >&2
  exit 1
fi

echo "Incrementing package version..."
"${PYTHON_ARGS[@]}" - <<'PY'
from pathlib import Path
import re
import tomllib

script_dir = Path.cwd()
pyproject_path = script_dir / "pyproject.toml"
init_path = script_dir / "src" / "goalseek" / "__init__.py"

with pyproject_path.open("rb") as f:
    version = tomllib.load(f)["project"]["version"]

match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
if not match:
    raise SystemExit(
        f"Unsupported version format {version!r}; expected MAJOR.MINOR.PATCH."
    )

major, minor, patch = (int(part) for part in match.groups())
new_version = f"{major}.{minor}.{patch + 1}"

pyproject_text = pyproject_path.read_text()
pyproject_text, pyproject_count = re.subn(
    r'(?m)^version = "' + re.escape(version) + r'"$',
    f'version = "{new_version}"',
    pyproject_text,
    count=1,
)
if pyproject_count != 1:
    raise SystemExit("Could not update project.version in pyproject.toml.")
pyproject_path.write_text(pyproject_text)

init_text = init_path.read_text()
init_text, init_count = re.subn(
    r'(?m)^__version__ = "' + re.escape(version) + r'"$',
    f'__version__ = "{new_version}"',
    init_text,
    count=1,
)
if init_count != 1:
    raise SystemExit("Could not update __version__ in src/goalseek/__init__.py.")
init_path.write_text(init_text)

print(f"Version incremented: {version} -> {new_version}")
PY

"$SCRIPT_DIR/make-package.sh"
