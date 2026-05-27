"""Unit tests for src.integrations.mcp.hevy.normalize_workout (pure)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from src.integrations.mcp.hevy import normalize_workout


def test_normalize_real_hevy_payload():
    """Real Hevy MCP shape: exercise uses `name`, set uses `weight`/`distance`/`duration`."""
    raw = {
        "id": "04a09f63",
        "title": "Entraînement de nuit",
        "startTime": "2026-05-26T16:34:40+00:00",
        "endTime": "2026-05-26T20:53:25+00:00",
        "exercises": [
            {
                "name": "Squat (Smith Machine)",
                "index": 0,
                "notes": "",
                "exerciseTemplateId": "DDCC3821",
                "sets": [
                    {"index": 0, "type": "normal", "weight": 66.8, "reps": 6, "rpe": 8.5},
                    {"index": 1, "type": "normal", "weight": 66.8, "reps": 6, "rpe": 8.5},
                ],
            }
        ],
    }
    dto = normalize_workout(raw)
    assert dto.hevy_id == "04a09f63"
    assert len(dto.exercises) == 1
    ex = dto.exercises[0]
    assert ex.title == "Squat (Smith Machine)"
    assert ex.exercise_template_id == "DDCC3821"
    assert ex.sets[0]["weight_kg"] == 66.8
    assert ex.sets[0]["reps"] == 6
    assert ex.sets[0]["rpe"] == 8.5
    assert ex.sets[0]["set_type"] == "normal"


def test_normalize_minimal_workout():
    raw = {
        "id": "abc123",
        "title": "Push day",
        "startTime": "2026-05-25T10:00:00Z",
        "exercises": [],
    }
    dto = normalize_workout(raw)
    assert dto.hevy_id == "abc123"
    assert dto.title == "Push day"
    assert dto.start_time == datetime(2026, 5, 25, 10, 0, tzinfo=UTC)
    assert dto.exercises == []
    assert dto.raw is raw


def test_normalize_with_exercises_and_sets():
    raw = {
        "id": "abc123",
        "startTime": "2026-05-25T10:00:00Z",
        "exercises": [
            {
                "title": "Bench Press",
                "exerciseTemplateId": "tmpl_bench",
                "supersetId": None,
                "sets": [
                    {"type": "warmup", "weightKg": 40, "reps": 10},
                    {"type": "normal", "weightKg": 80, "reps": 5, "rpe": 8.5},
                ],
            }
        ],
    }
    dto = normalize_workout(raw)
    assert len(dto.exercises) == 1
    ex = dto.exercises[0]
    assert ex.title == "Bench Press"
    assert ex.exercise_template_id == "tmpl_bench"
    assert len(ex.sets) == 2
    assert ex.sets[0]["set_type"] == "warmup"
    assert ex.sets[0]["weight_kg"] == 40
    assert ex.sets[1]["rpe"] == 8.5


def test_normalize_accepts_snake_case_too():
    """Some MCP wrappers serialise snake_case — we tolerate both."""
    raw = {
        "id": "abc",
        "start_time": "2026-05-25T10:00:00Z",
        "exercises": [
            {
                "title": "X",
                "exercise_template_id": "tmpl_x",
                "sets": [{"type": "normal", "weight_kg": 100, "reps": 1}],
            }
        ],
    }
    dto = normalize_workout(raw)
    assert dto.start_time == datetime(2026, 5, 25, 10, 0, tzinfo=UTC)
    assert dto.exercises[0].exercise_template_id == "tmpl_x"
    assert dto.exercises[0].sets[0]["weight_kg"] == 100


def test_normalize_rejects_missing_start_time():
    with pytest.raises(ValueError):
        normalize_workout({"id": "abc", "exercises": []})
