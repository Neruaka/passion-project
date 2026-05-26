"""Generic base repository (repository pattern).

Isolates business logic from SQLAlchemy. Each domain repository extends this.
See C4 L3 (Repository Layer) and the architecture rationale on testability.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[T]:
    """Common CRUD operations over an AsyncSession.

    Concrete repos set `model` and add domain queries (e.g. `find_by_hevy_id`).
    """

    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, pk: UUID | int | str) -> T | None:
        return await self.session.get(self.model, pk)

    async def list(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        await self.session.delete(entity)
        await self.session.flush()

    async def delete_by_pk(self, pk: Any) -> int:
        stmt = sql_delete(self.model).where(self.model.id == pk)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount or 0  # type: ignore[attr-defined]
