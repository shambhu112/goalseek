from __future__ import annotations

import json
import math
import re
from pathlib import Path

from goalseek.errors import MetricExtractionError
from goalseek.models.manifest import MetricConfig
from goalseek.models.results import MetricResult, VerificationCommandResult


def extract_metric(
    metric: MetricConfig,
    project_root: str | Path,
    command_results: list[VerificationCommandResult],
) -> MetricResult:
    root = Path(project_root).expanduser().resolve()
    try:
        value: float
        if metric.extractor.type.value == "json_file":
            payload = json.loads((root / metric.extractor.path).read_text(encoding="utf-8"))
            value = float(_json_pointer(payload, metric.extractor.json_pointer or ""))
        elif metric.extractor.type.value == "stdout_regex":
            haystack = "\n".join(result.stdout for result in command_results)
            value = _extract_regex(haystack, metric.extractor.regex or "")
        else:
            haystack = "\n".join(result.stderr for result in command_results)
            value = _extract_regex(haystack, metric.extractor.regex or "")
    except Exception as exc:
        raise MetricExtractionError(str(exc)) from exc

    thresholds_passed = thresholds_pass(metric, value)
    return MetricResult(
        name=metric.name,
        value=value,
        direction=metric.direction,
        thresholds_passed=thresholds_passed,
        extractor_type=metric.extractor.type.value,
    )


def compare(previous: float | None, current: float | None, direction: str, epsilon: float) -> str:
    previous_is_valid = _is_finite_metric(previous)
    current_is_valid = _is_finite_metric(current)
    if not previous_is_valid or not current_is_valid:
        if current_is_valid and not previous_is_valid:
            return "better"
        if previous_is_valid and not current_is_valid:
            return "worse"
        return "equal"
    if direction == "maximize":
        if current > previous + epsilon:
            return "better"
        if abs(current - previous) <= epsilon:
            return "equal"
        return "worse"
    if current < previous - epsilon:
        return "better"
    if abs(current - previous) <= epsilon:
        return "equal"
    return "worse"


def thresholds_pass(metric: MetricConfig, value: float | None) -> bool:
    if not _is_finite_metric(value):
        return False
    if metric.min_pass is not None and value < metric.min_pass:
        return False
    if metric.max_pass is not None and value > metric.max_pass:
        return False
    return True


def tie_breaker_prefers_candidate(retained_changed_loc: int | None, candidate_changed_loc: int | None) -> bool:
    if candidate_changed_loc is None:
        return False
    if retained_changed_loc is None:
        return True
    return candidate_changed_loc < retained_changed_loc


def _json_pointer(payload: object, pointer: str) -> object:
    if pointer == "":
        return payload
    current = payload
    for token in pointer.strip("/").split("/"):
        if isinstance(current, list):
            current = current[int(token)]
        else:
            current = current[token]
    return current


def _extract_regex(haystack: str, pattern: str) -> float:
    match = re.search(pattern, haystack, re.MULTILINE)
    if not match:
        raise MetricExtractionError("metric regex did not match output")
    try:
        return float(match.group(1))
    except (IndexError, ValueError) as exc:
        raise MetricExtractionError("metric regex must expose one numeric capture group") from exc


def _is_finite_metric(value: float | None) -> bool:
    try:
        return value is not None and math.isfinite(value)
    except TypeError:
        return False
