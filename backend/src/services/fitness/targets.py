"""Target progression: baseline → current → target (US-013b).

Pure logic: takes an ExerciseTarget snapshot + the user's current best, returns
a TargetProgress view (used by the API).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

ProgressStatus = Literal[
    "calibrating",
    "below_baseline",
    "on_track",
    "behind_schedule",
    "ahead_of_schedule",
    "achieved",
    "expired",
]


@dataclass(slots=True, frozen=True)
class TargetInput:
    exercise_template_id: str | None
    exercise_title: str
    workout_day: str | None
    set_at: datetime
    baseline_weight_kg: float | None
    baseline_reps: int | None
    baseline_1rm: float | None
    target_weight_kg_min: float | None
    target_weight_kg_max: float | None
    target_reps_min: int | None
    target_reps_max: int | None
    target_1rm: float | None
    estimated_weeks_min: int | None
    estimated_weeks_max: int | None
    status: str = "active"


@dataclass(slots=True, frozen=True)
class CurrentBest:
    weight_kg: float | None
    reps: int | None
    one_rm: float | None


@dataclass(slots=True)
class TargetProgress:
    exercise_template_id: str | None
    exercise_title: str
    workout_day: str | None
    baseline: CurrentBest
    current: CurrentBest
    target_weight_kg_min: float | None
    target_weight_kg_max: float | None
    target_reps: int | None
    target_1rm: float | None
    progress_pct: float
    weeks_elapsed: int
    weeks_estimated_max: int | None
    status: ProgressStatus


def _safe_div(a: float | None, b: float | None) -> float:
    if a is None or b is None or b == 0:
        return 0.0
    return float(a) / float(b)


def compute_target_progress(
    t: TargetInput,
    current: CurrentBest,
    *,
    now: datetime | None = None,
) -> TargetProgress:
    """Compute a TargetProgress row.

    `progress_pct`: 0% at baseline_1rm, 100% at target_1rm (clamp -100..150).
    `status` precedence:
      - achieved        — current_1rm >= target_1rm
      - calibrating     — no observed working set yet (current.one_rm is None)
      - below_baseline  — current_1rm < baseline_1rm (regression or under-trained)
      - expired         — weeks_elapsed > weeks_estimated_max and not achieved
      - ahead_of_schedule / behind_schedule / on_track — by time-vs-progress ratio
    """
    now = now or datetime.now(tz=UTC)
    weeks_elapsed = max(0, int((now - t.set_at).days // 7))
    baseline_1rm = t.baseline_1rm or 0.0
    target_1rm = t.target_1rm
    current_1rm = current.one_rm  # may be None

    target_reps = t.target_reps_min or t.target_reps_max

    # No working set observed yet for this exercise.
    if current_1rm is None or current_1rm == 0:
        return TargetProgress(
            exercise_template_id=t.exercise_template_id,
            exercise_title=t.exercise_title,
            workout_day=t.workout_day,
            baseline=CurrentBest(
                weight_kg=t.baseline_weight_kg,
                reps=t.baseline_reps,
                one_rm=t.baseline_1rm,
            ),
            current=current,
            target_weight_kg_min=t.target_weight_kg_min,
            target_weight_kg_max=t.target_weight_kg_max,
            target_reps=target_reps,
            target_1rm=t.target_1rm,
            progress_pct=0.0,
            weeks_elapsed=weeks_elapsed,
            weeks_estimated_max=t.estimated_weeks_max,
            status="calibrating",
        )

    # Compute progress (signed — allow negative when below baseline).
    if target_1rm is None or target_1rm <= baseline_1rm:
        progress_pct = 0.0
    else:
        gained = current_1rm - baseline_1rm
        needed = float(target_1rm) - baseline_1rm
        progress_pct = round(max(-100.0, min(150.0, (gained / needed) * 100)), 1)

    achieved = target_1rm is not None and current_1rm >= float(target_1rm)
    weeks_max = t.estimated_weeks_max
    status: ProgressStatus
    if achieved:
        status = "achieved"
    elif current_1rm < baseline_1rm:
        status = "below_baseline"
    elif weeks_max is None:
        status = "on_track"
    elif weeks_elapsed > weeks_max:
        status = "expired"
    else:
        time_ratio = weeks_elapsed / weeks_max if weeks_max else 0.0
        prog_ratio = progress_pct / 100
        if time_ratio - prog_ratio > 0.15:
            status = "behind_schedule"
        elif prog_ratio - time_ratio > 0.15:
            status = "ahead_of_schedule"
        else:
            status = "on_track"

    return TargetProgress(
        exercise_template_id=t.exercise_template_id,
        exercise_title=t.exercise_title,
        workout_day=t.workout_day,
        baseline=CurrentBest(
            weight_kg=t.baseline_weight_kg,
            reps=t.baseline_reps,
            one_rm=t.baseline_1rm,
        ),
        current=current,
        target_weight_kg_min=t.target_weight_kg_min,
        target_weight_kg_max=t.target_weight_kg_max,
        target_reps=target_reps,
        target_1rm=t.target_1rm,
        progress_pct=progress_pct,
        weeks_elapsed=weeks_elapsed,
        weeks_estimated_max=weeks_max,
        status=status,
    )
