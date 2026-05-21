#!/usr/bin/env bash
set -euo pipefail

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

load_dotenv() {
  local line key value

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="$(trim "$line")"
    [[ -z "$line" || "$line" == \#* ]] && continue

    line="${line#export }"
    [[ "$line" != *=* ]] && continue

    key="$(trim "${line%%=*}")"
    value="$(trim "${line#*=}")"

    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue

    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value:1:${#value}-2}"
    fi

    export "$key=$value"
  done < .env
}

if [[ -f .env ]]; then
  load_dotenv
fi

if [[ ! -d .venv ]]; then
  uv venv .venv
fi

CODEX_BIN="${CODEX_BIN:-$(command -v codex || true)}"
if [[ -z "$CODEX_BIN" ]]; then
  echo "codex CLI missing" >&2
  exit 1
fi

uv sync --extra dev
uv pip install --python .venv/bin/python --no-deps \
  "openai-codex @ git+https://github.com/openai/codex.git#subdirectory=sdk/python"

CODEX_BIN="$CODEX_BIN" uv run --no-sync python - <<'PY'
import os
import sysconfig
from pathlib import Path

codex_bin = Path(os.environ["CODEX_BIN"]).resolve()
site_packages = Path(sysconfig.get_paths()["purelib"])
package_dir = site_packages / "codex_cli_bin"
package_dir.mkdir(exist_ok=True)
init_file = package_dir / "__init__.py"
init_file.write_text(
    "from pathlib import Path\n\n"
    f"_CODEX_BIN = Path({str(codex_bin)!r})\n\n"
    "def bundled_codex_path():\n"
    "    return _CODEX_BIN\n\n"
    "def bundled_path_dir():\n"
    "    return _CODEX_BIN.parent\n"
)
PY

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY missing" >&2
  exit 1
fi

export GOALSEEK_LIVE_CODEX="${GOALSEEK_LIVE_CODEX:-1}"
export GOALSEEK_LIVE_CODEX_MODEL="${GOALSEEK_LIVE_CODEX_MODEL:-gpt-5-codex}"

uv run --no-sync pytest -m live "$@"
