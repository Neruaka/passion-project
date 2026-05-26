"""Workouts endpoints (US-009, US-010). See API_CONTRACTS.md > WORKOUTS.

GET    /workouts            — paginated list with filters
GET    /workouts/{id}       — detail with exercises + sets
POST   /workouts/sync       — manual sync trigger (Celery job)
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import PrincipalDep
from src.db.session import get_session
from src.models.workouts import Workout
from src.repositories.workouts import WorkoutListFilters, WorkoutRepository
from src.schemas.workouts import (
    ExerciseDetail,
    SetDetail,
    SyncTriggeredResponse,
    WorkoutDetail,
    WorkoutListResponse,
    WorkoutSummary,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _duration_minutes(w: Workout) -> int:
    if w.end_time is None:
        return 0
    return max(0, int((w.end_time - w.start_time).total_seconds() // 60))


def _to_summary(w: Workout) -> WorkoutSummary:
    return WorkoutSummary(
        id=w.id,
        hevy_id=w.hevy_id,
        title=w.title,
        start_time=w.start_time,
        duration_minutes=_duration_minutes(w),
        exercise_count=len(w.exercises) if "exercises" in w.__dict__ else 0,
        total_volume_kg=float(w.total_volume_kg) if w.total_volume_kg is not None else None,
        has_prs=False,  # PR detection arrives in sprint 2 (US-012)
    )


def _to_detail(w: Workout) -> WorkoutDetail:
    return WorkoutDetail(
        id=w.id,
        hevy_id=w.hevy_id,
        title=w.title,
        description=w.description,
        start_time=w.start_time,
        end_time=w.end_time,
        duration_minutes=_duration_minutes(w),
        total_volume_kg=float(w.total_volume_kg) if w.total_volume_kg is not None else None,
        exercises=[
            ExerciseDetail(
                title=ex.title,
                exercise_template_id=ex.exercise_template_id,
                order_index=ex.order_index,
                notes=ex.notes,
                sets=[
                    SetDetail(
                        order_index=s.order_index,
                        set_type=s.set_type,
                        weight_kg=float(s.weight_kg) if s.weight_kg is not None else None,
                        reps=s.reps,
                        rpe=float(s.rpe) if s.rpe is not None else None,
                    )
                    for s in ex.sets
                ],
            )
            for ex in sorted(w.exercises, key=lambda e: e.order_index)
        ],
    )


@router.get("", response_model=WorkoutListResponse)
async def list_workouts(
    session: SessionDep,
    _user: PrincipalDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    from_date: Annotated[datetime | None, Query()] = None,
    to_date: Annotated[datetime | None, Query()] = None,
    muscle_group: Annotated[str | None, Query()] = None,
    exercise: Annotated[str | None, Query(description="Filter by exercise_template_id")] = None,
) -> WorkoutListResponse:
    filters = WorkoutListFilters(
        from_date=from_date,
        to_date=to_date,
        muscle_group=muscle_group,
        exercise_template_id=exercise,
    )
    items, total = await WorkoutRepository(session).list_paginated(
        filters, page=page, page_size=page_size
    )
    return WorkoutListResponse(
        items=[_to_summary(w) for w in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/{workout_id}", response_model=WorkoutDetail)
async def get_workout(
    workout_id: UUID,
    session: SessionDep,
    _user: PrincipalDep,
) -> WorkoutDetail:
    workout = await WorkoutRepository(session).get_detail(workout_id)
    if workout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="workout_not_found")
    return _to_detail(workout)


@router.post(
    "/sync",
    response_model=SyncTriggeredResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_sync(_user: PrincipalDep) -> SyncTriggeredResponse:
    """Enqueue a manual Hevy sync (US-009 sc.1).

    TODO(sprint-1+): rate-limit at 30s/IP via Redis (US-009 sc.2).
    """
    # Lazy import to avoid Celery initialisation cost during API tests that
    # don't exercise this endpoint.
    from src.jobs.tasks import sync_hevy_workouts

    async_result = sync_hevy_workouts.delay()
    return SyncTriggeredResponse(
        job_id=str(async_result.id),
        message="Hevy sync queued — check Activity Log for completion.",
    )
