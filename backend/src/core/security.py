"""Authentication primitives: bcrypt password hashing and JWT issue/verify.

Implements NFR-SEC-001. Two privilege levels: user (login) and system (admin).
"""

from __future__ import annotations

from datetime import datetime


def hash_password(plain: str) -> str:
    """Hash a password with bcrypt (cost >= 12)."""
    raise NotImplementedError("Implement in sprint 1 (NFR-SEC-001)")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    raise NotImplementedError("Implement in sprint 1 (NFR-SEC-001)")


def issue_jwt(subject: str, expires_at: datetime) -> str:
    """Issue an HS256 JWT."""
    raise NotImplementedError("Implement in sprint 1 (NFR-SEC-001)")


def verify_jwt(token: str) -> dict:
    """Verify and decode a JWT, raising on invalid/expired tokens."""
    raise NotImplementedError("Implement in sprint 1 (NFR-SEC-001)")
