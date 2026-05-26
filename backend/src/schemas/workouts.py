"""Workout API schemas. See API_CONTRACTS.md > WORKOUTS."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkoutSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hevy_id: str
    title: str | None
    start_time: datetime
    duration_minutes: int = 0
    exercise_count: int = 0
    total_volume_kg: float | None = None
    has_prs: bool = False


class WorkoutListResponse(BaseModel):
    items: list[WorkoutSummary]
    total: int
    page: int
    page_size: int
    has_next: bool


class SetDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_index: int
    set_type: Literal["warmup", "normal", "failure", "dropset"] = "normal"
    weight_kg: float | None = None
    reps: int | None = None
    rpe: float | None = None
    is_pr: bool = False
    pr_type: str | None = None


class ExerciseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str | None
    exercise_template_id: str | None
    order_index: int
    notes: str | None = None
    primary_muscle_group: str | None = None
    secondary_muscle_groups: list[str] = Field(default_factory=list)
    sets: list[SetDetail] = Field(default_factory=list)


class WorkoutDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hevy_id: str
    title: str | None
    description: str | None
    start_time: datetime
    end_time: datetime | None
    duration_minutes: int = 0
    exercises: list[ExerciseDetail] = Field(default_factory=list)
    total_volume_kg: float | None = None


class SyncTriggeredResponse(BaseModel):
    job_id: str
    status: Literal["queued"] = "queued"
    message: str = "Hevy sync queued."
