#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
  PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="$(command -v python3)"
else
  echo "Python interpreter not found." >&2
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
"$PYTHON" -m build "$STAGING_DIR" --outdir "$SCRIPT_DIR/dist"

echo ""
echo "Built files:"
ls -lh dist/
