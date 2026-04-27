#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./new-branch.sh [branch-name]

Behavior:
  - Checks git repo is clean before creating branch.
  - If branch name is given, uses it.
  - If not given, creates: v<incremented-version>-<ddmm>
EOF
}

fail() {
  echo "Error: $*" >&2
  exit 1
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 1 ]]; then
  usage
  fail "too many arguments"
fi

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not inside a git repository"

if [[ -n "$(git status --porcelain)" ]]; then
  fail "git repo not clean. commit/stash/discard changes first"
fi

branch_name="${1:-}"

if [[ -z "$branch_name" ]]; then
  version_line="$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -n 1 || true)"

  if [[ "$version_line" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    major="${BASH_REMATCH[1]}"
    minor="${BASH_REMATCH[2]}"
    patch="${BASH_REMATCH[3]}"
  else
    major="0"
    minor="0"
    patch="0"
  fi

  next_patch=$((patch + 1))
  date_part="$(date +%d%m)"
  branch_name="v${major}.${minor}.${next_patch}-${date_part}"
fi

git check-ref-format --branch "$branch_name" >/dev/null 2>&1 || fail "invalid branch name: $branch_name"

if git show-ref --verify --quiet "refs/heads/$branch_name"; then
  fail "branch already exists locally: $branch_name"
fi

git switch -c "$branch_name"
echo "Created and switched to branch: $branch_name"
