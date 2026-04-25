from __future__ import annotations

from goalseek.models.manifest import MetricConfig, MetricExtractor, MetricExtractorType
from goalseek.verification.metrics import compare, thresholds_pass, tie_breaker_prefers_candidate


import math


def test_metric_compare_handles_maximize_and_minimize():
    assert compare(1.0, 2.0, "maximize", 0.0) == "better"
    assert compare(2.0, 1.0, "maximize", 0.0) == "worse"
    assert compare(2.0, 1.0, "minimize", 0.0) == "better"
    assert compare(1.0, 1.0, "maximize", 0.1) == "equal"


def test_thresholds_and_tie_breaker():
    metric = MetricConfig(
        name="score",
        direction="maximize",
        extractor=MetricExtractor(type=MetricExtractorType.JSON_FILE, path="x.json", json_pointer="/metric"),
        min_pass=1.0,
        max_pass=10.0,
    )
    assert thresholds_pass(metric, 5.0) is True
    assert thresholds_pass(metric, 0.5) is False
    assert tie_breaker_prefers_candidate(10, 5) is True
    assert tie_breaker_prefers_candidate(5, 5) is False

def test_compare_with_nan_values():
    nan = float('nan')
    result = compare(nan, 2.0, "maximize", 0.0)
    assert result is not None


def test_compare_with_none_values():
    result = compare(None, 2.0, "maximize", 0.0)
    assert result is not None


def test_thresholds_with_negative_metrics():
    metric = MetricConfig(
        name="score",
        direction="maximize",
        extractor=MetricExtractor(type=MetricExtractorType.JSON_FILE, path="x.json", json_pointer="/metric"),
        min_pass=-10.0,
        max_pass=0.0,
    )
    assert thresholds_pass(metric, -5.0) is True
    assert thresholds_pass(metric, -15.0) is False


def test_thresholds_with_missing_bounds():
    metric = MetricConfig(
        name="score",
        direction="maximize",
        extractor=MetricExtractor(type=MetricExtractorType.JSON_FILE, path="x.json", json_pointer="/metric"),
        min_pass=None,
        max_pass=None,
    )
    result = thresholds_pass(metric, 5.0)
    assert result is not None


def test_tie_breaker_with_extreme_values():
    result_large = tie_breaker_prefers_candidate(1e10, 1e9)
    assert result_large is not None

    result_negative = tie_breaker_prefers_candidate(-5, -10)
    assert result_negative is not None

    result_identical = tie_breaker_prefers_candidate(42, 42)
    assert result_identical is not None
