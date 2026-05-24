"""Shared pytest fixtures.

Integration tests use a disposable Postgres via testcontainers (NFR-TEST-004).
Unit tests for services need no fixtures (pure functions).
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def postgres_container():
    """Spin up a throwaway Postgres+pgvector container for integration tests.

    TODO(sprint-1): use testcontainers PostgresContainer with the pgvector
    image, run migrations, yield the connection URL.
    """
    pytest.skip("Implement in sprint 1 (NFR-TEST-004)")
