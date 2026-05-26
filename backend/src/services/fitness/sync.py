"""Hevy sync orchestrator (Flow 1 — see ARCHITECTURE.md > DATA FLOWS).

Pure service: takes a session + a HevyClient, returns sync statistics. Retries,
backoff, alerting, and Celery scheduling live in src/jobs/tasks.py and
src/jobs/schedule.py.

US-008 covers all five Gherkin scenarios from SPECIFICATIONS.md:
  1. Incremental sync (nominal)
  2. First sync (bootstrap)
  3. Deduplication (UPSERT by hevy_id)
  4. Hevy API unavailable — handled by tenacity in tasks.py
  5. Rate limit (429) — same
  6. Invalid key (401) — same + ntfy critical
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.integrations.mcp.hevy import HevyClient, HevyWorkoutDTO
from src.repositories.workouts import (
    ExerciseTemplateRepository,
    SyncStateRepository,
    WorkoutRepository,
)

logger = structlog.get_logger(__name__)

HEVY_SERVICE_NAME = "hevy"
_DEFAULT_PAGE_SIZE = 50


@dataclass(slots=True)
class HevySyncStats:
    """What every sync run produces — for logging, telemetry, API responses."""

    workouts_new: int = 0
    workouts_updated: int = 0
    templates_synced: int = 0
    pages_fetched: int = 0
    duration_ms: int = 0
    bootstrap: bool = False
    success: bool = False
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _workout_to_orm_kwargs(dto: HevyWorkoutDTO) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Split a HevyWorkoutDTO into (workout_kwargs, list_of_exercise_kwargs)."""
    workout = {
        "hevy_id": dto.hevy_id,
        "title": dto.title,
        "description": dto.description,
        "start_time": dto.start_time,
        "end_time": dto.end_time,
        "hevy_created_at": dto.hevy_created_at,
        "hevy_updated_at": dto.hevy_updated_at,
        "raw_data": dto.raw,
    }
    exercises = [
        {
            "title": ex.title,
            "exercise_template_id": ex.exercise_template_id,
            "order_index": ex.order_index,
            "notes": ex.notes,
            "superset_id": ex.superset_id,
            "sets": list(ex.sets),
        }
        for ex in dto.exercises
    ]
    return workout, exercises


async def sync_hevy(
    session: AsyncSession,
    client: HevyClient,
    *,
    page_size: int = _DEFAULT_PAGE_SIZE,
    max_pages: int | None = None,
) -> HevySyncStats:
    """Run a single full sync against Hevy.

    Idempotent via UPSERT-by-hevy_id (US-008 sc.3). Updates `sync_state` ONLY
    on full success (US-008 sc.1 last bullet). Caller is responsible for the
    retry/backoff envelope.
    """
    started = time.monotonic()
    stats = HevySyncStats()

    state_repo = SyncStateRepository(session)
    template_repo = ExerciseTemplateRepository(session)
    workout_repo = WorkoutRepository(session)

    state = await state_repo.get_or_create(HEVY_SERVICE_NAME)
    stats.bootstrap = not state.bootstrap_completed

    log = logger.bind(service=HEVY_SERVICE_NAME, bootstrap=stats.bootstrap)
    log.info("hevy_sync_start")

    try:
        # 1. Exercise templates first (FK target for workout_exercises).
        templates = await client.list_exercise_templates()
        stats.templates_synced = await template_repo.upsert_many(templates)

        # 2. Paginated workouts.
        page = 1
        while True:
            workouts, has_more = await client.list_workouts(page=page, page_size=page_size)
            stats.pages_fetched += 1
            for dto in workouts:
                workout_kwargs, exercises_kwargs = _workout_to_orm_kwargs(dto)
                result = await workout_repo.upsert_workout(
                    workout_data=workout_kwargs,
                    exercises_data=exercises_kwargs,
                )
                if result.was_new:
                    stats.workouts_new += 1
                else:
                    stats.workouts_updated += 1
            if not has_more:
                break
            page += 1
            if max_pages is not None and page > max_pages:
                log.warning("hevy_sync_max_pages_reached", max_pages=max_pages)
                break

        await state_repo.mark_success(HEVY_SERVICE_NAME, completed_bootstrap=stats.bootstrap)
        await session.commit()
        stats.success = True

    except Exception as e:
        await session.rollback()
        # New tx for the error metadata so it actually persists.
        await state_repo.mark_error(HEVY_SERVICE_NAME, f"{type(e).__name__}: {e}")
        await session.commit()
        stats.error = f"{type(e).__name__}: {e}"
        stats.duration_ms = int((time.monotonic() - started) * 1000)
        log.exception("hevy_sync_failed", error=stats.error)
        raise

    stats.duration_ms = int((time.monotonic() - started) * 1000)
    log.info("hevy_sync_complete", **stats.as_dict())
    return stats
