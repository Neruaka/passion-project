"""Auth endpoints integration tests (US-001)."""

from __future__ import annotations

import pytest


def test_login_with_correct_password_returns_token(test_client):
    resp = test_client.post("/api/v1/auth/login", json={"password": "changeme"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert "expires_at" in body
    # And the session cookie should be set httpOnly.
    set_cookie = resp.headers.get("set-cookie", "")
    assert "passion_session=" in set_cookie
    assert "HttpOnly" in set_cookie


def test_login_with_wrong_password_returns_401(test_client):
    resp = test_client.post("/api/v1/auth/login", json={"password": "nope"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "invalid_password"


def test_me_without_token_returns_401(test_client):
    resp = test_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_bearer_token_returns_identity(test_client):
    token = test_client.post("/api/v1/auth/login", json={"password": "changeme"}).json()[
        "access_token"
    ]
    resp = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["authenticated"] is True
    assert body["system_access_granted"] is False


def test_me_with_invalid_token_returns_401(test_client):
    resp = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert resp.status_code == 401


def test_system_unlock_grants_system_access(test_client):
    token = test_client.post("/api/v1/auth/login", json={"password": "changeme"}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    resp = test_client.post(
        "/api/v1/auth/system-unlock",
        headers=headers,
        json={"system_password": "changeme"},
    )
    assert resp.status_code == 200
    assert resp.json()["system_access_granted"] is True


def test_system_unlock_rejects_wrong_password(test_client):
    token = test_client.post("/api/v1/auth/login", json={"password": "changeme"}).json()[
        "access_token"
    ]
    resp = test_client.post(
        "/api/v1/auth/system-unlock",
        headers={"Authorization": f"Bearer {token}"},
        json={"system_password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.parametrize("path", ["/api/v1/auth/me"])
def test_protected_routes_reject_missing_auth(test_client, path):
    assert test_client.get(path).status_code == 401
