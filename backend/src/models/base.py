"""SQLAlchemy declarative base and shared column types.

Modern SQLAlchemy 2.0 style using Mapped / mapped_column.
All models inherit from Base. Import order in __init__.py matters for
Alembic autogenerate to discover every table.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def uuid_pk() -> Mapped[uuid.UUID]:
    """Standard UUID primary key with server-side default."""
    return mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )


def created_at_col() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


def updated_at_col() -> Mapped[datetime]:
    return mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


def tstz(nullable: bool = True) -> Mapped[datetime | None]:
    """A TIMESTAMPTZ column (timezone-aware), nullable by default.

    Matches the schema-wide convention of TIMESTAMPTZ. Use this instead of a
    bare `mapped_column()` for datetime fields, otherwise SQLAlchemy defaults to
    TIMESTAMP WITHOUT TIME ZONE and drifts from the database schema.
    """
    return mapped_column(DateTime(timezone=True), nullable=nullable)
