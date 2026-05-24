"""Group 7 — Gamification models.

Tables: missions, xp_log, user_level, streaks.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, created_at_col, tstz, updated_at_col, uuid_pk


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[uuid.UUID] = uuid_pk()
    for_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    mission_type: Mapped[str | None] = mapped_column(String(50))
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    completed_at: Mapped[datetime | None] = tstz()
    created_at: Mapped[datetime] = created_at_col()

    __table_args__ = (
        Index("idx_missions_date", for_date.desc(), "status"),
    )


class XPLog(Base):
    __tablename__ = "xp_log"

    id: Mapped[uuid.UUID] = uuid_pk()
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)  # mission|challenge|pr|...
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    earned_at: Mapped[datetime] = created_at_col()

    __table_args__ = (
        Index("idx_xp_log_earned", earned_at.desc()),
    )


class UserLevel(Base):
    __tablename__ = "user_level"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    current_xp: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    current_level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="Recruit")
    total_xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    updated_at: Mapped[datetime] = updated_at_col()

    __table_args__ = (CheckConstraint("id = 1", name="singleton_user_level"),)


class Streak(Base):
    __tablename__ = "streaks"

    id: Mapped[uuid.UUID] = uuid_pk()
    streak_type: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # workout|nutrition|sleep
    current_value: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    best_value: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    frozen_until: Mapped[date | None] = mapped_column(Date)
    freezes_used_this_month: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_calculated_at: Mapped[datetime] = created_at_col()
