"""Weekly / monthly aggregate stats (US-014, US-015).

Pure aggregation: takes a workout iterable + window dates, returns the row to
upsert in `weekly_stats` / `monthly_stats`.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta


@dataclass(slots=True)
class WorkoutAggInput:
    """Minimal workout shape stats need (joined sets aggregated upstream)."""

    workout_id: str
    start_time: datetime
    duration_minutes: int
    total_volume_kg: float
    pr_count: int = 0
    exercises: list[ExerciseAggInput] = field(default_factory=list)


@dataclass(slots=True)
class ExerciseAggInput:
    exercise_template_id: str | None
    exercise_title: str
    primary_muscle_group: str | None
    sets: list[tuple[float | None, int | None, str]]  # (weight, reps, set_type)


def _set_volume(weight: float | None, reps: int | None, set_type: str) -> float:
    if set_type in {"warmup", "failure"}:
        return 0.0
    if weight is None or reps is None:
        return 0.0
    return float(weight) * float(reps)


@dataclass(slots=True)
class PeriodStats:
    period: str  # "week" or "month"
    period_start: date
    period_end: date
    total_sessions: int
    total_duration_minutes: int
    total_volume_kg: float
    volume_per_muscle_group: dict[str, float]
    pr_count: int
    sessions_by_day: dict[str, int]
    top_exercises: list[tuple[str, float]]  # (exercise_title, volume) top 5


def week_bounds(d: date) -> tuple[date, date]:
    """ISO week (Mon..Sun) bounds containing d."""
    monday = d - timedelta(days=d.weekday())
    return monday, monday + timedelta(days=6)


def month_bounds(d: date) -> tuple[date, date]:
    first = d.replace(day=1)
    if first.month == 12:
        next_month = first.replace(year=first.year + 1, month=1)
    else:
        next_month = first.replace(month=first.month + 1)
    return first, next_month - timedelta(days=1)


def aggregate_period(
    workouts: list[WorkoutAggInput],
    *,
    period: str,
    period_start: date,
    period_end: date,
) -> PeriodStats:
    """Compute the stats row for [period_start, period_end] inclusive."""
    total_sessions = 0
    total_duration_minutes = 0
    total_volume_kg = 0.0
    pr_count = 0
    volume_per_muscle_group: dict[str, float] = defaultdict(float)
    sessions_by_day: dict[str, int] = defaultdict(int)
    volume_per_exercise: dict[str, float] = defaultdict(float)

    for w in workouts:
        d = w.start_time.date()
        if d < period_start or d > period_end:
            continue
        total_sessions += 1
        total_duration_minutes += w.duration_minutes
        total_volume_kg += w.total_volume_kg or 0.0
        pr_count += w.pr_count
        sessions_by_day[d.isoformat()] += 1
        for ex in w.exercises:
            ex_volume = 0.0
            for weight, reps, set_type in ex.sets:
                ex_volume += _set_volume(weight, reps, set_type)
            if ex_volume > 0:
                volume_per_exercise[ex.exercise_title] += ex_volume
                if ex.primary_muscle_group:
                    volume_per_muscle_group[ex.primary_muscle_group] += ex_volume

    top_exercises = sorted(volume_per_exercise.items(), key=lambda item: item[1], reverse=True)[:5]

    return PeriodStats(
        period=period,
        period_start=period_start,
        period_end=period_end,
        total_sessions=total_sessions,
        total_duration_minutes=total_duration_minutes,
        total_volume_kg=round(total_volume_kg, 2),
        volume_per_muscle_group={k: round(v, 2) for k, v in volume_per_muscle_group.items()},
        pr_count=pr_count,
        sessions_by_day=dict(sessions_by_day),
        top_exercises=[(t, round(v, 2)) for t, v in top_exercises],
    )
