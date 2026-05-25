"""Unit tests for core.security (NFR-SEC-001)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from src.core.security import (
    InvalidTokenError,
    hash_password,
    issue_jwt,
    verify_jwt,
    verify_password,
)


def test_hash_then_verify_matches():
    hashed = hash_password("hunter2")
    assert verify_password("hunter2", hashed)


def test_verify_rejects_wrong_password():
    hashed = hash_password("hunter2")
    assert not verify_password("not-the-password", hashed)


def test_verify_handles_malformed_hash():
    assert not verify_password("anything", "not-a-real-bcrypt-hash")


def test_jwt_roundtrip_carries_subject_and_scope():
    secret = "test-secret"
    exp = datetime.now(tz=UTC) + timedelta(minutes=5)
    token = issue_jwt("admin", exp, secret, scope="user")
    decoded = verify_jwt(token, secret)
    assert decoded["sub"] == "admin"
    assert decoded["scope"] == "user"


def test_jwt_rejects_wrong_secret():
    exp = datetime.now(tz=UTC) + timedelta(minutes=5)
    token = issue_jwt("admin", exp, "secret-A")
    with pytest.raises(InvalidTokenError):
        verify_jwt(token, "secret-B")


def test_jwt_rejects_expired_token():
    exp = datetime.now(tz=UTC) - timedelta(seconds=1)
    token = issue_jwt("admin", exp, "secret")
    with pytest.raises(InvalidTokenError):
        verify_jwt(token, "secret")


def test_jwt_extra_claims_survive_roundtrip():
    exp = datetime.now(tz=UTC) + timedelta(minutes=5)
    token = issue_jwt("admin", exp, "secret", extra={"system_unlock_until": 1234567890})
    decoded = verify_jwt(token, "secret")
    assert decoded["system_unlock_until"] == 1234567890
