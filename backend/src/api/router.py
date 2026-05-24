"""Main API router aggregating all v1 domain routers."""

from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# TODO(sprint-1+): include each domain router as it is implemented.
# from .v1 import auth, dashboard, workouts, ...
# api_router.include_router(auth.router)
