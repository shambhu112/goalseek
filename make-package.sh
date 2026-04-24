#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Cleaning old build artifacts..."
rm -rf build dist/*.tar.gz dist/*.whl

echo "Building package..."
python -m build

echo ""
echo "Built files:"
ls -lh dist/
