"""Add training_context.retired_exercises (JSONB array of titles) — Sprint 2 fix.

Permanently retired exercises (e.g. deadlift conventional, RDL, barbell squat)
shouldn't surface in plateau analysis or coach suggestions. Stored as JSONB so
we can extend with metadata later (reason, replacement, retired_at).

Revision ID: 20260528_1200_add_retired
Revises: 0001_initial_schema
Create Date: 2026-05-28T12:00:00+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260528_1200_add_retired"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "training_context",
        sa.Column(
            "retired_exercises",
            JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("training_context", "retired_exercises")
