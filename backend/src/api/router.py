"""Main API router aggregating all v1 domain routers."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.v1 import analysis, auth, workouts

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(workouts.router)
api_router.include_router(analysis.router)

# TODO(sprint-3+): include each domain router as it is implemented.
# from .v1 import dashboard, coach, ...
