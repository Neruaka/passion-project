"""Group 5 — Health models.

Tables: health_metrics (partitioned), health_markers.
The daily_health_summary materialized view is not an ORM model; it is created
and refreshed via raw SQL (migration + Celery job).

Note: health_metrics is partitioned by RANGE (recorded_at). Composite PK
(id, recorded_at) is required by Postgres partitioning. The partition DDL is
applied via op.execute() in the migration.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    DateTime,
    Date,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_col, uuid_pk


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    numeric_value: Mapped[float | None] = mapped_column(Numeric(12, 4))
    unit: Mapped[str | None] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(30), nullable=False)  # health_connect|manual|lab|dexcom
    source_device: Mapped[str | None] = mapped_column(String(50))
    source_app: Mapped[str | None] = mapped_column(String(50))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)  # 'metadata' is reserved in SA
    source_record_id: Mapped[str | None] = mapped_column(String(200))
    ingested_at: Mapped[datetime] = created_at_col()

    __table_args__ = (
        UniqueConstraint("source", "source_record_id", "recorded_at", name="uq_health_source_record"),
        Index("idx_health_metrics_type_time", "metric_type", recorded_at.desc()),
        Index("idx_health_metrics_recorded_brin", "recorded_at", postgresql_using="brin"),
        Index("idx_health_metrics_metadata", "metadata", postgresql_using="gin"),
        {"postgresql_partition_by": "RANGE (recorded_at)"},
    )


class HealthMarker(Base):
    __tablename__ = "health_markers"

    id: Mapped[uuid.UUID] = uuid_pk()
    measurement_date: Mapped[date] = mapped_column(Date, nullable=False)
    measurement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str | None] = mapped_column(String(100))
    values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    normalized_metrics: Mapped[dict | None] = mapped_column(JSONB)
    fasting_state: Mapped[bool | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    attachment_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = created_at_col()

    __table_args__ = (
        Index("idx_health_markers_date", measurement_date.desc()),
    )
