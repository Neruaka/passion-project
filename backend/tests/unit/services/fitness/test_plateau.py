"""Unit tests for src.services.fitness.plateau (US-013)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.services.fitness.plateau import (
    ExerciseSession,
    TargetSchedule,
    detect_behind_schedule,
    detect_plateaus,
    detect_regressions,
    detect_stalls,
    sessions_from_sets,
)
from src.services.fitness.pr_detection import SetContext


def _sess(when: datetime, weight: float, reps: int) -> ExerciseSession:
    return ExerciseSession(
        exercise_key="bench",
        exercise_title="Bench",
        exercise_template_id="bench",
        achieved_at=when,
        top_weight_kg=weight,
        top_reps=reps,
    )


_T0 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def test_plateau_official_when_same_weight_n_sessions():
    sessions = [_sess(_T0 + timedelta(days=i * 7), 80.0, 5) for i in range(4)]
    findings = detect_plateaus({"bench": sessions}, phase="bulking", threshold_sessions=4)
    assert len(findings) == 1
    f = findings[0]
    assert f.analysis_type == "plateau_official"
    assert f.details["stuck_at_weight_kg"] == 80.0


def test_plateau_official_no_false_positive_when_weight_increases():
    sessions = [
        _sess(_T0, 80.0, 5),
        _sess(_T0 + timedelta(days=7), 82.5, 5),
        _sess(_T0 + timedelta(days=14), 82.5, 5),
        _sess(_T0 + timedelta(days=21), 85.0, 5),
    ]
    assert detect_plateaus({"bench": sessions}, threshold_sessions=4) == []


def test_plateau_uses_phase_threshold():
    """Cutting phase tolerates more stagnation (6 sessions vs 3 for bulking)."""
    sessions = [_sess(_T0 + timedelta(days=i * 7), 80.0, 5) for i in range(5)]
    # 5 sessions of stagnation:
    assert detect_plateaus({"bench": sessions}, phase="cutting") == []  # threshold 6, no flag
    assert detect_plateaus({"bench": sessions}, phase="bulking") != []  # threshold 3, flagged


def test_stalls_detect_no_1rm_improvement():
    sessions = [
        _sess(_T0, 80, 5),  # 1RM ~93.3
        _sess(_T0 + timedelta(days=7), 70, 5),  # 1RM ~81.7 — lower
        _sess(_T0 + timedelta(days=14), 75, 5),  # 87.5
        _sess(_T0 + timedelta(days=21), 78, 5),  # 91.0
        _sess(_T0 + timedelta(days=28), 80, 5),  # 93.3 — same as start
    ]
    findings = detect_stalls({"bench": sessions}, window_sessions=4)
    assert len(findings) == 1
    assert findings[0].analysis_type == "plateau_stalled"


def test_regression_when_recent_below_older():
    now = datetime.now(tz=UTC)
    # older: heavy training (best 1RM ~120)
    # recent: lighter (best 1RM ~100) — drop > 7%
    sessions = [
        _sess(now - timedelta(days=50), 100, 5),  # 1RM ~116.7
        _sess(now - timedelta(days=45), 105, 5),  # 1RM ~122.5
        _sess(now - timedelta(days=10), 80, 5),  # 1RM ~93.3
        _sess(now - timedelta(days=5), 80, 5),  # 1RM ~93.3
    ]
    findings = detect_regressions({"bench": sessions}, phase="bulking")
    assert len(findings) == 1
    assert findings[0].analysis_type == "regression"
    assert findings[0].details["drop_pct"] > 5


def test_behind_schedule_when_weeks_elapsed_exceed_estimate():
    now = datetime.now(tz=UTC)
    targets = [
        TargetSchedule(
            exercise_template_id="bench",
            exercise_title="Bench",
            set_at=now - timedelta(weeks=20),
            estimated_weeks_max=10,
            target_1rm_estimate=120.0,
        )
    ]
    findings = detect_behind_schedule(targets, current_1rms={"bench": 90.0})
    assert len(findings) == 1
    assert findings[0].analysis_type == "behind_schedule"


def test_behind_schedule_no_flag_when_achieved():
    now = datetime.now(tz=UTC)
    targets = [
        TargetSchedule(
            exercise_template_id="bench",
            exercise_title="Bench",
            set_at=now - timedelta(weeks=20),
            estimated_weeks_max=10,
            target_1rm_estimate=120.0,
        )
    ]
    findings = detect_behind_schedule(targets, current_1rms={"bench": 130.0})
    assert findings == []


def test_sessions_from_sets_picks_top_working_set_per_day():
    from uuid import uuid4

    day1 = _T0
    sets = [
        SetContext(uuid4(), uuid4(), day1, "bench", "Bench", "chest", 60, 10, "warmup"),
        SetContext(uuid4(), uuid4(), day1, "bench", "Bench", "chest", 80, 5, "normal"),
        SetContext(uuid4(), uuid4(), day1, "bench", "Bench", "chest", 82.5, 4, "normal"),
        SetContext(uuid4(), uuid4(), day1, "bench", "Bench", "chest", 80, 6, "normal"),
    ]
    by_exercise = sessions_from_sets(sets)
    assert "bench" in by_exercise
    assert len(by_exercise["bench"]) == 1
    top = by_exercise["bench"][0]
    assert top.top_weight_kg == 82.5
    assert top.top_reps == 4
