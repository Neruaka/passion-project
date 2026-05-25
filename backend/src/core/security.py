"""Authentication primitives: bcrypt password hashing and JWT issue/verify.

Implements NFR-SEC-001. Two privilege levels: user (login) and system (admin).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import bcrypt
import jwt

# bcrypt cost factor per NFR-SEC-001 (>=12).
_BCRYPT_COST = 12

# JWT algorithm. HS256 is sufficient for a single-user, single-issuer system.
_JWT_ALGORITHM = "HS256"


class InvalidTokenError(Exception):
    """Raised when a JWT is invalid, malformed, or expired."""


def hash_password(plain: str) -> str:
    """Hash a password with bcrypt (cost >= 12)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(_BCRYPT_COST)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash. Constant-time."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def issue_jwt(
    subject: str,
    expires_at: datetime,
    secret: str,
    *,
    scope: str = "user",
    extra: dict[str, Any] | None = None,
) -> str:
    """Issue an HS256 JWT.

    Args:
        subject: identifier of the principal (e.g. "admin").
        expires_at: absolute expiry (timezone-aware UTC).
        secret: signing secret (from settings.jwt_secret).
        scope: "user" or "system" (see API_CONTRACTS > AUTH levels).
        extra: additional claims to merge into the payload.
    """
    now = datetime.now(tz=UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "scope": scope,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret, algorithm=_JWT_ALGORITHM)


def verify_jwt(token: str, secret: str) -> dict[str, Any]:
    """Verify and decode a JWT, raising InvalidTokenError on failure."""
    try:
        return jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
    except jwt.PyJWTError as e:
        raise InvalidTokenError(str(e)) from e
