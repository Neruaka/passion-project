"""Unit tests for core.logging — sensitive key redaction (NFR-PRIV-004)."""

from __future__ import annotations

from src.core.logging import SENSITIVE_KEYS, _mask_sensitive


def test_mask_redacts_top_level_sensitive_keys():
    event = {"password": "hunter2", "user": "admin"}
    out = _mask_sensitive(None, None, event)
    assert out["password"] == "***REDACTED***"
    assert out["user"] == "admin"


def test_mask_redacts_nested_sensitive_keys():
    event = {"payload": {"jwt_secret": "abc", "ok": True}}
    out = _mask_sensitive(None, None, event)
    assert out["payload"]["jwt_secret"] == "***REDACTED***"
    assert out["payload"]["ok"] is True


def test_all_sensitive_keys_lowercased():
    # Sanity: the constant should only contain lowercase keys (we match lower()).
    for k in SENSITIVE_KEYS:
        assert k == k.lower()
