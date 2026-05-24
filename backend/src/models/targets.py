"""Group 3 — Targets & Context models.

Tables: training_context, exercise_targets, program_split.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_col, tstz, updated_at_col, uuid_pk


class TrainingContext(Base):
    __tablename__ = "training_context"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    phase: Mapped[str | None] = mapped_column(String(20))  # cutting|bulking|maintenance|recomp
    phase_started_at: Mapped[date | None] = mapped_column(Date)
    phase_target_end_date: Mapped[date | None] = mapped_column(Date)
    current_weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    current_body_fat_pct: Mapped[float | None] = mapped_column(Numeric(4, 1))
    target_weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    target_body_fat_pct: Mapped[float | None] = mapped_column(Numeric(4, 1))
    daily_kcal_target: Mapped[int | None] = mapped_column(Integer)
    daily_protein_g_target_min: Mapped[int | None] = mapped_column(Integer)
    daily_protein_g_target_max: Mapped[int | None] = mapped_column(Integer)
    daily_hydration_l_target: Mapped[float | None] = mapped_column(Numeric(3, 1))
    sleep_target_hours_min: Mapped[float | None] = mapped_column(Numeric(3, 1))
    sleep_target_hours_max: Mapped[float | None] = mapped_column(Numeric(3, 1))
    bedtime_target: Mapped[time | None] = mapped_column(Time)
    wakeup_target: Mapped[time | None] = mapped_column(Time)
    daily_steps_target: Mapped[int | None] = mapped_column(Integer)
    weekly_long_walks_target: Mapped[int | None] = mapped_column(Integer)
    weekly_session_target: Mapped[int | None] = mapped_column(Integer)
    active_split: Mapped[str | None] = mapped_column(String(50))
    supplements: Mapped[dict | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = updated_at_col()

    __table_args__ = (CheckConstraint("id = 1", name="singleton_training_context"),)


class ExerciseTarget(Base):
    __tablename__ = "exercise_targets"

    id: Mapped[uuid.UUID] = uuid_pk()
    exercise_template_id: Mapped[str | None] = mapped_column(
        ForeignKey("exercise_templates.hevy_id")
    )
    exercise_title: Mapped[str | None] = mapped_column(String(200))  # denormalized (resilience)
    baseline_weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    baseline_reps: Mapped[int | None] = mapped_column(Integer)
    baseline_1rm_estimate: Mapped[float | None] = mapped_column(Numeric(6, 2))
    baseline_recorded_at: Mapped[datetime | None] = tstz()
    target_weight_kg_min: Mapped[float | None] = mapped_column(Numeric(6, 2))
    target_weight_kg_max: Mapped[float | None] = mapped_column(Numeric(6, 2))
    target_reps_min: Mapped[int | None] = mapped_column(Integer)
    target_reps_max: Mapped[int | None] = mapped_column(Integer)
    target_1rm_estimate: Mapped[float | None] = mapped_column(Numeric(6, 2))
    estimated_weeks_min: Mapped[int | None] = mapped_column(Integer)
    estimated_weeks_max: Mapped[int | None] = mapped_column(Integer)
    set_at: Mapped[datetime] = created_at_col()
    expected_completion_date: Mapped[date | None] = mapped_column(Date)
    exercise_type: Mapped[str | None] = mapped_column(String(30))
    track_1rm: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    track_volume: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    track_reps: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    workout_day: Mapped[str | None] = mapped_column(String(20))
    progression_chain: Mapped[dict | None] = mapped_column(JSONB)
    bodyweight_dependent: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    bw_threshold_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    context_phase: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    achieved_at: Mapped[datetime | None] = tstz()
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    __table_args__ = (
        Index(
            "idx_exercise_targets_status",
            "status",
            postgresql_where="status = 'active'",
        ),
    )


class ProgramSplit(Base):
    __tablename__ = "program_split"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    split_name: Mapped[str | None] = mapped_column(String(50))
    monday: Mapped[str | None] = mapped_column(String(20))
    tuesday: Mapped[str | None] = mapped_column(String(20))
    wednesday: Mapped[str | None] = mapped_column(String(20))
    thursday: Mapped[str | None] = mapped_column(String(20))
    friday: Mapped[str | None] = mapped_column(String(20))
    saturday: Mapped[str | None] = mapped_column(String(20))
    sunday: Mapped[str | None] = mapped_column(String(20))
    day_compositions: Mapped[dict | None] = mapped_column(JSONB)
    active_since: Mapped[date | None] = mapped_column(Date)
    active_until: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (CheckConstraint("id = 1", name="singleton_program_split"),)
