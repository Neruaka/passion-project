"""Shared pytest fixtures.

Two layers:
  * Unit tests (no DB / Redis): set env required by Settings, build the FastAPI
    app *without* lifespan.
  * Integration tests: spin up an ephemeral Postgres+pgvector via testcontainers
    (NFR-TEST-004), run Alembic, yield AsyncSession per test.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio

_BACKEND_ROOT = Path(__file__).resolve().parent.parent

# Bcrypt hash of "changeme" — keeps tests deterministic without depending on
# bcrypt at collection time.
_CHANGEME_HASH = "$2b$12$0lfu1ch/i8jsbm68mo4/9OP4E874u84p7XgQF7jbmvhaiIku9PsAW"

_TEST_ENV = {
    "ENVIRONMENT": "test",
    "DEBUG": "true",
    "DATABASE_URL": "postgresql+asyncpg://passion:passion@localhost:5432/passion",
    "REDIS_URL": "redis://localhost:6379/0",
    "JWT_SECRET": "test-secret-not-used-in-prod",
    "ADMIN_PASSWORD_HASH": _CHANGEME_HASH,
    "SYSTEM_PASSWORD_HASH": _CHANGEME_HASH,
    "JWT_EXPIRY_DAYS": "7",
    "ANTHROPIC_API_KEY": "sk-ant-test",
    "HEALTH_INGEST_TOKEN": "test-ingest-token",
}


@pytest.fixture(scope="session", autouse=True)
def _set_env() -> Iterator[None]:
    """Populate env vars required by Settings before any import touches them."""
    previous = {k: os.environ.get(k) for k in _TEST_ENV}
    os.environ.update(_TEST_ENV)
    # Clear the lru_cache so the next get_settings() picks up the new env.
    try:
        from src.core.config import get_settings

        get_settings.cache_clear()
    except Exception:
        pass
    yield
    for k, v in previous.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture()
def test_client():
    """A FastAPI TestClient WITHOUT lifespan (no Redis/DB ping required)."""
    from fastapi.testclient import TestClient
    from src.main import create_app

    app = create_app()
    # NOTE: not using `with TestClient(app)` → lifespan is not invoked.
    return TestClient(app)


def _to_async_dsn(url: str) -> str:
    """Normalise any postgresql DSN to asyncpg."""
    for prefix in ("postgresql+psycopg2://", "postgresql+psycopg://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix) :]
    return url


def _to_sync_dsn(url: str) -> str:
    """Normalise any postgresql DSN to psycopg2 (for Alembic)."""
    for prefix in ("postgresql+asyncpg://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix) :]
    return url


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    """Throwaway pgvector/postgres + Alembic upgrade head. Yields asyncpg DSN."""
    from alembic import command
    from alembic.config import Config
    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer(
        image="pgvector/pgvector:pg16",
        username="passion",
        password="passion",
        dbname="passion",
        driver=None,
    )
    container.start()
    try:
        raw_url = container.get_connection_url()
        sync_url = _to_sync_dsn(raw_url)
        alembic_cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(_BACKEND_ROOT / "migrations"))
        prev = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = sync_url
        try:
            command.upgrade(alembic_cfg, "head")
        finally:
            if prev is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = prev

        yield _to_async_dsn(raw_url)
    finally:
        container.stop()


_TRUNCATE_TABLES = [
    "workouts",
    "exercise_templates",
    "sync_state",
    "auth_attempts",
    "personal_records",
    "exercise_analysis",
    "weekly_stats",
    "monthly_stats",
    "agent_memory",
    "conversations",
    "messages",
    "workout_suggestions",
    "nutrition_plans",
    "challenges",
    "missions",
    "xp_log",
    "user_level",
    "streaks",
    "health_markers",
    "exercise_targets",
    "training_context",
    "program_split",
]


@pytest_asyncio.fixture()
async def db_session(postgres_url: str) -> AsyncIterator[object]:
    """Per-test AsyncSession; TRUNCATEs application tables at teardown.

    Each test starts with a clean slate. Reference / singleton rows (llm_config,
    notification_config) are intentionally NOT truncated; they're idempotent
    and shared across tests.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine(postgres_url, echo=False, pool_pre_ping=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with sessionmaker() as session:
        try:
            yield session
        finally:
            await session.rollback()
    # Wipe between tests so commits in one test don't leak to the next.
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {', '.join(_TRUNCATE_TABLES)} RESTART IDENTITY CASCADE"))
    await engine.dispose()
