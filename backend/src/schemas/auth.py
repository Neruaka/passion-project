"""Auth request/response schemas. See API_CONTRACTS.md > AUTH."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class MeResponse(BaseModel):
    authenticated: bool
    session_expires_at: datetime
    system_access_granted: bool


class SystemUnlockRequest(BaseModel):
    system_password: str = Field(min_length=1, max_length=200)


class SystemUnlockResponse(BaseModel):
    system_access_granted: bool
    expires_at: datetime
