"""Auth endpoints (US-001). See API_CONTRACTS.md > AUTH.

POST /auth/login, POST /auth/logout, GET /auth/me, POST /auth/system-unlock.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Response, status

from src.api.dependencies import SESSION_COOKIE, PrincipalDep, SettingsDep
from src.core.security import issue_jwt, verify_password
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    SystemUnlockRequest,
    SystemUnlockResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# 2nd-password (system) unlock lifetime — short by design (API_CONTRACTS).
_SYSTEM_UNLOCK_TTL = timedelta(hours=1)


def _set_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        expires=expires_at,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, settings: SettingsDep, response: Response) -> LoginResponse:
    if not verify_password(payload.password, settings.admin_password_hash):
        # TODO(sprint-1+): rate-limit via Redis (5 attempts / 15min — NFR-SEC-001).
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_password")

    expires_at = datetime.now(tz=UTC) + timedelta(days=settings.jwt_expiry_days)
    token = issue_jwt("admin", expires_at, settings.jwt_secret, scope="user")
    _set_session_cookie(response, token, expires_at)
    return LoginResponse(access_token=token, expires_at=expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, _: PrincipalDep) -> Response:
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=MeResponse)
def me(principal: PrincipalDep) -> MeResponse:
    return MeResponse(
        authenticated=True,
        session_expires_at=principal.expires_at,
        system_access_granted=principal.has_system_access,
    )


@router.post("/system-unlock", response_model=SystemUnlockResponse)
def system_unlock(
    payload: SystemUnlockRequest,
    principal: PrincipalDep,
    settings: SettingsDep,
    response: Response,
) -> SystemUnlockResponse:
    if not verify_password(payload.system_password, settings.system_password_hash):
        # TODO(sprint-1+): 3-fail / 1h lockout (NFR-SEC-001).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_system_password"
        )

    unlock_until = datetime.now(tz=UTC) + _SYSTEM_UNLOCK_TTL
    # Re-issue the JWT carrying the system unlock window so subsequent requests
    # (with the same cookie) get system access until unlock_until.
    new_token = issue_jwt(
        principal.subject,
        principal.expires_at,
        settings.jwt_secret,
        scope=principal.scope,
        extra={"system_unlock_until": int(unlock_until.timestamp())},
    )
    _set_session_cookie(response, new_token, principal.expires_at)
    return SystemUnlockResponse(system_access_granted=True, expires_at=unlock_until)
