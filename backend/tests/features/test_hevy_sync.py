"""Acceptance tests for hevy_sync.feature (US-008).

NOTE: pytest-bdd 8 has limited async-step support (each @then is called
synchronously even if defined async). Rather than fight that, we keep
hevy_sync.feature as the human-readable spec and implement the three
scenarios as plain pytest-asyncio tests below — same coverage, simpler
debugging, future migration to pytest-bdd async-steps is trivial.

Coverage:
  * Scenario "Incremental sync (nominal)"
  * Scenario "Deduplication on re-sync"
  * Scenario "Hevy API unavailable"
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from src.integrations.mcp.hevy import FakeHevyClient, HevyExerciseDTO, HevyWorkoutDTO
from src.repositories.workouts import (
    SyncStateRepository,
    WorkoutListFilters,
    WorkoutRepository,
)
from src.services.fitness.sync import HEVY_SERVICE_NAME, sync_hevy


def _workout(hevy_id: str, at: datetime | None = None) -> HevyWorkoutDTO:
    return HevyWorkoutDTO(
        hevy_id=hevy_id,
        title=f"Workout {hevy_id}",
        description=None,
        start_time=at or datetime(2026, 5, 25, 12, 0, tzinfo=UTC),
        end_time=None,
        hevy_created_at=None,
        hevy_updated_at=None,
        raw={"id": hevy_id, "title": f"Workout {hevy_id}"},
        exercises=[
            HevyExerciseDTO(
                title="Bench Press",
                exercise_template_id=None,
                order_index=0,
                sets=[{"order_index": 0, "set_type": "normal", "weight_kg": 80, "reps": 5}],
            )
        ],
    )


class _RaisingHevyClient(FakeHevyClient):
    """Simulates Hevy 5xx — list_workouts raises (US-008 sc.4)."""

    def __init__(self, exc: Exception) -> None:
        super().__init__([], [])
        self._exc = exc

    async def list_workouts(
        self, *, page: int = 1, page_size: int = 50
    ) -> tuple[list[HevyWorkoutDTO], bool]:
        raise self._exc


@pytest.mark.asyncio
async def test_incremental_sync_nominal(db_session) -> None:
    """GIVEN agent + valid key, last sync at T-30min
    WHEN scheduler triggers sync_hevy_workouts
    THEN each workout upserted by hevy_id, last_successful_sync updated."""
    # Seed sync_state to simulate an existing incremental run.
    state_repo = SyncStateRepository(db_session)
    state = await state_repo.get_or_create(HEVY_SERVICE_NAME)
    state.last_successful_sync = datetime.now(tz=UTC) - timedelta(minutes=30)
    state.bootstrap_completed = True
    await db_session.commit()

    hevy_workouts = [_workout("w1"), _workout("w2")]
    async with FakeHevyClient(hevy_workouts, []) as client:
        stats = await sync_hevy(db_session, client)

    assert stats.success is True
    assert stats.workouts_new == 2

    workout_repo = WorkoutRepository(db_session)
    for w in hevy_workouts:
        assert await workout_repo.get_by_hevy_id(w.hevy_id) is not None

    state = await state_repo.get_or_create(HEVY_SERVICE_NAME)
    assert state.last_successful_sync is not None


@pytest.mark.asyncio
async def test_deduplication_on_resync(db_session) -> None:
    """GIVEN workout 'w_abc' already exists
    WHEN a new sync returns that same workout
    THEN it is updated, not duplicated."""
    # 1st sync: seed
    async with FakeHevyClient([_workout("w_abc")], []) as client:
        await sync_hevy(db_session, client)

    # 2nd sync: same workout (would be a duplicate if not idempotent)
    async with FakeHevyClient([_workout("w_abc")], []) as client:
        stats = await sync_hevy(db_session, client)

    assert stats.success is True
    assert stats.workouts_new == 0
    assert stats.workouts_updated == 1

    repo = WorkoutRepository(db_session)
    items, total = await repo.list_paginated(WorkoutListFilters(), page=1, page_size=100)
    assert total == 1
    assert items[0].hevy_id == "w_abc"


@pytest.mark.asyncio
async def test_hevy_api_unavailable(db_session) -> None:
    """GIVEN Hevy API returns 5xx
    WHEN sync runs
    THEN service raises (Celery layer handles retry/backoff + ntfy),
         and last_successful_sync stays unchanged + last_error is captured."""
    async with _RaisingHevyClient(RuntimeError("Hevy 503 Service Unavailable")) as client:
        with pytest.raises(RuntimeError):
            await sync_hevy(db_session, client)

    state = await SyncStateRepository(db_session).get_or_create(HEVY_SERVICE_NAME)
    assert state.last_successful_sync is None
    assert state.last_error is not None
    assert "503" in state.last_error
