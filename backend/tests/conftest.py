"""Shared pytest fixtures.

Sprint 0 tests are lightweight: we set the env required by Settings and build
the app *without* the lifespan (no DB / Redis needed for auth + security tests).
Future integration tests will use testcontainers per NFR-TEST-004.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

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


@pytest.fixture(scope="session")
def postgres_container():
    """Spin up a throwaway Postgres+pgvector container for integration tests.

    TODO(sprint-1): use testcontainers PostgresContainer with the pgvector
    image, run migrations, yield the connection URL.
    """
    pytest.skip("Implement in sprint 1 (NFR-TEST-004)")
