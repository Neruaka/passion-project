"""Re-export the ORM Base so Alembic and tooling can import from one place."""

from __future__ import annotations

from src.models import Base  # noqa: F401
