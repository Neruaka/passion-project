"""Generic base repository (repository pattern).

Isolates business logic from SQLAlchemy. Each domain repository extends this.
See C4 L3 (Repository Layer) and the architecture rationale on testability.
"""

from __future__ import annotations


class BaseRepository[T]:
    """Common CRUD operations over an AsyncSession.

    TODO(sprint-1): implement get, list, add, update, delete with an injected
    AsyncSession. Concrete repos add domain queries (e.g. find_recent).
    """

    model: type[T]
