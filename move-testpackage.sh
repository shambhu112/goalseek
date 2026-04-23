#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: $0 [--overwrite|-o] <target-directory>" >&2
}

overwrite=false
target_dir=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--overwrite)
      overwrite=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
    *)
      if [[ -n "$target_dir" ]]; then
        echo "Too many arguments." >&2
        usage
        exit 1
      fi
      target_dir="$1"
      shift
      ;;
  esac
done

if [[ -z "$target_dir" ]]; then
  usage
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$script_dir/test-package"

mkdir -p "$target_dir"

source_dir="$(cd "$source_dir" && pwd)"
target_dir="$(cd "$target_dir" && pwd)"

git_repo=false
auto_commit=false
if git -C "$target_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git_repo=true
  if [[ -z "$(git -C "$target_dir" status --porcelain)" ]]; then
    auto_commit=true
  fi
fi

if [[ "$target_dir" == "$source_dir" ]]; then
  echo "Target directory must be different from $source_dir" >&2
  exit 1
fi

case "$target_dir" in
  "$source_dir"/*)
    echo "Target directory cannot be inside $source_dir" >&2
    exit 1
    ;;
esac

shopt -s dotglob nullglob
items=("$source_dir"/*)

if [[ ${#items[@]} -eq 0 ]]; then
  echo "Nothing to move from $source_dir"
  exit 0
fi

if [[ "$overwrite" == "true" ]]; then
  for item in "${items[@]}"; do
    item_name="$(basename "$item")"
    destination="$target_dir/$item_name"
    if [[ -e "$destination" || -L "$destination" ]]; then
      rm -rf -- "$destination"
    fi
    cp -a -- "$item" "$target_dir"/
  done
else
  for item in "${items[@]}"; do
    item_name="$(basename "$item")"
    destination="$target_dir/$item_name"
    if [[ -e "$destination" || -L "$destination" ]]; then
      echo "Target already has '$item_name'. Re-run with --overwrite to replace it." >&2
      exit 1
    fi
    cp -a -- "$item" "$target_dir"/
  done
fi

echo "Copied ${#items[@]} item(s) from $source_dir to $target_dir (overwrite=$overwrite)"

if [[ "$auto_commit" == "true" ]]; then
  git -C "$target_dir" -c user.name=goalseek -c user.email=goalseek@example.invalid add --all
  git -C "$target_dir" -c user.name=goalseek -c user.email=goalseek@example.invalid commit -m "project: import test package" >/dev/null
  echo "Committed imported files in $target_dir"
elif [[ "$git_repo" == "true" ]]; then
  echo "Skipped auto-commit because $target_dir already had uncommitted changes" >&2
fi
