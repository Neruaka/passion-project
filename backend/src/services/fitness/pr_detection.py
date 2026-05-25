"""Personal Record detection (US-012).

Pure business logic: given workout sets, detect the 4 PR types
(one_rep_max via Epley, reps_at_load, session_volume, muscle_group_volume).
No DB or LLM dependency -> unit-testable to 90%+ (NFR-TEST-002).
"""

from __future__ import annotations


def estimate_one_rep_max(weight_kg: float, reps: int) -> float:
    """Epley formula: 1RM = weight * (1 + reps / 30)."""
    return weight_kg * (1 + reps / 30)


def detect_prs(
    sets: list[dict[str, object]], history: dict[str, object]
) -> list[dict[str, object]]:
    """Detect all PRs in a set of logged sets against historical bests.

    TODO(sprint-3): implement the 4 PR types with warmup/failure filtering.
    """
    raise NotImplementedError("Implement in sprint 3 (US-012)")
