"""Group 6 — Coaching models.

Tables: workout_suggestions, nutrition_plans, challenges.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_col, tstz, uuid_pk


class WorkoutSuggestion(Base):
    __tablename__ = "workout_suggestions"

    id: Mapped[uuid.UUID] = uuid_pk()
    generated_at: Mapped[datetime] = created_at_col()
    for_date: Mapped[date] = mapped_column(Date, nullable=False)
    prompt_used: Mapped[str | None] = mapped_column(Text)
    llm_response_raw: Mapped[dict | None] = mapped_column(JSONB)
    recommendation: Mapped[str | None] = mapped_column(Text)
    reasoning: Mapped[str | None] = mapped_column(Text)
    workout_type: Mapped[str | None] = mapped_column(String(20))
    exercises: Mapped[dict | None] = mapped_column(JSONB)
    expected_duration_min: Mapped[int | None] = mapped_column(Integer)
    warnings: Mapped[dict | None] = mapped_column(JSONB)
    alternative_if_tired: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    user_feedback: Mapped[str | None] = mapped_column(Text)
    user_modifications: Mapped[dict | None] = mapped_column(JSONB)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    cost_eur: Mapped[float | None] = mapped_column(Numeric(8, 5))

    __table_args__ = (Index("idx_workout_suggestions_date", for_date.desc()),)


class NutritionPlan(Base):
    __tablename__ = "nutrition_plans"

    id: Mapped[uuid.UUID] = uuid_pk()
    for_date: Mapped[date] = mapped_column(Date, nullable=False)
    generated_at: Mapped[datetime] = created_at_col()
    daily_kcal_target: Mapped[int | None] = mapped_column(Integer)
    daily_protein_target_g: Mapped[int | None] = mapped_column(Integer)
    daily_carbs_target_g: Mapped[int | None] = mapped_column(Integer)
    daily_fats_target_g: Mapped[int | None] = mapped_column(Integer)
    hydration_target_l: Mapped[float | None] = mapped_column(Numeric(3, 1))
    timing_strategy: Mapped[str | None] = mapped_column(String(50))
    meal_distribution: Mapped[dict | None] = mapped_column(JSONB)
    supplements_today: Mapped[dict | None] = mapped_column(JSONB)
    is_training_day: Mapped[bool] = mapped_column(nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("idx_nutrition_plans_date", for_date.desc()),)


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = uuid_pk()
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    challenge_type: Mapped[str | None] = mapped_column(String(50))
    measurable_goal: Mapped[dict | None] = mapped_column(JSONB)
    tracking_method: Mapped[str | None] = mapped_column(String(20))  # auto|manual
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    deadline: Mapped[datetime | None] = tstz()
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    completed_at: Mapped[datetime | None] = tstz()
    progress: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = created_at_col()

    __table_args__ = (Index("idx_challenges_week", week_start.desc(), "status"),)
