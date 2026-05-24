"""Group 4 — Analysis models.

Tables: personal_records, exercise_analysis, weekly_stats, monthly_stats.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    DateTime,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_col, tstz, uuid_pk


class PersonalRecord(Base):
    __tablename__ = "personal_records"

    id: Mapped[uuid.UUID] = uuid_pk()
    exercise_template_id: Mapped[str | None] = mapped_column(
        ForeignKey("exercise_templates.hevy_id")
    )
    exercise_title: Mapped[str | None] = mapped_column(String(200))  # denormalized
    pr_type: Mapped[str] = mapped_column(String(30), nullable=False)
    new_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    old_value: Mapped[float | None] = mapped_column(Numeric(10, 2))
    gain: Mapped[float | None] = mapped_column(Numeric(10, 2))
    bucket: Mapped[str | None] = mapped_column(String(20))  # for reps_at_load (e.g. "80kg")
    workout_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workouts.id", ondelete="SET NULL")
    )
    workout_set_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workout_sets.id", ondelete="SET NULL")
    )
    achieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = created_at_col()

    __table_args__ = (
        Index("idx_prs_exercise_time", "exercise_template_id", achieved_at.desc()),
        Index("idx_prs_type", "pr_type", achieved_at.desc()),
    )


class ExerciseAnalysis(Base):
    __tablename__ = "exercise_analysis"

    id: Mapped[uuid.UUID] = uuid_pk()
    exercise_template_id: Mapped[str | None] = mapped_column(
        ForeignKey("exercise_templates.hevy_id")
    )
    exercise_title: Mapped[str | None] = mapped_column(String(200))
    analysis_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(20))  # minor|moderate|major
    details: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    resolved_at: Mapped[datetime | None] = tstz()
    created_at: Mapped[datetime] = created_at_col()

    __table_args__ = (
        Index(
            "idx_analysis_active",
            "status",
            "analysis_type",
            postgresql_where="status = 'active'",
        ),
    )


class WeeklyStats(Base):
    __tablename__ = "weekly_stats"

    id: Mapped[uuid.UUID] = uuid_pk()
    week_start: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_volume_kg: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    volume_per_muscle_group: Mapped[dict | None] = mapped_column(JSONB)
    pr_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = created_at_col()


class MonthlyStats(Base):
    __tablename__ = "monthly_stats"

    id: Mapped[uuid.UUID] = uuid_pk()
    month_start: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_volume_kg: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    volume_per_muscle_group: Mapped[dict | None] = mapped_column(JSONB)
    pr_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = created_at_col()
