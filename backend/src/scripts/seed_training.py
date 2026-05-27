"""Load config/training_seed.yaml into training_context + program_split + exercise_targets.

Idempotent: re-running updates fields by UNIQUE keys (singleton tables for
context/split, exercise_title for targets when no exercise_template_id is known).

Usage:
    docker compose exec backend python -m src.scripts.seed_training
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import structlog
import yaml  # type: ignore[import-untyped]
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings
from src.models.targets import ExerciseTarget, ProgramSplit, TrainingContext
from src.models.workouts import ExerciseTemplate

logger = structlog.get_logger(__name__)

_SEED_PATH = Path(__file__).resolve().parents[2] / "config" / "training_seed.yaml"


async def _resolve_template_id(session: AsyncSession, title: str) -> str | None:
    """Fuzzy-match exercise title to a Hevy template id (case-insensitive prefix).

    Returns None if no match — the target row is still created with a null FK
    and `exercise_title` denormalized (resilient to unmapped exercises, per
    ARCHITECTURE.md > Defensive denormalisation).
    """
    stmt = select(ExerciseTemplate.hevy_id).where(
        func.lower(ExerciseTemplate.title) == title.lower()
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _set_if_present(obj: Any, attr: str, value: Any) -> None:
    if value is not None:
        setattr(obj, attr, value)


async def _seed_training_context(session: AsyncSession, data: dict[str, Any]) -> None:
    stmt = select(TrainingContext).where(TrainingContext.id == 1)
    ctx = (await session.execute(stmt)).scalar_one_or_none()
    if ctx is None:
        ctx = TrainingContext(id=1)
        session.add(ctx)
    for field in (
        "phase",
        "current_weight_kg",
        "current_body_fat_pct",
        "target_weight_kg",
        "target_body_fat_pct",
        "daily_kcal_target",
        "daily_protein_g_target_min",
        "daily_protein_g_target_max",
        "daily_hydration_l_target",
        "sleep_target_hours_min",
        "sleep_target_hours_max",
        "daily_steps_target",
        "weekly_long_walks_target",
        "weekly_session_target",
        "active_split",
        "notes",
        "supplements",
        "retired_exercises",
    ):
        _set_if_present(ctx, field, data.get(field))
    if (started := data.get("phase_started_at")) is not None:
        ctx.phase_started_at = date.fromisoformat(str(started))
    if (end := data.get("phase_target_end_date")) is not None:
        ctx.phase_target_end_date = date.fromisoformat(str(end))
    if (bt := data.get("bedtime_target")) is not None:
        ctx.bedtime_target = datetime.strptime(bt, "%H:%M").time()
    if (wt := data.get("wakeup_target")) is not None:
        ctx.wakeup_target = datetime.strptime(wt, "%H:%M").time()
    await session.flush()


async def _seed_program_split(session: AsyncSession, data: dict[str, Any]) -> None:
    stmt = select(ProgramSplit).where(ProgramSplit.id == 1)
    split = (await session.execute(stmt)).scalar_one_or_none()
    if split is None:
        split = ProgramSplit(id=1)
        session.add(split)
    for field in (
        "split_name",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "day_compositions",
        "notes",
    ):
        _set_if_present(split, field, data.get(field))
    await session.flush()


async def _seed_one_target(session: AsyncSession, raw: dict[str, Any]) -> str:
    """Upsert a single exercise target by (exercise_title, workout_day). Returns action."""
    title = raw["title"]
    workout_day = raw.get("workout_day")
    stmt = select(ExerciseTarget).where(
        ExerciseTarget.exercise_title == title,
        ExerciseTarget.workout_day == workout_day,
    )
    target = (await session.execute(stmt)).scalar_one_or_none()
    action = "created"
    if target is None:
        target = ExerciseTarget(exercise_title=title, workout_day=workout_day)
        session.add(target)
        action = "created"
    else:
        action = "updated"

    baseline = raw.get("baseline") or {}
    target_block = raw.get("target") or {}
    weeks = raw.get("estimated_weeks") or {}

    target.exercise_template_id = await _resolve_template_id(session, title)
    target.exercise_type = raw.get("exercise_type")
    target.baseline_weight_kg = baseline.get("weight_kg")
    target.baseline_reps = baseline.get("reps")
    if baseline.get("weight_kg") is not None and baseline.get("reps") is not None:
        # Epley estimate
        target.baseline_1rm_estimate = round(
            float(baseline["weight_kg"]) * (1 + float(baseline["reps"]) / 30), 2
        )
        target.baseline_recorded_at = datetime.now(tz=UTC)
    target.target_weight_kg_min = target_block.get("weight_kg_min") or target_block.get("weight_kg")
    target.target_weight_kg_max = target_block.get("weight_kg_max") or target_block.get("weight_kg")
    target.target_reps_min = target_block.get("reps_min") or target_block.get("reps")
    target.target_reps_max = target_block.get("reps_max") or target_block.get("reps")
    if target.target_weight_kg_max and target.target_reps_min:
        target.target_1rm_estimate = round(
            float(target.target_weight_kg_max) * (1 + float(target.target_reps_min) / 30),
            2,
        )
    target.estimated_weeks_min = weeks.get("min")
    target.estimated_weeks_max = weeks.get("max")
    target.notes = raw.get("notes")
    target.bodyweight_dependent = bool(raw.get("bodyweight_dependent"))
    if raw.get("progression_chain"):
        target.progression_chain = raw["progression_chain"]
    elif raw.get("long_term"):
        target.progression_chain = {"long_term": raw["long_term"]}

    await session.flush()
    return action


async def _run() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    raw_yaml = yaml.safe_load(_SEED_PATH.read_text(encoding="utf-8"))

    async with sessionmaker() as session:
        try:
            await _seed_training_context(session, raw_yaml.get("training_context") or {})
            await _seed_program_split(session, raw_yaml.get("program_split") or {})

            actions = {"created": 0, "updated": 0}
            for raw in raw_yaml.get("exercise_targets") or []:
                action = await _seed_one_target(session, raw)
                actions[action] += 1

            await session.commit()
            logger.info(
                "training_seed_loaded",
                targets_created=actions["created"],
                targets_updated=actions["updated"],
            )
            print(
                f"Seed loaded: {actions['created']} targets created, "
                f"{actions['updated']} updated, training_context + program_split refreshed."
            )
        except Exception:
            await session.rollback()
            raise
        finally:
            await engine.dispose()


def main() -> int:
    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
