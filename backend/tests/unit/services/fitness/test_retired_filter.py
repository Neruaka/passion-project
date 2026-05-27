"""Unit tests for the retired-exercises filter (Sprint 2 fix)."""

from __future__ import annotations

from src.services.fitness.analysis_runner import _filter_retired, _is_retired
from src.services.fitness.plateau import PlateauFinding


def _f(title: str) -> PlateauFinding:
    return PlateauFinding(
        analysis_type="plateau_official",
        exercise_template_id=None,
        exercise_title=title,
        severity="minor",
    )


def test_is_retired_matches_case_insensitively():
    retired = ["Deadlift", "Squat (Barbell)"]
    assert _is_retired("Deadlift (Conventional)", retired) is True
    assert _is_retired("squat (barbell)", retired) is True
    assert _is_retired("Bench Press", retired) is False


def test_is_retired_matches_substring_both_directions():
    """Hevy may write 'Squat (Barre)' for the French user; we tolerate both."""
    retired = ["Squat (Barbell)", "Squat (Barre)"]
    assert _is_retired("Squat (Barre)", retired) is True
    assert _is_retired("Squat", retired) is True  # title is substring of retired entry


def test_is_retired_empty_list_returns_false():
    assert _is_retired("anything", []) is False


def test_filter_retired_drops_matching_findings():
    findings = [_f("Squat (Barbell)"), _f("Bench Press"), _f("Deadlift")]
    out = _filter_retired(findings, ["Deadlift", "Squat"])
    titles = {f.exercise_title for f in out}
    assert titles == {"Bench Press"}


def test_filter_retired_no_op_when_empty_list():
    findings = [_f("Squat (Barbell)")]
    assert _filter_retired(findings, []) == findings
