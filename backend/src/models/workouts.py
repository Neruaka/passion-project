"""Group 2 — Workouts & Exercises models.

Tables: exercise_templates, workouts, workout_exercises, workout_sets, sync_state.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, created_at_col, tstz, updated_at_col, uuid_pk


class ExerciseTemplate(Base):
    __tablename__ = "exercise_templates"

    hevy_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    primary_muscle_group: Mapped[str | None] = mapped_column(String(50))
    secondary_muscle_groups: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)))
    equipment: Mapped[str | None] = mapped_column(String(50))
    exercise_type: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = created_at_col()


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[uuid.UUID] = uuid_pk()
    hevy_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = tstz()
    hevy_created_at: Mapped[datetime | None] = tstz()
    hevy_updated_at: Mapped[datetime | None] = tstz()
    total_volume_kg: Mapped[float | None] = mapped_column(Numeric(10, 2))  # precalculated
    synced_at: Mapped[datetime] = created_at_col()
    raw_data: Mapped[dict | None] = mapped_column(JSONB)

    exercises: Mapped[list[WorkoutExercise]] = relationship(
        back_populates="workout", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_workouts_start_time", start_time.desc()),
        Index("idx_workouts_raw_data", "raw_data", postgresql_using="gin"),
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id: Mapped[uuid.UUID] = uuid_pk()
    workout_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False
    )
    exercise_template_id: Mapped[str | None] = mapped_column(
        ForeignKey("exercise_templates.hevy_id")
    )
    title: Mapped[str | None] = mapped_column(String(200))
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    superset_id: Mapped[str | None] = mapped_column(String(50))

    workout: Mapped[Workout] = relationship(back_populates="exercises")
    sets: Mapped[list[WorkoutSet]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_workout_exercises_workout", "workout_id", "order_index"),)


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id: Mapped[uuid.UUID] = uuid_pk()
    workout_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_exercises.id", ondelete="CASCADE"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    set_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="normal")
    weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    reps: Mapped[int | None] = mapped_column(Integer)
    rpe: Mapped[float | None] = mapped_column(Numeric(3, 1))
    distance_meters: Mapped[float | None] = mapped_column(Numeric(8, 2))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    exercise: Mapped[WorkoutExercise] = relationship(back_populates="sets")

    __table_args__ = (Index("idx_workout_sets_exercise", "workout_exercise_id", "order_index"),)


class SyncState(Base):
    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    service: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )  # hevy|cronometer|health
    last_successful_sync: Mapped[datetime | None] = tstz()
    bootstrap_completed: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    last_error: Mapped[str | None] = mapped_column(Text)
    last_error_at: Mapped[datetime | None] = tstz()
    updated_at: Mapped[datetime] = updated_at_col()
