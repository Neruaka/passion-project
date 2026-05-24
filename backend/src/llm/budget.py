"""Budget tracker enforcing the daily LLM cost cap (NFR-COST-002).

Hard cap: 1.5 EUR/day, 45 EUR/month. Resets at midnight. Falls back to Gemini
Flash free tier when the Anthropic budget is exhausted.
"""

from __future__ import annotations

from .router import TaskComplexity


class BudgetTracker:
    def can_afford(self, complexity: TaskComplexity, max_tokens: int) -> bool:
        """Return True if the projected call fits within the daily budget."""
        raise NotImplementedError("Implement in sprint 2 (NFR-COST-002)")
