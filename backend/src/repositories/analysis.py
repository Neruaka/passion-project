"""Repositories for Sprint 2: PRs, analysis findings, weekly/monthly stats,
training context + exercise targets.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.models.analysis import (
    ExerciseAnalysis,
    MonthlyStats,
    PersonalRecord,
    WeeklyStats,
)
from src.models.targets import ExerciseTarget, TrainingContext
from src.models.workouts import ExerciseTemplate, Workout, WorkoutExercise, WorkoutSet
from src.repositories.base import BaseRepository
from src.services.fitness.pr_detection import (
    NewPR,
    PRBaselines,
    SetContext,
    _week_monday,
)


class PersonalRecordRepository(BaseRepository[PersonalRecord]):
    model = PersonalRecord

    async def all_baselines(self) -> PRBaselines:
        """Load 'best so far' for each PR type from existing records."""
        stmt = select(PersonalRecord)
        rows = (await self.session.execute(stmt)).scalars().all()
        baselines = PRBaselines()
        for r in rows:
            key = r.exercise_template_id or f"_{(r.exercise_title or '').lower().strip()}"
            value = float(r.new_value)
            if r.pr_type == "one_rep_max":
                baselines.one_rep_max[key] = max(baselines.one_rep_max.get(key, 0.0), value)
            elif r.pr_type == "reps_at_load" and r.bucket:
                composite = (key, r.bucket)
                baselines.reps_at_load[composite] = max(
                    baselines.reps_at_load.get(composite, 0), int(value)
                )
            elif r.pr_type == "session_volume":
                baselines.session_volume[key] = max(baselines.session_volume.get(key, 0.0), value)
            elif r.pr_type == "muscle_group_volume" and r.bucket:
                try:
                    week_start = date.fromisoformat(r.bucket)
                except ValueError:
                    continue
                composite_mg = (r.exercise_title or "", week_start)
                baselines.muscle_group_volume[composite_mg] = max(
                    baselines.muscle_group_volume.get(composite_mg, 0.0), value
                )
        return baselines

    async def insert_many(self, prs: list[NewPR]) -> int:
        if not prs:
            return 0
        rows = [
            {
                "exercise_template_id": p.exercise_template_id,
                "exercise_title": p.exercise_title,
                "pr_type": p.pr_type,
                "new_value": p.new_value,
                "old_value": p.old_value,
                "gain": p.gain,
                "bucket": p.bucket,
                "workout_id": p.workout_id,
                "workout_set_id": p.workout_set_id,
                "achieved_at": p.achieved_at,
            }
            for p in prs
        ]
        stmt = pg_insert(PersonalRecord).values(rows)
        await self.session.execute(stmt)
        await self.session.flush()
        return len(rows)

    async def list_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        pr_type: str | None = None,
        exercise_template_id: str | None = None,
    ) -> tuple[Sequence[PersonalRecord], int]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        base = select(PersonalRecord)
        count_base = select(func.count()).select_from(PersonalRecord)
        if pr_type:
            base = base.where(PersonalRecord.pr_type == pr_type)
            count_base = count_base.where(PersonalRecord.pr_type == pr_type)
        if exercise_template_id:
            base = base.where(PersonalRecord.exercise_template_id == exercise_template_id)
            count_base = count_base.where(
                PersonalRecord.exercise_template_id == exercise_template_id
            )
        offset = (page - 1) * page_size
        items_stmt = base.order_by(desc(PersonalRecord.achieved_at)).limit(page_size).offset(offset)
        items = (await self.session.execute(items_stmt)).scalars().all()
        total = (await self.session.execute(count_base)).scalar_one()
        return items, int(total)


class ExerciseAnalysisRepository(BaseRepository[ExerciseAnalysis]):
    model = ExerciseAnalysis

    async def resolve_active(self, analysis_type: str | None = None) -> int:
        """Mark current active findings as resolved (we'll re-emit fresh ones)."""
        stmt = select(ExerciseAnalysis).where(ExerciseAnalysis.status == "active")
        if analysis_type is not None:
            stmt = stmt.where(ExerciseAnalysis.analysis_type == analysis_type)
        rows = (await self.session.execute(stmt)).scalars().all()
        now = datetime.now(tz=UTC)
        for r in rows:
            r.status = "resolved"
            r.resolved_at = now
        await self.session.flush()
        return len(rows)

    async def insert_many(self, findings: list[dict[str, Any]]) -> int:
        if not findings:
            return 0
        stmt = pg_insert(ExerciseAnalysis).values(findings)
        await self.session.execute(stmt)
        await self.session.flush()
        return len(findings)

    async def list_active(self, *, analysis_type: str | None = None) -> Sequence[ExerciseAnalysis]:
        stmt = select(ExerciseAnalysis).where(ExerciseAnalysis.status == "active")
        if analysis_type:
            stmt = stmt.where(ExerciseAnalysis.analysis_type == analysis_type)
        stmt = stmt.order_by(desc(ExerciseAnalysis.created_at))
        return (await self.session.execute(stmt)).scalars().all()


class WeeklyStatsRepository(BaseRepository[WeeklyStats]):
    model = WeeklyStats

    async def upsert(self, row: dict[str, Any]) -> None:
        stmt = pg_insert(WeeklyStats).values(row)
        update_cols = {k: stmt.excluded[k] for k in row if k != "week_start"}
        stmt = stmt.on_conflict_do_update(index_elements=["week_start"], set_=update_cols)
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_for_week(self, week_start: date) -> WeeklyStats | None:
        return (
            (
                await self.session.execute(
                    select(WeeklyStats).where(WeeklyStats.week_start == week_start)
                )
            )
            .scalars()
            .one_or_none()
        )


class MonthlyStatsRepository(BaseRepository[MonthlyStats]):
    model = MonthlyStats

    async def upsert(self, row: dict[str, Any]) -> None:
        stmt = pg_insert(MonthlyStats).values(row)
        update_cols = {k: stmt.excluded[k] for k in row if k != "month_start"}
        stmt = stmt.on_conflict_do_update(index_elements=["month_start"], set_=update_cols)
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_for_month(self, month_start: date) -> MonthlyStats | None:
        return (
            (
                await self.session.execute(
                    select(MonthlyStats).where(MonthlyStats.month_start == month_start)
                )
            )
            .scalars()
            .one_or_none()
        )


class TrainingContextRepository(BaseRepository[TrainingContext]):
    model = TrainingContext

    async def get_singleton(self) -> TrainingContext | None:
        return (
            (await self.session.execute(select(TrainingContext).where(TrainingContext.id == 1)))
            .scalars()
            .one_or_none()
        )


class ExerciseTargetRepository(BaseRepository[ExerciseTarget]):
    model = ExerciseTarget

    async def list_active(self) -> Sequence[ExerciseTarget]:
        stmt = select(ExerciseTarget).where(ExerciseTarget.status == "active")
        return (await self.session.execute(stmt)).scalars().all()


# ----- Helpers to materialise SetContext from joined workout tables -----------


async def load_all_set_contexts(session: Any) -> list[SetContext]:
    """JOIN workouts + workout_exercises + workout_sets + exercise_templates
    and return SetContext-ready dataclasses.

    Used by the nightly analysis job — full rescan (cheap for our volumes).
    """
    stmt = (
        select(
            WorkoutSet.id,
            Workout.id,
            Workout.start_time,
            WorkoutExercise.exercise_template_id,
            WorkoutExercise.title.label("ex_title"),
            ExerciseTemplate.title.label("tmpl_title"),
            ExerciseTemplate.primary_muscle_group,
            WorkoutSet.weight_kg,
            WorkoutSet.reps,
            WorkoutSet.set_type,
        )
        .select_from(WorkoutSet)
        .join(WorkoutExercise, WorkoutExercise.id == WorkoutSet.workout_exercise_id)
        .join(Workout, Workout.id == WorkoutExercise.workout_id)
        .outerjoin(
            ExerciseTemplate, ExerciseTemplate.hevy_id == WorkoutExercise.exercise_template_id
        )
        .order_by(Workout.start_time, WorkoutExercise.order_index, WorkoutSet.order_index)
    )
    rows = (await session.execute(stmt)).all()
    contexts: list[SetContext] = []
    for r in rows:
        title = r.ex_title or r.tmpl_title or "Unknown exercise"
        contexts.append(
            SetContext(
                set_id=r.id,
                workout_id=r[1],
                achieved_at=r.start_time,
                exercise_template_id=r.exercise_template_id,
                exercise_title=title,
                primary_muscle_group=r.primary_muscle_group,
                weight_kg=float(r.weight_kg) if r.weight_kg is not None else None,
                reps=r.reps,
                set_type=r.set_type or "normal",
            )
        )
    return contexts


__all__ = [
    "ExerciseAnalysisRepository",
    "ExerciseTargetRepository",
    "MonthlyStatsRepository",
    "PersonalRecordRepository",
    "TrainingContextRepository",
    "WeeklyStatsRepository",
    "_week_monday",  # re-export for the runner
    "load_all_set_contexts",
]
