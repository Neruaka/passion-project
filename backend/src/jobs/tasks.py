"""Celery tasks (autodiscovered by celery_app.app.autodiscover_tasks).

Each task wraps an async service in a fresh event loop, manages a DB session,
adds retry/backoff per US-008 acceptance criteria (1min / 5min / 15min), and
escalates persistent failures via ntfy.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.celery_app import app
from src.core.config import get_settings
from src.integrations.external.ntfy import notify
from src.integrations.mcp.hevy import FakeHevyClient, HevyClient, McpHevyClient
from src.services.fitness.sync import sync_hevy

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def _session_scope() -> AsyncIterator[AsyncSession]:
    """One-shot AsyncSession for a Celery task."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with sessionmaker() as session:
            yield session
    finally:
        await engine.dispose()


def _build_hevy_client() -> HevyClient:
    """Pick MCP (real key) or Fake (no key) automatically.

    The Fake path lets the worker boot in dev with HEVY_API_KEY empty without
    crashing the entire Celery process on schedule firing.
    """
    settings = get_settings()
    if settings.hevy_api_key:
        return McpHevyClient(api_key=settings.hevy_api_key)
    logger.warning("hevy_api_key_missing_fake_client")
    return FakeHevyClient()


async def _do_sync_hevy() -> dict[str, Any]:
    async with _session_scope() as session:
        client = _build_hevy_client()
        async with client:
            stats = await sync_hevy(session, client)
            return stats.as_dict()


@app.task(  # type: ignore[untyped-decorator]
    name="sync_hevy_workouts",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,  # 1 min, doubles
    retry_backoff_max=900,  # cap at 15 min (US-008 sc.4)
    retry_jitter=True,
    max_retries=3,
)
def sync_hevy_workouts(self: Any) -> dict[str, Any]:
    """Periodic Hevy sync — runs every 30 min via Celery Beat (US-008)."""
    log = logger.bind(task="sync_hevy_workouts", retries=self.request.retries)
    try:
        result = asyncio.run(_do_sync_hevy())
    except Exception as e:
        log.exception("sync_hevy_attempt_failed", error=str(e))
        # Final retry? Escalate via ntfy.
        if self.request.retries >= (self.max_retries or 0):
            settings = get_settings()
            asyncio.run(
                notify(
                    settings.ntfy_topic,
                    f"Hevy sync FAILED after {self.max_retries + 1} attempts: {e!s}",
                    title="PASSION — Hevy sync down",
                    priority="high",
                    tags=["warning", "hevy"],
                )
            )
        raise
    log.info("sync_hevy_done", **result)
    return result
