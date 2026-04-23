from __future__ import annotations

import fnmatch
import os
from pathlib import Path, PurePosixPath

from goalseek.errors import ScopeViolationError


GLOB_CHARS = set("*?[")


def normalize_relpath(value: str) -> str:
    candidate = PurePosixPath(value)
    normalized = candidate.as_posix().lstrip("./")
    if normalized == ".":
        return ""
    return normalized


def ensure_within_root(root: Path, candidate: Path) -> Path:
    root_real = root.resolve()
    candidate_real = candidate.resolve(strict=False)
    try:
        candidate_real.relative_to(root_real)
    except ValueError as exc:
        raise ScopeViolationError(f"path escapes project root: {candidate}") from exc
    return candidate_real


def manifest_path_is_safe(path: str) -> bool:
    if not path or os.path.isabs(path):
        return False
    pure = PurePosixPath(path)
    return ".." not in pure.parts


def static_prefix(pattern: str) -> str:
    prefix = []
    for part in PurePosixPath(pattern).parts:
        if any(char in GLOB_CHARS for char in part):
            break
        prefix.append(part)
    return PurePosixPath(*prefix).as_posix() if prefix else ""


def pattern_matches(path: str, pattern: str) -> bool:
    path = normalize_relpath(path)
    pattern = normalize_relpath(pattern)
    if pattern.endswith("/**"):
        return path == pattern[:-3] or path.startswith(pattern[:-3] + "/")
    if any(char in pattern for char in GLOB_CHARS):
        return fnmatch.fnmatch(path, pattern)
    return path == pattern


def patterns_overlap(left: str, right: str) -> bool:
    left_prefix = static_prefix(left)
    right_prefix = static_prefix(right)
    if not left_prefix or not right_prefix:
        return left == right
    return (
        left_prefix == right_prefix
        or left_prefix.startswith(right_prefix + "/")
        or right_prefix.startswith(left_prefix + "/")
    )
