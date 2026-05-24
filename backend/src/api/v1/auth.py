"""Auth endpoints (US-001). See API_CONTRACTS.md > AUTH.

POST /auth/login, POST /auth/logout, GET /auth/me, POST /auth/system-unlock.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

# TODO(sprint-1): implement login/logout/me/system-unlock per API_CONTRACTS.
