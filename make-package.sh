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

echo "Cleaning old build artifacts..."
rm -rf build dist/*.tar.gz dist/*.whl

STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT

echo "Preparing staged package sources..."
mkdir -p "$STAGING_DIR/src/goalseek"

cp pyproject.toml "$STAGING_DIR/"
cp README.md "$STAGING_DIR/"
cp LICENSE "$STAGING_DIR/"

rsync -a --prune-empty-dirs \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  src/goalseek/ "$STAGING_DIR/src/goalseek/"

echo "Building package..."
"${PYTHON_ARGS[@]}" -m build "$STAGING_DIR" --outdir "$SCRIPT_DIR/dist"

echo "Updating version metadata..."
"${PYTHON_ARGS[@]}" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
import tomllib

script_dir = Path.cwd()
pyproject_path = script_dir / "pyproject.toml"
version_info_path = script_dir / "dist" / "version-info.json"

with pyproject_path.open("rb") as f:
    project = tomllib.load(f)["project"]

version = project["version"]
sdist_name = f"{project['name']}-{version}.tar.gz"
build_date = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

version_info = {}
if version_info_path.exists():
    version_info = json.loads(version_info_path.read_text())

version_info["production-version"] = version
version_info["production-version-file"] = sdist_name
version_info["build-date"] = build_date

version_info_path.write_text(json.dumps(version_info, indent=4) + "\n")
PY

echo ""
echo "Built files:"
ls -lh dist/
