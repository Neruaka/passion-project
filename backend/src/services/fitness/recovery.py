"""Muscle-group recovery state (US-011).

Pure logic: takes recent workouts + a recovery profile, returns a per-muscle
status `ready | recovering | heavy_fatigue | neglected`.

Recovery rules of thumb (tuneable):
  * 0-24h since last hit  → recovering
  * 24-48h on a hit muscle → recovering (still sore)
  * >= 7 days untrained    → neglected
  * Last week's volume > 2x median → heavy_fatigue
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

RecoveryState = Literal["ready", "recovering", "heavy_fatigue", "neglected"]


@dataclass(slots=True)
class MuscleHit:
    muscle_group: str
    achieved_at: datetime
    volume_kg: float


@dataclass(slots=True)
class MuscleStatus:
    muscle_group: str
    recovery_state: RecoveryState
    days_since_last_trained: float
    recovery_left_days: float
    volume_last_7d: float
    frequency_last_30d: int
    flag: str | None  # "neglected" | "high_load" | None


_DEFAULT_RECOVERY_DAYS: dict[str, float] = {
    # By muscle group, how long until "ready" after a hit.
    "chest": 2.5,
    "back": 2.5,
    "shoulders": 2.0,
    "lats": 2.5,
    "biceps": 2.0,
    "triceps": 2.0,
    "forearms": 1.5,
    "quadriceps": 3.0,
    "hamstrings": 3.0,
    "glutes": 2.5,
    "calves": 1.5,
    "abdominals": 1.0,
    "lower_back": 3.5,
    "upper_back": 2.5,
    "traps": 2.0,
    "neck": 1.0,
    "adductors": 2.0,
    "cardio": 0.5,
    "full_body": 3.0,
}

_NEGLECT_DAYS = 7.0


def compute_muscle_statuses(
    hits: list[MuscleHit],
    *,
    now: datetime | None = None,
    tracked_groups: list[str] | None = None,
    recovery_days: dict[str, float] | None = None,
) -> list[MuscleStatus]:
    """Compute the recovery status of each tracked muscle group."""
    now = now or datetime.now(tz=UTC)
    recovery_days = recovery_days or _DEFAULT_RECOVERY_DAYS
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    by_group: dict[str, list[MuscleHit]] = defaultdict(list)
    for h in hits:
        by_group[h.muscle_group].append(h)
    groups = tracked_groups or list(by_group.keys()) or list(recovery_days.keys())

    # Median weekly volume as the baseline for "high_load".
    weekly_volumes_all = [
        sum(h.volume_kg for h in hh if h.achieved_at >= week_ago) for hh in by_group.values()
    ]
    weekly_volumes_all = [v for v in weekly_volumes_all if v > 0]
    median_weekly = (
        sorted(weekly_volumes_all)[len(weekly_volumes_all) // 2] if weekly_volumes_all else 0.0
    )

    statuses: list[MuscleStatus] = []
    for group in groups:
        group_hits = sorted(by_group.get(group, []), key=lambda h: h.achieved_at)
        last_trained = group_hits[-1].achieved_at if group_hits else None
        if last_trained is None:
            statuses.append(
                MuscleStatus(
                    muscle_group=group,
                    recovery_state="neglected",
                    days_since_last_trained=float("inf"),
                    recovery_left_days=0.0,
                    volume_last_7d=0.0,
                    frequency_last_30d=0,
                    flag="neglected",
                )
            )
            continue
        days_since = (now - last_trained).total_seconds() / 86400
        need = recovery_days.get(group, 2.5)
        recovery_left = max(0.0, need - days_since)
        vol_7d = sum(h.volume_kg for h in group_hits if h.achieved_at >= week_ago)
        freq_30d = sum(1 for h in group_hits if h.achieved_at >= month_ago)

        # Categorize state
        if days_since >= _NEGLECT_DAYS:
            state: RecoveryState = "neglected"
            flag: str | None = "neglected"
        elif median_weekly and vol_7d > 2 * median_weekly:
            state = "heavy_fatigue"
            flag = "high_load"
        elif recovery_left > 0:
            state = "recovering"
            flag = None
        else:
            state = "ready"
            flag = None

        statuses.append(
            MuscleStatus(
                muscle_group=group,
                recovery_state=state,
                days_since_last_trained=round(days_since, 2),
                recovery_left_days=round(recovery_left, 2),
                volume_last_7d=round(vol_7d, 2),
                frequency_last_30d=freq_30d,
                flag=flag,
            )
        )
    return statuses
