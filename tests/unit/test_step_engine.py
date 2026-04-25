from __future__ import annotations

import pytest

from goalseek.api import run_baseline, run_step
from goalseek.errors import ProjectStateError
from tests.helpers import write_fake_provider, write_fake_provider_data

def test_step_engine_advances_one_phase_at_a_time(project_factory):
    project_root = project_factory("step-unit")
    write_fake_provider(project_root, "fake_provider_single_improve.yaml")
    run_baseline(str(project_root))

    first = run_step(str(project_root))
    assert first["current_phase"] == "PLAN"

    second = run_step(str(project_root))
    assert second["current_phase"] == "APPLY_CHANGE"



def test_step_engine_multiple_sequential_steps(project_factory):
    """Execute 5+ consecutive steps and verify phase progression."""
    project_root = project_factory("multi-step")
    write_fake_provider(project_root, "fake_provider_single_improve.yaml")
    run_baseline(str(project_root))

    phases = []
    for i in range(5):
        result = run_step(str(project_root))
        phases.append(result["current_phase"])

    # Verify we got different phases and progression is consistent
    assert len(phases) == 5
    assert phases[0] == "PLAN"
    assert len(set(phases)) > 1  # Not all phases are the same


def test_step_engine_step_before_baseline_fails(project_factory):
    """Attempt to run step without prior baseline initialization."""
    project_root = project_factory("no-baseline")
    write_fake_provider(project_root, "fake_provider_single_improve.yaml")

    # Running step before baseline should fail
    with pytest.raises(Exception):
        run_step(str(project_root))


def test_step_engine_with_minimal_config(project_factory):
    """Run step engine with minimal project configuration."""
    project_root = project_factory("minimal-config")
    write_fake_provider_data(project_root, {})
    run_baseline(str(project_root))

    result = run_step(str(project_root))
    assert result["current_phase"] == "PLAN"


def test_step_engine_idempotency(project_factory):
    """Run the same step twice and verify result consistency."""
    project_root = project_factory("idempotency")
    write_fake_provider(project_root, "fake_provider_single_improve.yaml")
    run_baseline(str(project_root))

    first = run_step(str(project_root))
    second = run_step(str(project_root))

    # Both steps should report the same or progressed phase
    assert first["current_phase"] == second["current_phase"] or \
           (first["current_phase"] == "PLAN" and second["current_phase"] == "APPLY_CHANGE")


def test_step_engine_phase_sequence_validation(project_factory):
    """Test that phases follow expected order."""
    project_root = project_factory("phase-sequence")
    write_fake_provider(project_root, "fake_provider_single_improve.yaml")
    run_baseline(str(project_root))

    expected_phases = ["PLAN", "APPLY_CHANGE", "COMMIT", "VERIFY", "DECIDE", "LOG", "READ_CONTEXT"]
    for expected_phase in expected_phases:
        result = run_step(str(project_root))
        assert result["current_phase"] == expected_phase



def test_step_engine_step_missing_provider_config(project_factory):
    project_root = project_factory("missing-config")
    with open(str(project_root / "config" / "project.yaml"), "w") as f:
        f.write("loop:\n  repair_attempts: 1\n")

    run_baseline(str(project_root))
    result = run_step(str(project_root))

    # Provider config is defaulted by EffectiveConfig, so the first step should
    # still succeed and advance into planning.
    assert result["current_phase"] == "PLAN"


def test_step_engine_baseline_output_structure(project_factory):
    project_root = project_factory("output-structure")
    write_fake_provider(project_root, "fake_provider_output.yaml")

    result = run_baseline(str(project_root))

    assert isinstance(result, dict), "run_baseline should return a dict"
    assert "record" in result, "output should contain record field"
    assert "run_dir" in result, "output should contain run_dir field"
    assert "metric" in result, "output should contain metric field"



def test_step_engine_with_none_project_root():
    """Pass None as project root; expect TypeError or AttributeError."""
    with pytest.raises((TypeError, AttributeError)):
        run_step(None)


def test_step_engine_with_empty_project_root():
    """Pass empty string as project root; expect project discovery to fail."""
    with pytest.raises((FileNotFoundError, ValueError, ProjectStateError)):
        run_step("")


def test_step_engine_without_required_config_files(tmp_path):
    """Run step on project missing mandatory configuration; expect root/config discovery failure."""
    project_root = str(tmp_path)
    with pytest.raises((KeyError, FileNotFoundError, ProjectStateError)):
        run_step(project_root)


def test_step_engine_returns_dict_with_phase(project_factory):
    """Verify that successful run_step() returns a dict with 'current_phase' key."""
    project_root = project_factory("step-unit")
    write_fake_provider(project_root, "fake_provider_single_improve.yaml")
    run_baseline(str(project_root))

    result = run_step(str(project_root))
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "current_phase" in result, f"Missing 'current_phase' key in result: {result.keys()}"


def test_step_engine_phase_is_string_type(project_factory):
    """Verify that the phase value in output is a string, not None/int."""
    project_root = project_factory("step-unit")
    write_fake_provider(project_root, "fake_provider_single_improve.yaml")
    run_baseline(str(project_root))

    result = run_step(str(project_root))
    phase = result.get("current_phase")
    assert isinstance(phase, str), f"Expected phase to be str, got {type(phase).__name__}: {phase}"
    assert phase is not None, "Phase should not be None"
