from __future__ import annotations

from goalseek.models.manifest import MetricConfig, MetricExtractor, MetricExtractorType
from goalseek.verification.metrics import compare, thresholds_pass, tie_breaker_prefers_candidate


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
