"""Repository integration tests for Sprint 1 (testcontainers Postgres+pgvector)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from src.repositories.workouts import (
    ExerciseTemplateRepository,
    SyncStateRepository,
    WorkoutListFilters,
    WorkoutRepository,
)


@pytest.mark.asyncio
async def test_exercise_template_upsert_inserts_then_updates(db_session) -> None:
    repo = ExerciseTemplateRepository(db_session)

    # Insert
    n = await repo.upsert_many(
        [{"hevy_id": "ex_bench", "title": "Bench Press", "primary_muscle_group": "chest"}]
    )
    assert n >= 1
    template = await repo.get_by_hevy_id("ex_bench")
    assert template is not None
    assert template.title == "Bench Press"

    # Update (same hevy_id, different title)
    await repo.upsert_many(
        [{"hevy_id": "ex_bench", "title": "Bench Press (Barbell)", "primary_muscle_group": "chest"}]
    )
    template = await repo.get_by_hevy_id("ex_bench")
    assert template is not None
    assert template.title == "Bench Press (Barbell)"


@pytest.mark.asyncio
async def test_workout_upsert_creates_then_replaces_children(db_session) -> None:
    repo = WorkoutRepository(db_session)
    start = datetime(2026, 5, 25, 10, 0, tzinfo=UTC)

    # 1) Create
    result = await repo.upsert_workout(
        workout_data={
            "hevy_id": "w_abc",
            "title": "Push day",
            "start_time": start,
            "end_time": start + timedelta(minutes=45),
        },
        exercises_data=[
            {
                "title": "Bench Press",
                "exercise_template_id": None,
                "order_index": 0,
                "notes": None,
                "superset_id": None,
                "sets": [
                    {"order_index": 0, "set_type": "warmup", "weight_kg": 40, "reps": 10},
                    {"order_index": 1, "set_type": "normal", "weight_kg": 80, "reps": 5},
                ],
            }
        ],
    )
    assert result.was_new is True
    await db_session.commit()

    # 2) UPSERT with different sets — children should be replaced
    result = await repo.upsert_workout(
        workout_data={
            "hevy_id": "w_abc",
            "title": "Push day (renamed)",
            "start_time": start,
            "end_time": start + timedelta(minutes=50),
        },
        exercises_data=[
            {
                "title": "Bench Press",
                "exercise_template_id": None,
                "order_index": 0,
                "notes": None,
                "superset_id": None,
                "sets": [{"order_index": 0, "set_type": "normal", "weight_kg": 85, "reps": 5}],
            }
        ],
    )
    assert result.was_new is False
    await db_session.commit()

    detail = await repo.get_detail(result.workout.id)
    assert detail is not None
    assert detail.title == "Push day (renamed)"
    assert len(detail.exercises) == 1
    assert len(detail.exercises[0].sets) == 1
    assert float(detail.exercises[0].sets[0].weight_kg) == 85


@pytest.mark.asyncio
async def test_workout_list_paginated_filters_by_date(db_session) -> None:
    repo = WorkoutRepository(db_session)
    base = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)

    for i in range(5):
        await repo.upsert_workout(
            workout_data={
                "hevy_id": f"w_{i}",
                "title": f"Workout {i}",
                "start_time": base + timedelta(days=i),
            },
            exercises_data=[],
        )
    await db_session.commit()

    items, total = await repo.list_paginated(
        WorkoutListFilters(from_date=base + timedelta(days=2)),
        page=1,
        page_size=10,
    )
    assert total == 3
    assert [w.hevy_id for w in items] == ["w_4", "w_3", "w_2"]  # newest first


@pytest.mark.asyncio
async def test_sync_state_mark_success_clears_error(db_session) -> None:
    repo = SyncStateRepository(db_session)

    await repo.mark_error("hevy", "boom")
    state = await repo.get_or_create("hevy")
    assert state.last_error == "boom"
    assert state.last_successful_sync is None

    await repo.mark_success("hevy", completed_bootstrap=True)
    state = await repo.get_or_create("hevy")
    assert state.last_error is None
    assert state.last_successful_sync is not None
    assert state.bootstrap_completed is True
