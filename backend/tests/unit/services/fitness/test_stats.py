"""Unit tests for src.services.fitness.stats (US-014/015)."""

from __future__ import annotations

from datetime import UTC, date, datetime

from src.services.fitness.stats import (
    ExerciseAggInput,
    WorkoutAggInput,
    aggregate_period,
    month_bounds,
    week_bounds,
)


def _ex(title: str, muscle: str, *sets) -> ExerciseAggInput:
    return ExerciseAggInput(
        exercise_template_id=None,
        exercise_title=title,
        primary_muscle_group=muscle,
        sets=list(sets),
    )


def _w(when: datetime, *exercises) -> WorkoutAggInput:
    return WorkoutAggInput(
        workout_id=when.isoformat(),
        start_time=when,
        duration_minutes=60,
        total_volume_kg=sum(
            (w or 0) * (r or 0)
            for ex in exercises
            for w, r, t in ex.sets
            if t not in {"warmup", "failure"}
        ),
        pr_count=0,
        exercises=list(exercises),
    )


def test_week_bounds_returns_monday_to_sunday():
    # 2026-05-27 is a Wednesday
    start, end = week_bounds(date(2026, 5, 27))
    assert start == date(2026, 5, 25)  # Monday
    assert end == date(2026, 5, 31)  # Sunday


def test_month_bounds_returns_first_to_last():
    start, end = month_bounds(date(2026, 5, 15))
    assert start == date(2026, 5, 1)
    assert end == date(2026, 5, 31)
    start, end = month_bounds(date(2026, 12, 15))
    assert start == date(2026, 12, 1)
    assert end == date(2026, 12, 31)


def test_aggregate_period_sums_sessions_and_volume():
    w1 = _w(
        datetime(2026, 5, 25, 12, tzinfo=UTC),
        _ex("Bench", "chest", (80, 5, "normal"), (80, 5, "normal")),
    )
    w2 = _w(
        datetime(2026, 5, 27, 12, tzinfo=UTC),
        _ex("Hack Squat", "quadriceps", (100, 8, "normal")),
    )
    out = aggregate_period(
        [w1, w2], period="week", period_start=date(2026, 5, 25), period_end=date(2026, 5, 31)
    )
    assert out.total_sessions == 2
    assert out.total_volume_kg == 800 + 800  # w1+w2 from total_volume_kg field
    # Volume per muscle group sums set-level (recomputed)
    assert out.volume_per_muscle_group["chest"] == 800
    assert out.volume_per_muscle_group["quadriceps"] == 800
    assert "Bench" in {t for t, _ in out.top_exercises}


def test_aggregate_period_skips_warmup_and_failure_sets():
    w = _w(
        datetime(2026, 5, 25, 12, tzinfo=UTC),
        _ex("Bench", "chest", (40, 10, "warmup"), (80, 5, "normal"), (100, 1, "failure")),
    )
    out = aggregate_period(
        [w], period="week", period_start=date(2026, 5, 25), period_end=date(2026, 5, 31)
    )
    assert out.volume_per_muscle_group["chest"] == 400  # only the working set


def test_aggregate_period_filters_by_date_window():
    w = _w(
        datetime(2026, 4, 1, 12, tzinfo=UTC),  # outside the May 25-31 window
        _ex("Bench", "chest", (80, 5, "normal")),
    )
    out = aggregate_period(
        [w], period="week", period_start=date(2026, 5, 25), period_end=date(2026, 5, 31)
    )
    assert out.total_sessions == 0
    assert out.volume_per_muscle_group == {}
