#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d .venv ]]; then
  uv venv .venv
fi

uv sync --extra dev

unset GOALSEEK_LIVE_CODEX

uv run pytest -m "not live" "$@"
