"""FastAPI application entrypoint.

Wires the API router, middleware, exception handlers, observability, and the
embedded Brain orchestrator (embedded in the API process for the MVP per
ADR-003 / C4 L2; separable into its own service in Phase 4+).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: init observability, DB, brain scheduler.

    TODO(sprint-1): setup_observability, create engine, start brain loop.
    """
    yield


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="PASSION",
        version="0.1.0",
        lifespan=lifespan,
    )
    # TODO(sprint-1): app.include_router(api_router), add middleware,
    # register exception handlers, mount WebSocket.
    return app


app = create_app()
