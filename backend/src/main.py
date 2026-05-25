"""FastAPI application entrypoint.

Wires the API router, middleware, exception handlers, observability, and (in
later sprints) the embedded Brain orchestrator.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis

from src.api.router import api_router
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.core.observability import setup_observability
from src.core.security import verify_password
from src.db.session import dispose_engine, init_engine, ping

logger = structlog.get_logger(__name__)

_redis: aioredis.Redis | None = None


def _check_default_admin_password(admin_password_hash: str) -> None:
    """Loud warning at startup if the admin password is still 'changeme'."""
    if verify_password("changeme", admin_password_hash):
        logger.warning(
            "default_admin_password_in_use",
            message=(
                "ADMIN_PASSWORD_HASH is still the default 'changeme'. "
                "Generate a real hash with `python -m scripts.hash_password` "
                "and update backend/.env before exposing this server."
            ),
        )


async def _redis_ping() -> bool:
    if _redis is None:
        return False
    try:
        pong = await _redis.ping()  # type: ignore[misc]
        return bool(pong)
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _redis
    settings = get_settings()

    configure_logging(level=settings.__dict__.get("log_level", "INFO") or "INFO", json_output=True)
    _check_default_admin_password(settings.admin_password_hash)

    init_engine(settings.database_url, echo=settings.debug)
    _redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    logger.info("startup_complete", environment=settings.environment)
    try:
        yield
    finally:
        logger.info("shutdown_begin")
        if _redis is not None:
            await _redis.aclose()
        await dispose_engine()
        logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="PASSION",
        version="0.1.0",
        lifespan=lifespan,
    )

    # In dev the frontend (localhost:3000) calls the backend (localhost:8000)
    # cross-origin. In prod the frontend is served behind Caddy on the same
    # origin and CORS is not needed.
    if settings.environment != "production":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    setup_observability(app, service_name="passion-backend")
    app.include_router(api_router)

    @app.get("/health", tags=["system"], include_in_schema=False)
    async def health() -> JSONResponse:
        db_ok = await ping()
        redis_ok = await _redis_ping()
        ok = db_ok and redis_ok
        body = {
            "status": "ok" if ok else "degraded",
            "db": "ok" if db_ok else "down",
            "redis": "ok" if redis_ok else "down",
            "version": app.version,
        }
        return JSONResponse(body, status_code=200 if ok else 503)

    return app


app = create_app()
