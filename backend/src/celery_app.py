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

app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # By default Celery wraps sys.stdout/stderr in a LoggingProxy that has no
    # .fileno(), which makes asyncio.create_subprocess_exec crash when a task
    # spawns a child process (e.g. McpHevyClient -> npx hevy-mcp). Disable that
    # redirection so child processes inherit the real file descriptors; our
    # structlog logger keeps emitting JSON to stdout regardless.
    worker_redirect_stdouts=False,
)

# Tasks live in src.jobs.tasks; the import below triggers @app.task
# registration. Beat schedule is loaded from src.jobs.schedule.
# autodiscover_tasks is also wired so future task modules under src.jobs.* are
# picked up without editing this file.
app.autodiscover_tasks(["src.jobs"], force=True)

from src.jobs import tasks as _tasks  # noqa: E402, F401  — ensures @app.task runs
from src.jobs.schedule import beat_schedule  # noqa: E402

app.conf.beat_schedule = beat_schedule
