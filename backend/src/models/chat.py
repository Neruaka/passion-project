"""Group 8 — Memory & Chat models.

Tables: agent_memory (pgvector + HNSW), conversations, messages.

The HNSW index on agent_memory.embedding cannot be expressed via Alembic
autogenerate; it is created via op.execute() in the migration.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, created_at_col, tstz, uuid_pk


class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id: Mapped[uuid.UUID] = uuid_pk()
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)))
    source: Mapped[str] = mapped_column(String(20), nullable=False, server_default="implicit")
    created_at: Mapped[datetime] = created_at_col()
    expires_at: Mapped[datetime | None] = tstz()
    is_obsolete: Mapped[bool] = mapped_column(nullable=False, server_default="false")

    __table_args__ = (
        # HNSW index created via op.execute() in migration (autogenerate can't do it).
        Index("idx_agent_memory_tags", "tags", postgresql_using="gin"),
        Index(
            "idx_agent_memory_active",
            created_at.desc(),
            postgresql_where="is_obsolete = false",
        ),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = uuid_pk()
    conversation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # direct_line|coach_fitness
    started_at: Mapped[datetime] = created_at_col()
    last_message_at: Mapped[datetime | None] = tstz()

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_conversations_last_msg", last_message_at.desc()),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user|assistant|system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = created_at_col()

    conversation: Mapped[Conversation] = relationship(back_populates="messages")

    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id", "created_at"),
    )
