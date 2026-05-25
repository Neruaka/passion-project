"""Celery application entrypoint (workers + beat).

Run worker:  celery -A src.celery_app worker --loglevel=info
Run beat:    celery -A src.celery_app beat --loglevel=info

Both run from the same image (one Docker image, two compose services) per the
container simplification decision.
"""

from __future__ import annotations

from celery import Celery

from src.core.config import get_settings

settings = get_settings()

app = Celery(
    "passion",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# TODO(sprint-1+): autodiscover tasks in src.jobs, load beat schedule from
# src.jobs.schedule (cf. ROADMAP s1).
# app.autodiscover_tasks(["src.jobs"])
# from src.jobs.schedule import beat_schedule
# app.conf.beat_schedule = beat_schedule

app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)
