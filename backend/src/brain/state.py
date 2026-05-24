"""Brain state definition for the LangGraph orchestrator.

The state flows through the think -> plan -> execute -> reflect nodes.
See Flow 4 (autonomous brain cycle).
"""

from __future__ import annotations

from typing import TypedDict


class BrainState(TypedDict, total=False):
    """Shared state carried across the brain cycle nodes."""

    trigger: str            # 'scheduler' | 'event'
    context: dict           # gathered world state (THINK)
    plan: list[dict]        # prioritized actions (PLAN)
    executed_action: dict   # the single action run this cycle (EXECUTE)
    reflection: str         # learnings to store in memory (REFLECT)
