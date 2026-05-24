"""Unit tests for PR detection (US-012). Pure functions, no DB/LLM."""

from __future__ import annotations

import pytest

from src.services.fitness.pr_detection import estimate_one_rep_max


def test_epley_one_rep_max():
    # Epley: 90kg x 5 reps -> 90 * (1 + 5/30) = 105kg
    assert estimate_one_rep_max(90, 5) == pytest.approx(105.0)


def test_epley_single_rep_close_to_weight():
    # 1 rep -> 1RM slightly above the weight
    assert estimate_one_rep_max(100, 1) == pytest.approx(100 * (1 + 1 / 30))
