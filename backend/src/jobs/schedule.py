"""Celery Beat schedule (periodic tasks).

Defines the cron-like cadence for autonomous jobs:
  - sync_hevy: every 30 min (US-008)
  - sync_cronometer: hourly (US-018)
  - nightly_analysis: daily 03:30 (PR/plateau/stats)
  - daily_briefing: configurable hour, default 07:00 (US-006)
  - refresh_matviews: daily 04:30
  - brain_cycle: hourly (Flow 4)
  - create_partitions: quarterly check
"""

from __future__ import annotations

# TODO(sprint-2): define beat_schedule dict consumed by celery_app.
beat_schedule: dict = {}
