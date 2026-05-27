"""Unit tests for src.services.fitness.pr_detection (US-012). Pure, no DB/LLM."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from src.services.fitness.pr_detection import (
    PRBaselines,
    SetContext,
    detect_all_prs,
    detect_muscle_group_volume_prs,
    detect_one_rep_max_prs,
    detect_reps_at_load_prs,
    detect_session_volume_prs,
    estimate_one_rep_max,
    weight_bucket,
)

# ----- Epley + helpers ---------------------------------------------------------


def test_epley_known_value():
    # Epley: 90kg x 5 reps → 90 * (1 + 5/30) = 105.0
    assert estimate_one_rep_max(90, 5) == 105.0


def test_epley_single_rep_close_to_weight():
    # 1 rep → 1RM = weight * (1 + 1/30) = 100 * 1.0333... = 103.3 (rounded)
    assert estimate_one_rep_max(100, 1) == pytest.approx(103.3, abs=0.01)


def test_epley_rejects_zero_reps():
    with pytest.raises(ValueError):
        estimate_one_rep_max(100, 0)


def test_weight_bucket_rounds_down():
    assert weight_bucket(82.5) == "80kg"
    assert weight_bucket(80.0) == "80kg"
    assert weight_bucket(84.99) == "80kg"
    assert weight_bucket(85.0) == "85kg"
    assert weight_bucket(127, granularity_kg=10) == "120kg"


# ----- Fixtures helper ---------------------------------------------------------


def _set(
    when: datetime,
    *,
    exercise_id: str = "bench",
    title: str = "Bench Press",
    muscle: str | None = "chest",
    weight: float | None = 80.0,
    reps: int | None = 5,
    set_type: str = "normal",
    workout_id=None,
) -> SetContext:
    return SetContext(
        set_id=uuid4() if weight else None,
        workout_id=workout_id or uuid4(),
        achieved_at=when,
        exercise_template_id=exercise_id,
        exercise_title=title,
        primary_muscle_group=muscle,
        weight_kg=weight,
        reps=reps,
        set_type=set_type,
    )


_NOW = datetime(2026, 5, 25, 12, 0, tzinfo=UTC)


# ----- One-rep-max -------------------------------------------------------------


def test_one_rep_max_emits_pr_when_no_baseline():
    sets = [_set(_NOW, weight=80, reps=5)]  # 1RM = 93.3
    prs = detect_one_rep_max_prs(sets, PRBaselines())
    assert len(prs) == 1
    assert prs[0].pr_type == "one_rep_max"
    assert prs[0].new_value == pytest.approx(93.3, abs=0.01)
    assert prs[0].old_value is None
    assert prs[0].gain is None


def test_one_rep_max_emits_only_when_beats_baseline():
    sets = [_set(_NOW, weight=80, reps=5)]  # 93.3
    baselines = PRBaselines(one_rep_max={"bench": 100.0})
    prs = detect_one_rep_max_prs(sets, baselines)
    assert prs == []


def test_one_rep_max_returns_only_top_within_batch():
    sets = [
        _set(_NOW, weight=80, reps=5),  # 93.3
        _set(_NOW + timedelta(hours=1), weight=85, reps=5),  # 99.2
        _set(_NOW + timedelta(hours=2), weight=82, reps=5),  # 95.7 — skipped
    ]
    prs = detect_one_rep_max_prs(sets, PRBaselines())
    assert len(prs) == 1
    assert prs[0].new_value == pytest.approx(99.2, abs=0.01)


def test_one_rep_max_skips_warmup_and_failure_sets():
    sets = [
        _set(_NOW, weight=120, reps=3, set_type="warmup"),  # would be 132
        _set(_NOW + timedelta(hours=1), weight=80, reps=5),  # 93.3
        _set(_NOW + timedelta(hours=2), weight=200, reps=1, set_type="failure"),  # would be 206
    ]
    prs = detect_one_rep_max_prs(sets, PRBaselines())
    assert len(prs) == 1
    assert prs[0].new_value == pytest.approx(93.3, abs=0.01)


def test_one_rep_max_skips_null_weight_or_reps():
    sets = [
        _set(_NOW, weight=None, reps=5),
        _set(_NOW + timedelta(hours=1), weight=80, reps=None),
    ]
    assert detect_one_rep_max_prs(sets, PRBaselines()) == []


# ----- Reps at load ------------------------------------------------------------


def test_reps_at_load_buckets_by_weight():
    sets = [
        _set(_NOW, weight=82.5, reps=5),  # bucket 80kg
        _set(_NOW + timedelta(hours=1), weight=82.5, reps=7),  # bucket 80kg — beats
        _set(_NOW + timedelta(hours=2), weight=92.5, reps=4),  # bucket 90kg (new)
    ]
    prs = detect_reps_at_load_prs(sets, PRBaselines())
    by_bucket = {p.bucket: p for p in prs}
    assert set(by_bucket.keys()) == {"80kg", "90kg"}
    assert by_bucket["80kg"].new_value == 7
    assert by_bucket["90kg"].new_value == 4


def test_reps_at_load_respects_baseline():
    sets = [_set(_NOW, weight=82.5, reps=4)]
    baselines = PRBaselines(reps_at_load={("bench", "80kg"): 6})
    assert detect_reps_at_load_prs(sets, baselines) == []


# ----- Session volume ----------------------------------------------------------


def test_session_volume_aggregates_per_workout():
    wid = uuid4()
    sets = [
        _set(_NOW, weight=80, reps=5, workout_id=wid),  # 400
        _set(_NOW + timedelta(minutes=5), weight=80, reps=5, workout_id=wid),  # +400
        _set(_NOW + timedelta(minutes=10), weight=80, reps=5, workout_id=wid),  # +400
    ]
    prs = detect_session_volume_prs(sets, PRBaselines())
    assert len(prs) == 1
    assert prs[0].new_value == 1200.0


def test_session_volume_emits_only_when_beats_baseline():
    sets = [_set(_NOW, weight=80, reps=5)]  # 400 vol
    baselines = PRBaselines(session_volume={"bench": 500.0})
    assert detect_session_volume_prs(sets, baselines) == []


# ----- Muscle-group weekly volume ----------------------------------------------


def test_muscle_group_volume_groups_by_week_and_muscle():
    sets = [
        _set(_NOW, weight=80, reps=5, muscle="chest"),  # 400 chest, week N
        _set(_NOW + timedelta(days=1), weight=80, reps=5, muscle="chest"),  # +400
        _set(_NOW + timedelta(days=10), weight=80, reps=5, muscle="chest"),  # 400 week N+2
        _set(_NOW, weight=100, reps=3, muscle="back"),  # 300 back
    ]
    prs = detect_muscle_group_volume_prs(sets, PRBaselines())
    by_group = {p.exercise_title: p for p in prs}
    assert "chest" in by_group
    assert "back" in by_group
    assert by_group["chest"].new_value == 800.0  # best week = 800
    assert by_group["back"].new_value == 300.0


def test_muscle_group_volume_skips_when_no_muscle_group():
    sets = [_set(_NOW, weight=80, reps=5, muscle=None)]
    assert detect_muscle_group_volume_prs(sets, PRBaselines()) == []


# ----- Detector orchestrator ---------------------------------------------------


def test_detect_all_prs_returns_all_four_types():
    sets = [_set(_NOW, weight=80, reps=5)]
    types = {p.pr_type for p in detect_all_prs(sets, PRBaselines())}
    assert types == {"one_rep_max", "reps_at_load", "session_volume", "muscle_group_volume"}
