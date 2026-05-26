# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps: psycopg2/asyncpg builds + nodejs/npm so the backend can spawn
# MCP servers (hevy-mcp, cronometer-mcp) as stdio subprocesses (ADR-002).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .

COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
COPY config ./config

# Default command runs the API; compose overrides for celery worker/beat.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
