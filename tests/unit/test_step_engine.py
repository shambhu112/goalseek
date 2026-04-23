from __future__ import annotations

from goalseek.api import run_baseline, run_step
from tests.helpers import write_fake_provider


def test_step_engine_advances_one_phase_at_a_time(project_factory):
    project_root = project_factory("step-unit")
    write_fake_provider(project_root, "fake_provider_single_improve.yaml")
    run_baseline(str(project_root))

    first = run_step(str(project_root))
    assert first["current_phase"] == "PLAN"

    second = run_step(str(project_root))
    assert second["current_phase"] == "APPLY_CHANGE"
