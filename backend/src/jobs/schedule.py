"""Celery Beat schedule (periodic tasks).

Defines the cron-like cadence for autonomous jobs. Loaded by celery_app from
src.jobs.schedule.beat_schedule.

Cadences (see ROADMAP):
  - sync_hevy: every 30 min (US-008)
  - sync_cronometer: hourly (US-018) — sprint 7
  - nightly_analysis: daily 03:30 — sprint 2
  - daily_briefing: configurable hour, default 07:00 — sprint 6
  - refresh_matviews: daily 04:30 — sprint 2
  - brain_cycle: hourly (Flow 4) — sprint 4
  - create_partitions: quarterly check — sprint 7
"""

from __future__ import annotations

from typing import Any

beat_schedule: dict[str, dict[str, Any]] = {
    "sync-hevy-every-30-min": {
        "task": "sync_hevy_workouts",
        "schedule": 30 * 60,  # seconds — 30 min (US-008)
    },
}
