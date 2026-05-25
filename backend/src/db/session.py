"""Async SQLAlchemy engine and session factory.

Provides the AsyncSession used by repositories. Connection pool sized per
NFR-SCA-002 (max pool 20, initial 10).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Create the async engine + sessionmaker. Idempotent."""
    global _engine, _sessionmaker
    if _engine is not None:
        return _engine
    _engine = create_async_engine(
        database_url,
        echo=echo,
        pool_size=10,
        max_overflow=10,  # max pool = 20
        pool_pre_ping=True,
    )
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    return _engine


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("DB engine not initialized — call init_engine() at startup.")
    return _engine


async def dispose_engine() -> None:
    """Close all pooled connections (call on shutdown)."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yield an AsyncSession per request."""
    if _sessionmaker is None:
        raise RuntimeError("DB sessionmaker not initialized — call init_engine() at startup.")
    async with _sessionmaker() as session:
        yield session


async def ping(engine: AsyncEngine | None = None) -> bool:
    """Run SELECT 1 against the DB. Returns True on success, False on failure."""
    from sqlalchemy import text

    eng = engine or _engine
    if eng is None:
        return False
    try:
        async with eng.connect() as conn:
            result: Any = await conn.execute(text("SELECT 1"))
            return bool(result.scalar() == 1)
    except Exception:
        return False
