"""Analysis endpoints (Sprint 2). See API_CONTRACTS.md > ANALYSIS.

GET  /analysis/prs                       — paginated PR list
GET  /analysis/plateaus                  — active plateau / regression / behind_schedule findings
GET  /analysis/targets                   — TargetProgress for each active target
GET  /analysis/muscle-status             — per-muscle recovery state
GET  /analysis/stats                     — weekly / monthly aggregates
GET  /analysis/exercise/{id}/progression — per-exercise progression series
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import PrincipalDep
from src.db.session import get_session
from src.models.analysis import ExerciseAnalysis, PersonalRecord
from src.repositories.analysis import (
    ExerciseAnalysisRepository,
    PersonalRecordRepository,
    load_all_set_contexts,
)
from src.schemas.analysis import (
    MuscleStatusOut,
    PlateauAnalysis,
    PRListResponse,
    ProgressionPoint,
    ProgressionResponse,
    PRRecord,
    StatsResponse,
    TargetPoint,
    TargetProgressOut,
)
from src.services.fitness.analysis_runner import (
    compute_muscle_recovery,
    compute_target_progress_for_all,
    get_period_stats,
)
from src.services.fitness.pr_detection import _is_working_set, estimate_one_rep_max

router = APIRouter(prefix="/analysis", tags=["analysis"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/prs", response_model=PRListResponse)
async def list_prs(
    session: SessionDep,
    _user: PrincipalDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    pr_type: Annotated[str | None, Query()] = None,
    exercise: Annotated[str | None, Query(description="Filter by exercise_template_id")] = None,
) -> PRListResponse:
    items, total = await PersonalRecordRepository(session).list_paginated(
        page=page, page_size=page_size, pr_type=pr_type, exercise_template_id=exercise
    )
    return PRListResponse(
        items=[PRRecord.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/plateaus", response_model=list[PlateauAnalysis])
async def list_plateaus(
    session: SessionDep,
    _user: PrincipalDep,
    analysis_type: Annotated[str | None, Query()] = None,
) -> list[PlateauAnalysis]:
    rows = await ExerciseAnalysisRepository(session).list_active(analysis_type=analysis_type)
    return [PlateauAnalysis.model_validate(r) for r in rows]


@router.get("/targets", response_model=list[TargetProgressOut])
async def list_targets(session: SessionDep, _user: PrincipalDep) -> list[TargetProgressOut]:
    progresses = await compute_target_progress_for_all(session)
    return [
        TargetProgressOut(
            exercise_template_id=p.exercise_template_id,
            exercise_title=p.exercise_title,
            workout_day=p.workout_day,
            baseline=TargetPoint(
                weight_kg=p.baseline.weight_kg,
                reps=p.baseline.reps,
                one_rm_estimate=p.baseline.one_rm,
            ),
            current=TargetPoint(
                weight_kg=p.current.weight_kg,
                reps=p.current.reps,
                one_rm_estimate=p.current.one_rm,
            ),
            target_weight_kg_min=p.target_weight_kg_min,
            target_weight_kg_max=p.target_weight_kg_max,
            target_reps=p.target_reps,
            target_1rm=p.target_1rm,
            progress_pct=p.progress_pct,
            weeks_elapsed=p.weeks_elapsed,
            weeks_estimated_max=p.weeks_estimated_max,
            status=p.status,
        )
        for p in progresses
    ]


@router.get("/muscle-status", response_model=list[MuscleStatusOut])
async def muscle_status(session: SessionDep, _user: PrincipalDep) -> list[MuscleStatusOut]:
    rows = await compute_muscle_recovery(session)
    return [MuscleStatusOut(**r) for r in rows]


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    session: SessionDep,
    _user: PrincipalDep,
    period: Annotated[str, Query(pattern="^(week|month)$")] = "week",
    ref_date: Annotated[date | None, Query()] = None,
) -> StatsResponse:
    ref = ref_date or datetime.now(tz=UTC).date()
    data = await get_period_stats(session, period=period, ref_date=ref)
    return StatsResponse(**data)


@router.get("/exercise/{exercise_id}/progression", response_model=ProgressionResponse)
async def exercise_progression(
    exercise_id: str,
    session: SessionDep,
    _user: PrincipalDep,
) -> ProgressionResponse:
    """Aggregated per-session series for an exercise (by exercise_template_id)."""
    sets = await load_all_set_contexts(session)
    sets = [s for s in sets if s.exercise_template_id == exercise_id and _is_working_set(s)]
    # Group by day → best 1RM + total volume
    by_day: dict[date, dict[str, float]] = defaultdict(lambda: {"one_rm": 0.0, "volume": 0.0})
    title = "Unknown"
    for s in sorted(sets, key=lambda x: x.achieved_at):
        assert s.weight_kg is not None and s.reps is not None
        title = s.exercise_title
        d = s.achieved_at.date()
        one_rm = estimate_one_rep_max(s.weight_kg, s.reps)
        by_day[d]["one_rm"] = max(by_day[d]["one_rm"], one_rm)
        by_day[d]["volume"] += float(s.weight_kg) * float(s.reps)
    data_points = [
        ProgressionPoint(date=d, one_rm_estimate=v["one_rm"], volume_kg=round(v["volume"], 2))
        for d, v in sorted(by_day.items())
    ]

    # Also pull PRs and active plateaus for this exercise
    prs_rows = (
        (
            await session.execute(
                select(PersonalRecord)
                .where(PersonalRecord.exercise_template_id == exercise_id)
                .order_by(PersonalRecord.achieved_at.desc())
                .limit(20)
            )
        )
        .scalars()
        .all()
    )
    plateaus_rows = (
        (
            await session.execute(
                select(ExerciseAnalysis)
                .where(
                    ExerciseAnalysis.exercise_template_id == exercise_id,
                    ExerciseAnalysis.status == "active",
                )
                .order_by(ExerciseAnalysis.created_at.desc())
            )
        )
        .scalars()
        .all()
    )

    return ProgressionResponse(
        exercise_title=title,
        exercise_template_id=exercise_id,
        data_points=data_points,
        prs=[
            {
                "pr_type": p.pr_type,
                "new_value": float(p.new_value),
                "achieved_at": p.achieved_at.isoformat(),
                "bucket": p.bucket,
            }
            for p in prs_rows
        ],
        plateaus=[
            {
                "analysis_type": pl.analysis_type,
                "severity": pl.severity,
                "details": pl.details,
                "created_at": pl.created_at.isoformat(),
            }
            for pl in plateaus_rows
        ],
    )
