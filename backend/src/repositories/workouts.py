"""Workout, exercise template, and sync-state repositories (Sprint 1)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from src.models.workouts import (
    ExerciseTemplate,
    SyncState,
    Workout,
    WorkoutExercise,
    WorkoutSet,
)
from src.repositories.base import BaseRepository


@dataclass(slots=True)
class WorkoutListFilters:
    """Filters for GET /workouts (US-010)."""

    from_date: datetime | None = None
    to_date: datetime | None = None
    muscle_group: str | None = None
    exercise_template_id: str | None = None


@dataclass(slots=True)
class UpsertResult:
    """Outcome of a workout upsert (telemetry-friendly)."""

    workout: Workout
    was_new: bool


class ExerciseTemplateRepository(BaseRepository[ExerciseTemplate]):
    """Hevy exercise template catalogue (PK = hevy_id)."""

    model = ExerciseTemplate

    async def upsert_many(self, templates: list[dict[str, Any]]) -> int:
        """Bulk UPSERT by hevy_id. Returns the row count touched."""
        if not templates:
            return 0
        stmt = pg_insert(ExerciseTemplate).values(templates)
        update_cols = {
            "title": stmt.excluded.title,
            "primary_muscle_group": stmt.excluded.primary_muscle_group,
            "secondary_muscle_groups": stmt.excluded.secondary_muscle_groups,
            "equipment": stmt.excluded.equipment,
            "exercise_type": stmt.excluded.exercise_type,
        }
        stmt = stmt.on_conflict_do_update(index_elements=["hevy_id"], set_=update_cols)
        result = await self.session.execute(stmt)
        await self.session.flush()
        # Bulk UPSERT bypasses the identity map → expire so subsequent queries
        # re-load the fresh row instead of returning the cached stale one.
        self.session.expire_all()
        return result.rowcount or 0  # type: ignore[attr-defined]

    async def get_by_hevy_id(self, hevy_id: str) -> ExerciseTemplate | None:
        return await self.session.get(ExerciseTemplate, hevy_id)


class WorkoutRepository(BaseRepository[Workout]):
    """CRUD + UPSERT for workouts (with embedded exercises and sets)."""

    model = Workout

    async def get_by_hevy_id(self, hevy_id: str) -> Workout | None:
        stmt = select(Workout).where(Workout.hevy_id == hevy_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_detail(self, workout_id: UUID) -> Workout | None:
        """Eager-load exercises and sets for the detail endpoint."""
        stmt = (
            select(Workout)
            .where(Workout.id == workout_id)
            .options(selectinload(Workout.exercises).selectinload(WorkoutExercise.sets))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_workout(
        self,
        *,
        workout_data: dict[str, Any],
        exercises_data: list[dict[str, Any]],
    ) -> UpsertResult:
        """Idempotent UPSERT by hevy_id (US-008 scenario 3).

        Strategy: delete-then-recreate via ORM. Cascade removes the old
        exercises/sets; a fresh tree is then inserted. Simpler than column-by-
        column diffing and fast enough for ~weekly workout volumes.
        """
        existing = await self.get_by_hevy_id(workout_data["hevy_id"])
        was_new = existing is None
        if existing is not None:
            await self.session.delete(existing)
            await self.session.flush()

        workout = Workout(**workout_data)
        for ex in exercises_data:
            sets_data = ex.pop("sets", [])
            wex = WorkoutExercise(**ex)
            for s in sets_data:
                wex.sets.append(WorkoutSet(**s))
            workout.exercises.append(wex)

        self.session.add(workout)
        await self.session.flush()
        return UpsertResult(workout=workout, was_new=was_new)

    async def list_paginated(
        self,
        filters: WorkoutListFilters,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Workout], int]:
        """Return (items, total_count) — paginated, newest first (US-010)."""
        page_size = min(max(page_size, 1), 100)
        page = max(page, 1)

        base = select(Workout)
        count_base = select(func.count()).select_from(Workout)

        if filters.from_date is not None:
            base = base.where(Workout.start_time >= filters.from_date)
            count_base = count_base.where(Workout.start_time >= filters.from_date)
        if filters.to_date is not None:
            base = base.where(Workout.start_time <= filters.to_date)
            count_base = count_base.where(Workout.start_time <= filters.to_date)
        if filters.muscle_group or filters.exercise_template_id:
            base = base.join(Workout.exercises)
            count_base = count_base.join(WorkoutExercise, WorkoutExercise.workout_id == Workout.id)
            if filters.exercise_template_id is not None:
                base = base.where(
                    WorkoutExercise.exercise_template_id == filters.exercise_template_id
                )
                count_base = count_base.where(
                    WorkoutExercise.exercise_template_id == filters.exercise_template_id
                )
            if filters.muscle_group is not None:
                base = base.join(
                    ExerciseTemplate,
                    WorkoutExercise.exercise_template_id == ExerciseTemplate.hevy_id,
                ).where(ExerciseTemplate.primary_muscle_group == filters.muscle_group)
                count_base = count_base.join(
                    ExerciseTemplate,
                    WorkoutExercise.exercise_template_id == ExerciseTemplate.hevy_id,
                ).where(ExerciseTemplate.primary_muscle_group == filters.muscle_group)
            base = base.distinct()

        offset = (page - 1) * page_size
        items_stmt = base.order_by(desc(Workout.start_time)).limit(page_size).offset(offset)
        items_result = await self.session.execute(items_stmt)
        items = items_result.scalars().unique().all()

        total_result = await self.session.execute(count_base)
        total = total_result.scalar_one()
        return items, int(total)


class SyncStateRepository(BaseRepository[SyncState]):
    """Per-service sync state (last_successful_sync, bootstrap_completed, errors)."""

    model = SyncState

    async def get_or_create(self, service: str) -> SyncState:
        stmt = select(SyncState).where(SyncState.service == service)
        result = await self.session.execute(stmt)
        state = result.scalar_one_or_none()
        if state is None:
            state = SyncState(service=service)
            self.session.add(state)
            await self.session.flush()
        return state

    async def mark_success(self, service: str, *, completed_bootstrap: bool = False) -> None:
        state = await self.get_or_create(service)
        state.last_successful_sync = datetime.now(tz=UTC)
        state.last_error = None
        state.last_error_at = None
        if completed_bootstrap:
            state.bootstrap_completed = True
        await self.session.flush()

    async def mark_error(self, service: str, message: str) -> None:
        state = await self.get_or_create(service)
        state.last_error = message[:500]
        state.last_error_at = datetime.now(tz=UTC)
        await self.session.flush()
