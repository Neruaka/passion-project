"""Unit tests for src.services.fitness.targets (US-013b)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.services.fitness.targets import (
    CurrentBest,
    TargetInput,
    compute_target_progress,
)


def _target(
    *,
    set_at: datetime,
    weeks_max: int | None = 12,
    baseline_1rm: float = 60.0,
    target_1rm: float = 84.0,
) -> TargetInput:
    return TargetInput(
        exercise_template_id="bench",
        exercise_title="Bench Press",
        workout_day="monday",
        set_at=set_at,
        baseline_weight_kg=50,
        baseline_reps=6,
        baseline_1rm=baseline_1rm,
        target_weight_kg_min=65,
        target_weight_kg_max=70,
        target_reps_min=6,
        target_reps_max=6,
        target_1rm=target_1rm,
        estimated_weeks_min=10,
        estimated_weeks_max=weeks_max,
    )


_NOW = datetime(2026, 5, 28, 12, 0, tzinfo=UTC)


def test_achieved_when_current_meets_target():
    t = _target(set_at=_NOW - timedelta(weeks=4))
    p = compute_target_progress(t, CurrentBest(70, 6, 84.0), now=_NOW)
    assert p.status == "achieved"
    assert p.progress_pct == 100.0


def test_on_track_when_progress_matches_time():
    # 50% through the time, 50% through the progress
    t = _target(set_at=_NOW - timedelta(weeks=6), weeks_max=12)
    halfway_1rm = 60 + (84 - 60) * 0.5
    p = compute_target_progress(t, CurrentBest(60, 6, halfway_1rm), now=_NOW)
    assert p.status == "on_track"
    assert 45 < p.progress_pct < 55


def test_behind_schedule_when_time_outpaces_progress():
    t = _target(set_at=_NOW - timedelta(weeks=10), weeks_max=12)
    p = compute_target_progress(t, CurrentBest(55, 6, 62.0), now=_NOW)  # ~ 8% progress
    assert p.status == "behind_schedule"


def test_ahead_of_schedule_when_progress_outpaces_time():
    t = _target(set_at=_NOW - timedelta(weeks=2), weeks_max=12)  # 16% time
    p = compute_target_progress(t, CurrentBest(65, 6, 78.0), now=_NOW)  # 75% progress
    assert p.status == "ahead_of_schedule"


def test_expired_when_time_exceeds_estimate_and_not_achieved():
    t = _target(set_at=_NOW - timedelta(weeks=20), weeks_max=12)
    p = compute_target_progress(t, CurrentBest(58, 6, 65.0), now=_NOW)
    assert p.status == "expired"


def test_weeks_elapsed_clamped_to_zero():
    t = _target(set_at=_NOW + timedelta(days=1))  # future set_at
    p = compute_target_progress(t, CurrentBest(50, 6, 60.0), now=_NOW)
    assert p.weeks_elapsed == 0


def test_calibrating_when_no_observed_set():
    t = _target(set_at=_NOW - timedelta(weeks=2))
    p = compute_target_progress(t, CurrentBest(None, None, None), now=_NOW)
    assert p.status == "calibrating"
    assert p.progress_pct == 0.0


def test_calibrating_when_zero_one_rm():
    t = _target(set_at=_NOW - timedelta(weeks=2))
    p = compute_target_progress(t, CurrentBest(None, None, 0.0), now=_NOW)
    assert p.status == "calibrating"


def test_below_baseline_when_current_under_baseline():
    t = _target(set_at=_NOW - timedelta(weeks=2), baseline_1rm=60.0, target_1rm=84.0)
    p = compute_target_progress(t, CurrentBest(45, 5, 52.5), now=_NOW)
    assert p.status == "below_baseline"
    assert p.progress_pct < 0  # negative progress now allowed


def test_progress_pct_floor_at_minus_100():
    t = _target(set_at=_NOW - timedelta(weeks=2), baseline_1rm=60.0, target_1rm=84.0)
    p = compute_target_progress(t, CurrentBest(20, 5, 23.3), now=_NOW)
    assert p.progress_pct >= -100.0
