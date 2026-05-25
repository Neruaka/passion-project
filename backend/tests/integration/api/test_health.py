"""/health endpoint smoke tests.

Without lifespan, DB and Redis are not initialized → /health returns 503 with a
structured payload. That's the desired behaviour for the Docker healthcheck.
"""

from __future__ import annotations


def test_health_returns_structured_payload(test_client):
    resp = test_client.get("/health")
    # No DB / Redis in test context → 503 with degraded status.
    assert resp.status_code == 503
    body = resp.json()
    assert set(body.keys()) >= {"status", "db", "redis", "version"}
    assert body["status"] == "degraded"
    assert body["db"] == "down"
    assert body["redis"] == "down"


def test_health_responds_within_a_second(test_client):
    import time

    start = time.monotonic()
    test_client.get("/health")
    assert time.monotonic() - start < 1.0
