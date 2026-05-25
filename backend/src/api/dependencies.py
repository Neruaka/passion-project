"""Common FastAPI dependencies (auth, settings)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status

from src.core.config import Settings, get_settings
from src.core.security import InvalidTokenError, verify_jwt

SESSION_COOKIE = "passion_session"


class Principal:
    """Authenticated principal extracted from a verified JWT."""

    __slots__ = ("expires_at", "scope", "subject", "system_unlock_until")

    def __init__(
        self,
        subject: str,
        scope: str,
        expires_at: datetime,
        system_unlock_until: datetime | None = None,
    ) -> None:
        self.subject = subject
        self.scope = scope
        self.expires_at = expires_at
        self.system_unlock_until = system_unlock_until

    @property
    def has_system_access(self) -> bool:
        if self.system_unlock_until is None:
            return False
        return self.system_unlock_until > datetime.now(tz=UTC)


SettingsDep = Annotated[Settings, Depends(get_settings)]


def _extract_token(
    authorization: str | None,
    cookie_token: str | None,
) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    if cookie_token:
        return cookie_token
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_token")


def get_current_principal(
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
    session_cookie: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Principal:
    """Authenticate a request via Bearer header OR httpOnly session cookie."""
    token = _extract_token(authorization, session_cookie)
    try:
        payload = verify_jwt(token, settings.jwt_secret)
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token") from e

    unlock_until_ts = payload.get("system_unlock_until")
    return Principal(
        subject=str(payload["sub"]),
        scope=str(payload.get("scope", "user")),
        expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
        system_unlock_until=(
            datetime.fromtimestamp(unlock_until_ts, tz=UTC) if unlock_until_ts else None
        ),
    )


PrincipalDep = Annotated[Principal, Depends(get_current_principal)]


def require_system_access(principal: PrincipalDep) -> Principal:
    """Dependency for `[system]` routes (NFR-SEC-001 — 2nd password)."""
    if not principal.has_system_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="system_unlock_required")
    return principal
