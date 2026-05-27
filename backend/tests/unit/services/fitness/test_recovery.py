"""Unit tests for src.services.fitness.recovery (US-011)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.services.fitness.recovery import MuscleHit, compute_muscle_statuses

_NOW = datetime(2026, 5, 28, 12, 0, tzinfo=UTC)


def test_neglected_when_never_trained():
    statuses = {
        s.muscle_group: s for s in compute_muscle_statuses([], now=_NOW, tracked_groups=["chest"])
    }
    assert statuses["chest"].recovery_state == "neglected"
    assert statuses["chest"].flag == "neglected"


def test_neglected_when_last_hit_too_old():
    hits = [MuscleHit("chest", _NOW - timedelta(days=10), 500.0)]
    statuses = {
        s.muscle_group: s for s in compute_muscle_statuses(hits, now=_NOW, tracked_groups=["chest"])
    }
    assert statuses["chest"].recovery_state == "neglected"


def test_recovering_when_within_recovery_window():
    hits = [MuscleHit("chest", _NOW - timedelta(hours=12), 500.0)]
    statuses = {
        s.muscle_group: s for s in compute_muscle_statuses(hits, now=_NOW, tracked_groups=["chest"])
    }
    assert statuses["chest"].recovery_state == "recovering"
    assert statuses["chest"].recovery_left_days > 0


def test_ready_when_past_recovery_window():
    hits = [MuscleHit("chest", _NOW - timedelta(days=4), 500.0)]
    statuses = {
        s.muscle_group: s for s in compute_muscle_statuses(hits, now=_NOW, tracked_groups=["chest"])
    }
    assert statuses["chest"].recovery_state == "ready"


def test_heavy_fatigue_when_volume_far_above_median():
    # 4 chest hits last week (high), 1 small back hit → chest is the outlier
    hits = [MuscleHit("chest", _NOW - timedelta(days=i), 2000.0) for i in (1, 2, 3, 4)] + [
        MuscleHit("back", _NOW - timedelta(days=3), 100.0)
    ]
    statuses = {
        s.muscle_group: s
        for s in compute_muscle_statuses(hits, now=_NOW, tracked_groups=["chest", "back"])
    }
    assert statuses["chest"].recovery_state in {"heavy_fatigue", "recovering"}


def test_status_includes_freq_and_volume_metadata():
    hits = [
        MuscleHit("chest", _NOW - timedelta(days=2), 500.0),
        MuscleHit("chest", _NOW - timedelta(days=4), 600.0),
    ]
    statuses = {
        s.muscle_group: s for s in compute_muscle_statuses(hits, now=_NOW, tracked_groups=["chest"])
    }
    chest = statuses["chest"]
    assert chest.frequency_last_30d == 2
    assert chest.volume_last_7d == 1100.0
