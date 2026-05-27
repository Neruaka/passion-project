"""Analysis runner — bridges DB I/O with the pure detection/aggregation services.

Called by the nightly Celery job (`tasks.nightly_analysis`) and also
on-demand by the API where a fresh recompute is cheap.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.analysis import (
    ExerciseAnalysisRepository,
    ExerciseTargetRepository,
    MonthlyStatsRepository,
    PersonalRecordRepository,
    TrainingContextRepository,
    WeeklyStatsRepository,
    load_all_set_contexts,
)
from src.services.fitness.plateau import (
    TargetSchedule,
    detect_behind_schedule,
    detect_plateaus,
    detect_regressions,
    detect_stalls,
    sessions_from_sets,
)
from src.services.fitness.pr_detection import (
    NewPR,
    SetContext,
    _is_working_set,
    detect_all_prs,
    estimate_one_rep_max,
)
from src.services.fitness.recovery import MuscleHit, compute_muscle_statuses
from src.services.fitness.stats import (
    ExerciseAggInput,
    WorkoutAggInput,
    aggregate_period,
    month_bounds,
    week_bounds,
)
from src.services.fitness.targets import (
    CurrentBest,
    TargetInput,
    TargetProgress,
    compute_target_progress,
)

logger = structlog.get_logger(__name__)


def _is_retired(exercise_title: str, retired: list[str]) -> bool:
    """Case-insensitive substring match (e.g. 'Squat (Barbell)' matches 'Squat (Barre)' loosely)."""
    if not retired or not exercise_title:
        return False
    lo = exercise_title.lower()
    return any(r.lower() in lo or lo in r.lower() for r in retired)


def _filter_retired(findings: list[Any], retired: list[str]) -> list[Any]:
    """Drop findings whose exercise_title matches a retired exercise."""
    if not retired:
        return findings
    return [f for f in findings if not _is_retired(f.exercise_title, retired)]


@dataclass(slots=True)
class AnalysisStats:
    new_prs: int = 0
    plateau_findings: int = 0
    weekly_rows_upserted: int = 0
    monthly_rows_upserted: int = 0
    duration_ms: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _exercise_key(s: SetContext) -> str:
    return s.exercise_template_id or f"_{s.exercise_title.lower().strip()}"


def _current_best_1rms(sets: list[SetContext]) -> dict[str, float]:
    """For each exercise key, the best Epley 1RM observed in working sets."""
    best: dict[str, float] = {}
    for s in sets:
        if not _is_working_set(s):
            continue
        assert s.weight_kg is not None and s.reps is not None
        one_rm = estimate_one_rep_max(s.weight_kg, s.reps)
        key = _exercise_key(s)
        if one_rm > best.get(key, 0.0):
            best[key] = one_rm
    return best


def _sets_to_aggregate_input(sets: list[SetContext]) -> list[WorkoutAggInput]:
    """Pivot SetContexts to per-workout structure required by stats.aggregate_period."""
    by_workout: dict[Any, dict[str, Any]] = {}
    for s in sets:
        if s.workout_id is None:
            continue
        w = by_workout.setdefault(
            s.workout_id,
            {
                "workout_id": str(s.workout_id),
                "start_time": s.achieved_at,
                "duration_minutes": 0,  # unknown at set level
                "total_volume_kg": 0.0,
                "exercises": {},
            },
        )
        ex_key = (s.exercise_template_id, s.exercise_title, s.primary_muscle_group)
        ex = w["exercises"].setdefault(
            ex_key,
            ExerciseAggInput(
                exercise_template_id=s.exercise_template_id,
                exercise_title=s.exercise_title,
                primary_muscle_group=s.primary_muscle_group,
                sets=[],
            ),
        )
        ex.sets.append((s.weight_kg, s.reps, s.set_type))
        if s.set_type not in {"warmup", "failure"} and s.weight_kg and s.reps:
            w["total_volume_kg"] += float(s.weight_kg) * float(s.reps)

    return [
        WorkoutAggInput(
            workout_id=w["workout_id"],
            start_time=w["start_time"],
            duration_minutes=w["duration_minutes"],
            total_volume_kg=round(w["total_volume_kg"], 2),
            pr_count=0,
            exercises=list(w["exercises"].values()),
        )
        for w in by_workout.values()
    ]


def _sets_to_muscle_hits(sets: list[SetContext]) -> list[MuscleHit]:
    by_session: dict[tuple[str, Any], float] = defaultdict(float)
    last_time: dict[tuple[str, Any], datetime] = {}
    for s in sets:
        if not _is_working_set(s) or not s.primary_muscle_group:
            continue
        assert s.weight_kg is not None and s.reps is not None
        composite = (s.primary_muscle_group, s.workout_id)
        by_session[composite] += float(s.weight_kg) * float(s.reps)
        last_time[composite] = s.achieved_at
    return [
        MuscleHit(muscle_group=g, achieved_at=last_time[k], volume_kg=v)
        for k, v in by_session.items()
        for g in [k[0]]
    ]


# ----- Main orchestrator ------------------------------------------------------


async def run_nightly_analysis(session: AsyncSession) -> AnalysisStats:
    """Full rescan: PRs + plateaus + weekly/monthly stats. Idempotent."""
    import time

    started = time.monotonic()
    stats = AnalysisStats()

    sets = await load_all_set_contexts(session)
    if not sets:
        logger.info("nightly_analysis_no_sets")
        stats.duration_ms = int((time.monotonic() - started) * 1000)
        return stats

    pr_repo = PersonalRecordRepository(session)
    ana_repo = ExerciseAnalysisRepository(session)
    weekly_repo = WeeklyStatsRepository(session)
    monthly_repo = MonthlyStatsRepository(session)
    ctx_repo = TrainingContextRepository(session)
    target_repo = ExerciseTargetRepository(session)

    # 1. PR detection (incremental — only beats current baselines)
    baselines = await pr_repo.all_baselines()
    new_prs: list[NewPR] = detect_all_prs(sets, baselines)
    stats.new_prs = await pr_repo.insert_many(new_prs)

    # 2. Plateau / stall / regression / behind-schedule
    ctx = await ctx_repo.get_singleton()
    phase = ctx.phase if ctx else None
    retired: list[str] = list(ctx.retired_exercises) if ctx and ctx.retired_exercises else []
    sessions_by_exercise = sessions_from_sets(sets)
    findings = (
        detect_plateaus(sessions_by_exercise, phase=phase)
        + detect_stalls(sessions_by_exercise, phase=phase)
        + detect_regressions(sessions_by_exercise, phase=phase)
    )
    # Suppress findings on permanently retired exercises (US-013 + program policy).
    findings = _filter_retired(findings, retired)

    targets = await target_repo.list_active()
    target_schedules = [
        TargetSchedule(
            exercise_template_id=t.exercise_template_id,
            exercise_title=t.exercise_title or "Unknown",
            set_at=t.set_at,
            estimated_weeks_max=t.estimated_weeks_max,
            target_1rm_estimate=float(t.target_1rm_estimate) if t.target_1rm_estimate else None,
        )
        for t in targets
        if t.exercise_title
    ]
    current_1rms = _current_best_1rms(sets)
    findings += detect_behind_schedule(target_schedules, current_1rms)

    await ana_repo.resolve_active()
    stats.plateau_findings = await ana_repo.insert_many(
        [
            {
                "exercise_template_id": f.exercise_template_id,
                "exercise_title": f.exercise_title,
                "analysis_type": f.analysis_type,
                "severity": f.severity,
                "details": f.details,
                "status": "active",
            }
            for f in findings
        ]
    )

    # 3. Weekly + monthly stats (current + previous week/month)
    agg_inputs = _sets_to_aggregate_input(sets)
    today = datetime.now(tz=UTC).date()
    weekly_targets = {today, today - timedelta(days=7)}
    monthly_targets = {today, (today.replace(day=1) - timedelta(days=1))}

    for ref in weekly_targets:
        start, end = week_bounds(ref)
        period = aggregate_period(agg_inputs, period="week", period_start=start, period_end=end)
        await weekly_repo.upsert(
            {
                "week_start": period.period_start,
                "total_sessions": period.total_sessions,
                "total_duration_minutes": period.total_duration_minutes,
                "total_volume_kg": period.total_volume_kg,
                "volume_per_muscle_group": period.volume_per_muscle_group,
                "pr_count": period.pr_count,
            }
        )
        stats.weekly_rows_upserted += 1

    for ref in monthly_targets:
        start, end = month_bounds(ref)
        period = aggregate_period(agg_inputs, period="month", period_start=start, period_end=end)
        await monthly_repo.upsert(
            {
                "month_start": period.period_start,
                "total_sessions": period.total_sessions,
                "total_duration_minutes": period.total_duration_minutes,
                "total_volume_kg": period.total_volume_kg,
                "volume_per_muscle_group": period.volume_per_muscle_group,
                "pr_count": period.pr_count,
            }
        )
        stats.monthly_rows_upserted += 1

    await session.commit()
    stats.duration_ms = int((time.monotonic() - started) * 1000)
    logger.info("nightly_analysis_complete", **stats.as_dict())
    return stats


# ----- Read helpers exposed to the API ----------------------------------------


async def compute_target_progress_for_all(session: AsyncSession) -> list[TargetProgress]:
    target_repo = ExerciseTargetRepository(session)
    targets = await target_repo.list_active()
    sets = await load_all_set_contexts(session)
    current_1rms = _current_best_1rms(sets)
    # Also need current top weight/reps per exercise
    best_by_key: dict[str, tuple[float, int]] = {}
    for s in sets:
        if not _is_working_set(s):
            continue
        assert s.weight_kg is not None and s.reps is not None
        key = _exercise_key(s)
        prev = best_by_key.get(key)
        one_rm = estimate_one_rep_max(s.weight_kg, s.reps)
        prev_one_rm = estimate_one_rep_max(prev[0], prev[1]) if prev else 0.0
        if one_rm > prev_one_rm:
            best_by_key[key] = (s.weight_kg, s.reps)

    progresses: list[TargetProgress] = []
    for t in targets:
        if not t.exercise_title:
            continue
        key = t.exercise_template_id or f"_{t.exercise_title.lower().strip()}"
        wt_reps = best_by_key.get(key)
        current = CurrentBest(
            weight_kg=wt_reps[0] if wt_reps else None,
            reps=wt_reps[1] if wt_reps else None,
            one_rm=current_1rms.get(key),
        )
        progresses.append(
            compute_target_progress(
                TargetInput(
                    exercise_template_id=t.exercise_template_id,
                    exercise_title=t.exercise_title,
                    workout_day=t.workout_day,
                    set_at=t.set_at,
                    baseline_weight_kg=float(t.baseline_weight_kg)
                    if t.baseline_weight_kg
                    else None,
                    baseline_reps=t.baseline_reps,
                    baseline_1rm=float(t.baseline_1rm_estimate)
                    if t.baseline_1rm_estimate
                    else None,
                    target_weight_kg_min=float(t.target_weight_kg_min)
                    if t.target_weight_kg_min
                    else None,
                    target_weight_kg_max=float(t.target_weight_kg_max)
                    if t.target_weight_kg_max
                    else None,
                    target_reps_min=t.target_reps_min,
                    target_reps_max=t.target_reps_max,
                    target_1rm=float(t.target_1rm_estimate) if t.target_1rm_estimate else None,
                    estimated_weeks_min=t.estimated_weeks_min,
                    estimated_weeks_max=t.estimated_weeks_max,
                    status=t.status,
                ),
                current,
            )
        )
    return progresses


async def compute_muscle_recovery(session: AsyncSession) -> list[dict[str, Any]]:
    sets = await load_all_set_contexts(session)
    hits = _sets_to_muscle_hits(sets)
    statuses = compute_muscle_statuses(hits)
    return [
        {
            "muscle_group": s.muscle_group,
            "recovery_state": s.recovery_state,
            "days_since_last_trained": s.days_since_last_trained,
            "recovery_left_days": s.recovery_left_days,
            "volume_last_7d": s.volume_last_7d,
            "frequency_last_30d": s.frequency_last_30d,
            "flag": s.flag,
        }
        for s in statuses
    ]


async def get_period_stats(session: AsyncSession, *, period: str, ref_date: date) -> dict[str, Any]:
    sets = await load_all_set_contexts(session)
    agg_inputs = _sets_to_aggregate_input(sets)
    if period == "month":
        start, end = month_bounds(ref_date)
    else:
        start, end = week_bounds(ref_date)
    period_stats = aggregate_period(agg_inputs, period=period, period_start=start, period_end=end)
    return {
        "period": period_stats.period,
        "period_start": period_stats.period_start.isoformat(),
        "period_end": period_stats.period_end.isoformat(),
        "total_sessions": period_stats.total_sessions,
        "total_duration_minutes": period_stats.total_duration_minutes,
        "total_volume_kg": period_stats.total_volume_kg,
        "volume_by_muscle": period_stats.volume_per_muscle_group,
        "pr_count": period_stats.pr_count,
        "sessions_by_day": period_stats.sessions_by_day,
        "top_exercises": [{"title": t, "volume_kg": v} for t, v in period_stats.top_exercises],
    }
