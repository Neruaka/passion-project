"""Celery application entrypoint (workers + beat).

Run worker:  celery -A src.celery_app worker --loglevel=info
Run beat:    celery -A src.celery_app beat --loglevel=info

Both run from the same image (one Docker image, two compose services) per the
container simplification decision.
"""

from __future__ import annotations

# TODO(sprint-1): instantiate Celery(app), configure broker (Redis),
# autodiscover tasks in src.jobs, load beat schedule from src.jobs.schedule.
