"""Alembic migration environment.

Reads DATABASE_URL from the environment (never hardcoded). Targets the
metadata of all ORM models so that future `alembic revision --autogenerate`
can detect drift. Note: the *initial* migration is hand-written because it
contains native partitioning, HNSW/BRIN indexes, and a materialized view —
none of which autogenerate can express.

Runtime uses `postgresql+asyncpg://...` (async driver), but Alembic itself is
synchronous — we transparently swap `+asyncpg` for `+psycopg2` here so one
DATABASE_URL works for both.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import all models so Base.metadata is fully populated.
from models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _to_sync_url(url: str) -> str:
    """Convert an async driver URL to its sync equivalent for Alembic."""
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)


# Inject DB URL from environment (transparently sync-ified).
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", _to_sync_url(database_url))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL to stdout, no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to the DB and apply)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
