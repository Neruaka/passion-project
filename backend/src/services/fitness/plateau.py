"""Plateau / regression / behind-schedule detection (US-013, Sprint 2).

Pure logic: takes per-exercise history + training context, returns
ExerciseAnalysis candidates.

Plateau heuristics (context-aware):
  * `plateau_official` — same top-set weight for >= N consecutive sessions
  * `plateau_stalled` — best 1RM hasn't increased in >= N sessions
  * `regression`      — recent best 1RM < older best 1RM by > threshold
  * `behind_schedule` — weeks_elapsed > weeks_estimated_max on the target

Tolerance is widened during cutting (you don't expect PRs on a deficit).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal

from src.services.fitness.pr_detection import (
    SetContext,
    _is_working_set,
    estimate_one_rep_max,
)

AnalysisType = Literal["plateau_official", "plateau_stalled", "regression", "behind_schedule"]
Severity = Literal["minor", "moderate", "major"]

# Tolerance windows by phase. Cutting = no PR expected → longer tolerance.
_PLATEAU_THRESHOLD_SESSIONS = {
    "cutting": 6,
    "maintenance": 4,
    "bulking": 3,
    "recomp": 5,
    None: 4,
}

_REGRESSION_PCT = {
    "cutting": 0.07,  # 7% drop during a cut is real
    "maintenance": 0.05,
    "bulking": 0.04,
    "recomp": 0.05,
    None: 0.05,
}


@dataclass(slots=True)
class ExerciseSession:
    """One session's top working set for an exercise (already aggregated)."""

    exercise_key: str
    exercise_title: str
    exercise_template_id: str | None
    achieved_at: datetime
    top_weight_kg: float
    top_reps: int

    @property
    def one_rm(self) -> float:
        return estimate_one_rep_max(self.top_weight_kg, self.top_reps)


@dataclass(slots=True)
class PlateauFinding:
    analysis_type: AnalysisType
    exercise_template_id: str | None
    exercise_title: str
    severity: Severity
    details: dict[str, Any] = field(default_factory=dict)


def sessions_from_sets(sets: list[SetContext]) -> dict[str, list[ExerciseSession]]:
    """Reduce raw sets to one top working set per (exercise, session-day)."""
    # Group sets by (exercise_key, session_day, achieved_at) and keep the heaviest.
    from collections import defaultdict

    grouped: dict[tuple[str, date], ExerciseSession] = {}
    for s in sets:
        if not _is_working_set(s):
            continue
        assert s.weight_kg is not None and s.reps is not None
        key = s.exercise_template_id or f"_{s.exercise_title.lower().strip()}"
        day = s.achieved_at.date()
        existing = grouped.get((key, day))
        # "Top set" = heaviest weight; ties broken by reps.
        if (
            existing is None
            or s.weight_kg > existing.top_weight_kg
            or (s.weight_kg == existing.top_weight_kg and s.reps > existing.top_reps)
        ):
            grouped[(key, day)] = ExerciseSession(
                exercise_key=key,
                exercise_title=s.exercise_title,
                exercise_template_id=s.exercise_template_id,
                achieved_at=s.achieved_at,
                top_weight_kg=float(s.weight_kg),
                top_reps=s.reps,
            )

    by_exercise: dict[str, list[ExerciseSession]] = defaultdict(list)
    for sess in grouped.values():
        by_exercise[sess.exercise_key].append(sess)
    for k in by_exercise:
        by_exercise[k].sort(key=lambda x: x.achieved_at)
    return dict(by_exercise)


def detect_plateaus(
    sessions_by_exercise: dict[str, list[ExerciseSession]],
    *,
    phase: str | None = None,
    threshold_sessions: int | None = None,
) -> list[PlateauFinding]:
    """Detect 'same top weight for N consecutive sessions' plateaus."""
    n = threshold_sessions or _PLATEAU_THRESHOLD_SESSIONS.get(phase, 4)
    findings: list[PlateauFinding] = []
    for _key, sessions in sessions_by_exercise.items():
        if len(sessions) < n:
            continue
        last = sessions[-n:]
        weights = {s.top_weight_kg for s in last}
        if len(weights) == 1:
            findings.append(
                PlateauFinding(
                    analysis_type="plateau_official",
                    exercise_template_id=last[-1].exercise_template_id,
                    exercise_title=last[-1].exercise_title,
                    severity="moderate" if n <= 4 else "minor",
                    details={
                        "consecutive_sessions": n,
                        "stuck_at_weight_kg": last[-1].top_weight_kg,
                        "phase": phase,
                    },
                )
            )
    return findings


def detect_stalls(
    sessions_by_exercise: dict[str, list[ExerciseSession]],
    *,
    phase: str | None = None,
    window_sessions: int = 4,
) -> list[PlateauFinding]:
    """Best 1RM didn't increase over the last `window_sessions`."""
    findings: list[PlateauFinding] = []
    for _key, sessions in sessions_by_exercise.items():
        if len(sessions) < window_sessions + 1:
            continue
        recent = sessions[-window_sessions:]
        previous = sessions[:-window_sessions]
        best_recent = max(s.one_rm for s in recent)
        best_prev = max(s.one_rm for s in previous) if previous else 0.0
        if best_recent <= best_prev:
            findings.append(
                PlateauFinding(
                    analysis_type="plateau_stalled",
                    exercise_template_id=recent[-1].exercise_template_id,
                    exercise_title=recent[-1].exercise_title,
                    severity="minor",
                    details={
                        "window_sessions": window_sessions,
                        "best_1rm_recent": best_recent,
                        "best_1rm_previous": best_prev,
                        "phase": phase,
                    },
                )
            )
    return findings


def detect_regressions(
    sessions_by_exercise: dict[str, list[ExerciseSession]],
    *,
    phase: str | None = None,
    lookback_days: int = 30,
    older_window_days: int = 60,
) -> list[PlateauFinding]:
    """Best 1RM in last `lookback_days` < best in older window by > threshold pct."""
    threshold = _REGRESSION_PCT.get(phase, 0.05)
    now = datetime.now(tz=UTC)
    recent_cutoff = now - timedelta(days=lookback_days)
    older_cutoff = now - timedelta(days=older_window_days)
    findings: list[PlateauFinding] = []
    for _key, sessions in sessions_by_exercise.items():
        recent = [s for s in sessions if s.achieved_at >= recent_cutoff]
        older = [s for s in sessions if older_cutoff <= s.achieved_at < recent_cutoff]
        if not recent or not older:
            continue
        best_recent = max(s.one_rm for s in recent)
        best_older = max(s.one_rm for s in older)
        drop_pct = (best_older - best_recent) / best_older if best_older else 0.0
        if drop_pct > threshold:
            findings.append(
                PlateauFinding(
                    analysis_type="regression",
                    exercise_template_id=recent[-1].exercise_template_id,
                    exercise_title=recent[-1].exercise_title,
                    severity="major" if drop_pct > 0.12 else "moderate",
                    details={
                        "best_1rm_recent": best_recent,
                        "best_1rm_older": best_older,
                        "drop_pct": round(drop_pct * 100, 1),
                        "threshold_pct": round(threshold * 100, 1),
                        "phase": phase,
                    },
                )
            )
    return findings


@dataclass(slots=True)
class TargetSchedule:
    """What we need from ExerciseTarget to compute behind_schedule."""

    exercise_template_id: str | None
    exercise_title: str
    set_at: datetime
    estimated_weeks_max: int | None
    target_1rm_estimate: float | None


def detect_behind_schedule(
    targets: list[TargetSchedule],
    current_1rms: dict[str, float],  # exercise_key → current best 1RM
) -> list[PlateauFinding]:
    """For each target: if weeks_elapsed > weeks_estimated_max and 1RM still below target → flag."""
    findings: list[PlateauFinding] = []
    now = datetime.now(tz=UTC)
    for t in targets:
        if t.estimated_weeks_max is None or t.target_1rm_estimate is None:
            continue
        weeks_elapsed = (now - t.set_at).days / 7
        if weeks_elapsed <= t.estimated_weeks_max:
            continue
        key = t.exercise_template_id or f"_{t.exercise_title.lower().strip()}"
        current = current_1rms.get(key, 0.0)
        if current < float(t.target_1rm_estimate):
            findings.append(
                PlateauFinding(
                    analysis_type="behind_schedule",
                    exercise_template_id=t.exercise_template_id,
                    exercise_title=t.exercise_title,
                    severity="moderate" if weeks_elapsed < t.estimated_weeks_max * 1.5 else "major",
                    details={
                        "weeks_elapsed": round(weeks_elapsed, 1),
                        "weeks_estimated_max": t.estimated_weeks_max,
                        "current_1rm": current,
                        "target_1rm": float(t.target_1rm_estimate),
                    },
                )
            )
    return findings
