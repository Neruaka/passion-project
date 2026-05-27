"""Personal Record detection (US-012, Sprint 2).

Pure business logic: given workout sets, detect the 4 PR types:
  1. one_rep_max         — best Epley-estimated 1RM per exercise
  2. reps_at_load        — most reps at a weight bucket (5kg granularity)
  3. session_volume      — highest single-session volume per exercise
  4. muscle_group_volume — highest weekly volume per muscle group

The functions in this module are SIDE-EFFECT FREE (no DB, no LLM). They take
plain dataclasses and return plain dataclasses → unit-testable to ~100%
(NFR-TEST-002).

A separate orchestrator (`run_pr_detection`) lives in
`services/fitness/analysis_runner.py` to wire DB I/O.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Literal
from uuid import UUID

PrType = Literal["one_rep_max", "reps_at_load", "session_volume", "muscle_group_volume"]

# Set types we EXCLUDE from PR detection (warmup, intentional failure, dropsets
# don't count as real working performance).
_EXCLUDED_SET_TYPES: frozenset[str] = frozenset({"warmup", "failure", "dropset"})


def estimate_one_rep_max(weight_kg: float, reps: int) -> float:
    """Epley formula: 1RM = weight * (1 + reps / 30). Round to 0.1 kg."""
    if reps <= 0:
        raise ValueError("reps must be > 0")
    return round(weight_kg * (1 + reps / 30), 1)


def weight_bucket(weight_kg: float, granularity_kg: float = 5.0) -> str:
    """Round a weight DOWN to the nearest bucket for reps_at_load.

    Example: 82.5kg @ granularity 5 → "80kg".
    """
    bucket = int(weight_kg // granularity_kg) * int(granularity_kg)
    return f"{bucket}kg"


@dataclass(slots=True, frozen=True)
class SetContext:
    """A single working set with everything PR detection needs."""

    set_id: UUID | None
    workout_id: UUID | None
    achieved_at: datetime
    exercise_template_id: str | None
    exercise_title: str
    primary_muscle_group: str | None
    weight_kg: float | None
    reps: int | None
    set_type: str = "normal"


@dataclass(slots=True)
class NewPR:
    """A PR candidate produced by detection — ready to persist."""

    pr_type: PrType
    exercise_template_id: str | None
    exercise_title: str
    new_value: float
    old_value: float | None
    gain: float | None
    achieved_at: datetime
    workout_id: UUID | None = None
    workout_set_id: UUID | None = None
    bucket: str | None = None


@dataclass(slots=True)
class PRBaselines:
    """The 'best so far' across all 4 PR types, fed back into detection."""

    one_rep_max: dict[str, float] = field(default_factory=dict)  # by exercise_template_id-or-title
    reps_at_load: dict[tuple[str, str], int] = field(
        default_factory=dict
    )  # by (key, bucket) → reps
    session_volume: dict[str, float] = field(default_factory=dict)  # by exercise key
    muscle_group_volume: dict[tuple[str, date], float] = field(
        default_factory=dict
    )  # by (group, week_monday)


def _exercise_key(s: SetContext) -> str:
    """Stable key for grouping per exercise (FK first, fallback to title)."""
    return s.exercise_template_id or f"_{s.exercise_title.lower().strip()}"


def _is_working_set(s: SetContext) -> bool:
    return (
        s.set_type not in _EXCLUDED_SET_TYPES
        and s.weight_kg is not None
        and s.reps is not None
        and s.weight_kg > 0
        and s.reps > 0
    )


def _week_monday(d: datetime) -> date:
    """The Monday of the ISO week containing d (timezone-agnostic)."""
    day = d.date()
    return day - timedelta(days=day.weekday())


# ----- Type 1: one-rep-max PRs --------------------------------------------------


def detect_one_rep_max_prs(sets: list[SetContext], baselines: PRBaselines) -> list[NewPR]:
    """For each working set, compute Epley 1RM; emit if > the prior best for the exercise."""
    new_prs: list[NewPR] = []
    # Track best within this batch so we only emit the FINAL best, not every monotonic step.
    best_in_batch: dict[str, tuple[float, SetContext]] = {}
    for s in sorted(sets, key=lambda x: x.achieved_at):
        if not _is_working_set(s):
            continue
        # type narrowing
        assert s.weight_kg is not None and s.reps is not None
        one_rm = estimate_one_rep_max(s.weight_kg, s.reps)
        key = _exercise_key(s)
        old = max(baselines.one_rep_max.get(key, 0.0), best_in_batch.get(key, (0.0, s))[0])
        if one_rm > old:
            best_in_batch[key] = (one_rm, s)
    for key, (one_rm, s) in best_in_batch.items():
        prior = baselines.one_rep_max.get(key)
        new_prs.append(
            NewPR(
                pr_type="one_rep_max",
                exercise_template_id=s.exercise_template_id,
                exercise_title=s.exercise_title,
                new_value=one_rm,
                old_value=prior,
                gain=(one_rm - prior) if prior is not None else None,
                achieved_at=s.achieved_at,
                workout_id=s.workout_id,
                workout_set_id=s.set_id,
            )
        )
    return new_prs


# ----- Type 2: reps-at-load PRs -------------------------------------------------


def detect_reps_at_load_prs(
    sets: list[SetContext],
    baselines: PRBaselines,
    *,
    bucket_kg: float = 5.0,
) -> list[NewPR]:
    """For each (exercise, weight_bucket), emit a PR if the set's reps beat the prior best."""
    new_prs: list[NewPR] = []
    best_in_batch: dict[tuple[str, str], tuple[int, SetContext]] = {}
    for s in sorted(sets, key=lambda x: x.achieved_at):
        if not _is_working_set(s):
            continue
        assert s.weight_kg is not None and s.reps is not None
        key = _exercise_key(s)
        bucket = weight_bucket(s.weight_kg, bucket_kg)
        composite = (key, bucket)
        prior = baselines.reps_at_load.get(composite, 0)
        running = best_in_batch.get(composite, (prior, s))[0]
        if s.reps > running:
            best_in_batch[composite] = (s.reps, s)
    for (key, bucket), (reps, s) in best_in_batch.items():
        prior_reps: int | None = baselines.reps_at_load.get((key, bucket))
        new_prs.append(
            NewPR(
                pr_type="reps_at_load",
                exercise_template_id=s.exercise_template_id,
                exercise_title=s.exercise_title,
                new_value=float(reps),
                old_value=float(prior_reps) if prior_reps is not None else None,
                gain=float(reps - prior_reps) if prior_reps is not None else None,
                achieved_at=s.achieved_at,
                workout_id=s.workout_id,
                workout_set_id=s.set_id,
                bucket=bucket,
            )
        )
    return new_prs


# ----- Type 3: session-volume PRs ----------------------------------------------


def detect_session_volume_prs(sets: list[SetContext], baselines: PRBaselines) -> list[NewPR]:
    """Highest single-session volume per exercise."""
    by_session: dict[tuple[UUID | None, str], float] = defaultdict(float)
    by_session_meta: dict[tuple[UUID | None, str], SetContext] = {}
    for s in sets:
        if not _is_working_set(s):
            continue
        assert s.weight_kg is not None and s.reps is not None
        composite = (s.workout_id, _exercise_key(s))
        by_session[composite] += float(s.weight_kg) * float(s.reps)
        by_session_meta.setdefault(composite, s)

    new_prs: list[NewPR] = []
    best_in_batch: dict[str, tuple[float, SetContext]] = {}
    for (_wid, key), volume in by_session.items():
        rep_meta = by_session_meta[(_wid, key)]
        prior = baselines.session_volume.get(key, 0.0)
        running = best_in_batch.get(key, (prior, rep_meta))[0]
        if volume > running:
            best_in_batch[key] = (volume, rep_meta)
    for key, (volume, rep_meta) in best_in_batch.items():
        prior_volume: float | None = baselines.session_volume.get(key)
        new_prs.append(
            NewPR(
                pr_type="session_volume",
                exercise_template_id=rep_meta.exercise_template_id,
                exercise_title=rep_meta.exercise_title,
                new_value=round(volume, 2),
                old_value=round(prior_volume, 2) if prior_volume is not None else None,
                gain=round(volume - prior_volume, 2) if prior_volume is not None else None,
                achieved_at=rep_meta.achieved_at,
                workout_id=rep_meta.workout_id,
            )
        )
    return new_prs


# ----- Type 4: muscle-group weekly-volume PRs ----------------------------------


def detect_muscle_group_volume_prs(sets: list[SetContext], baselines: PRBaselines) -> list[NewPR]:
    """Highest weekly volume per primary muscle group."""
    by_week: dict[tuple[str, date], float] = defaultdict(float)
    last_set: dict[tuple[str, date], SetContext] = {}
    for s in sets:
        if not _is_working_set(s) or not s.primary_muscle_group:
            continue
        assert s.weight_kg is not None and s.reps is not None
        composite = (s.primary_muscle_group, _week_monday(s.achieved_at))
        by_week[composite] += float(s.weight_kg) * float(s.reps)
        last_set[composite] = s

    new_prs: list[NewPR] = []
    best_in_batch: dict[str, tuple[float, SetContext, date]] = {}
    for (group, week_start), volume in by_week.items():
        prior = baselines.muscle_group_volume.get((group, week_start), 0.0)
        # We compare against the all-time best for THIS group, regardless of week.
        all_time_prior = max(
            [v for (g, _), v in baselines.muscle_group_volume.items() if g == group] + [prior]
        )
        running = best_in_batch.get(
            group, (all_time_prior, last_set[(group, week_start)], week_start)
        )[0]
        if volume > running:
            best_in_batch[group] = (volume, last_set[(group, week_start)], week_start)
    for group, (volume, rep_meta, week_start) in best_in_batch.items():
        prior_candidates = [v for (g, _), v in baselines.muscle_group_volume.items() if g == group]
        prior_group: float | None = max(prior_candidates) if prior_candidates else None
        new_prs.append(
            NewPR(
                pr_type="muscle_group_volume",
                exercise_template_id=None,
                exercise_title=group,
                new_value=round(volume, 2),
                old_value=round(prior_group, 2) if prior_group is not None else None,
                gain=round(volume - prior_group, 2) if prior_group is not None else None,
                achieved_at=rep_meta.achieved_at,
                workout_id=None,
                bucket=week_start.isoformat(),
            )
        )
    return new_prs


# ----- Orchestrator (pure) ------------------------------------------------------


def detect_all_prs(sets: list[SetContext], baselines: PRBaselines) -> list[NewPR]:
    """Run all 4 detectors on the same set batch."""
    return (
        detect_one_rep_max_prs(sets, baselines)
        + detect_reps_at_load_prs(sets, baselines)
        + detect_session_volume_prs(sets, baselines)
        + detect_muscle_group_volume_prs(sets, baselines)
    )
