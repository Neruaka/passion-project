"""Group 1 — Auth & System models.

Tables: llm_config, notification_config, auth_attempts, agent_actions.

Note: agent_actions is partitioned by RANGE (created_at) at the database level.
SQLAlchemy/Alembic autogenerate cannot express native partitioning, so the
partitioning DDL is applied via raw op.execute() in the migration. This model
describes the logical shape; the composite PK (id, created_at) reflects the
Postgres requirement that the partition key be part of the primary key.
"""

from __future__ import annotations

import uuid
from datetime import datetime, time

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_col, updated_at_col


class LLMConfig(Base):
    __tablename__ = "llm_config"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    navichat_model: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="claude-sonnet-4-5"
    )
    daily_call_budget: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    daily_cost_budget_eur: Mapped[float] = mapped_column(
        Numeric(6, 2), nullable=False, server_default="1.50"
    )
    routing_enabled: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    updated_at: Mapped[datetime] = updated_at_col()

    __table_args__ = (CheckConstraint("id = 1", name="singleton_llm_config"),)


class NotificationConfig(Base):
    __tablename__ = "notification_config"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    email_enabled: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    push_enabled: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    briefing_hour: Mapped[time] = mapped_column(Time, nullable=False, server_default="07:00")
    ntfy_topic: Mapped[str | None] = mapped_column(String(200))
    recipient_email: Mapped[str | None] = mapped_column(String(255))
    updated_at: Mapped[datetime] = updated_at_col()

    __table_args__ = (CheckConstraint("id = 1", name="singleton_notif_config"),)


class AuthAttempt(Base):
    __tablename__ = "auth_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    ip_address: Mapped[str | None] = mapped_column(INET)
    attempt_type: Mapped[str] = mapped_column(String(20), nullable=False)  # login|system_access
    success: Mapped[bool] = mapped_column(nullable=False)
    attempted_at: Mapped[datetime] = created_at_col()

    __table_args__ = (Index("idx_auth_attempts_ip_time", "ip_address", attempted_at.desc()),)


class AgentAction(Base):
    __tablename__ = "agent_actions"

    # Composite PK required by partitioning (partition key must be in PK).
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input: Mapped[dict | None] = mapped_column(JSONB)
    output: Mapped[dict | None] = mapped_column(JSONB)
    prompt_sent: Mapped[str | None] = mapped_column(Text)
    llm_response_raw: Mapped[str | None] = mapped_column(Text)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    cost_eur: Mapped[float | None] = mapped_column(Numeric(8, 5))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success|error|partial
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True, nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_agent_actions_created_name", created_at.desc(), "agent_name"),
        {"postgresql_partition_by": "RANGE (created_at)"},
    )
