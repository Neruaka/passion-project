"""Async SQLAlchemy engine and session factory.

Provides the AsyncSession used by repositories. Connection pool sized per
NFR-SCA-002 (max pool 20, initial 10).
"""

from __future__ import annotations


def create_engine_and_sessionmaker(database_url: str):
    """Create the async engine and sessionmaker.

    TODO(sprint-1): configure async engine (asyncpg), pool sizing, session
    factory, and a get_session() dependency for FastAPI.
    """
    raise NotImplementedError("Implement in sprint 1")
