"""Analysis API schemas (Sprint 2). See API_CONTRACTS.md > ANALYSIS."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PRRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exercise_title: str | None
    exercise_template_id: str | None = None
    pr_type: Literal["one_rep_max", "reps_at_load", "session_volume", "muscle_group_volume"]
    new_value: float
    old_value: float | None = None
    gain: float | None = None
    bucket: str | None = None
    achieved_at: datetime
    workout_id: UUID | None = None


class PRListResponse(BaseModel):
    items: list[PRRecord]
    total: int
    page: int
    page_size: int


class PlateauAnalysis(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exercise_title: str | None
    exercise_template_id: str | None = None
    analysis_type: Literal["plateau_official", "plateau_stalled", "regression", "behind_schedule"]
    severity: Literal["minor", "moderate", "major"] | None = None
    details: dict[str, Any] | None = None
    status: Literal["active", "resolved"]
    created_at: datetime


class TargetPoint(BaseModel):
    weight_kg: float | None = None
    reps: int | None = None
    one_rm_estimate: float | None = None


class TargetProgressOut(BaseModel):
    exercise_template_id: str | None
    exercise_title: str
    workout_day: str | None
    baseline: TargetPoint
    current: TargetPoint
    target_weight_kg_min: float | None
    target_weight_kg_max: float | None
    target_reps: int | None
    target_1rm: float | None
    progress_pct: float
    weeks_elapsed: int
    weeks_estimated_max: int | None
    status: Literal[
        "calibrating",
        "below_baseline",
        "on_track",
        "behind_schedule",
        "ahead_of_schedule",
        "achieved",
        "expired",
    ]


class MuscleStatusOut(BaseModel):
    muscle_group: str
    recovery_state: Literal["ready", "recovering", "heavy_fatigue", "neglected"]
    days_since_last_trained: float
    recovery_left_days: float
    volume_last_7d: float
    frequency_last_30d: int
    flag: str | None = None


class TopExercise(BaseModel):
    title: str
    volume_kg: float


class StatsResponse(BaseModel):
    period: Literal["week", "month"]
    period_start: date
    period_end: date
    total_sessions: int
    total_duration_minutes: int
    total_volume_kg: float
    volume_by_muscle: dict[str, float] = Field(default_factory=dict)
    pr_count: int
    sessions_by_day: dict[str, int] = Field(default_factory=dict)
    top_exercises: list[TopExercise] = Field(default_factory=list)


class ProgressionPoint(BaseModel):
    date: date
    one_rm_estimate: float
    volume_kg: float


class ProgressionResponse(BaseModel):
    exercise_title: str
    exercise_template_id: str | None
    data_points: list[ProgressionPoint]
    prs: list[dict[str, Any]] = Field(default_factory=list)
    plateaus: list[dict[str, Any]] = Field(default_factory=list)
