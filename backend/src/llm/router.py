"""LLM Router — 3-tier routing (Gemini Flash / Claude Haiku / Claude Sonnet).

Implements ADR-002 and NFR-COST-004. Routes each call by complexity, enforces
the budget (NFR-COST-002), applies guardrails, and tracks cost/tokens.
"""

from __future__ import annotations

from enum import StrEnum


class TaskComplexity(StrEnum):
    SIMPLE = "simple"  # -> Gemini Flash (free)
    MEDIUM = "medium"  # -> Claude Haiku
    COMPLEX = "complex"  # -> Claude Sonnet


class LLMRouter:
    """Routes LLM calls across providers with budget + guardrail enforcement."""

    async def call(
        self,
        prompt: str,
        complexity: TaskComplexity,
        max_tokens: int = 1000,
        sensitive: bool = False,
        force_model: str | None = None,
    ) -> dict:
        """Route and execute an LLM call.

        TODO(sprint-2): budget check -> model selection -> input guardrails ->
        provider call -> output guardrails -> cost tracking -> retry/fallback.
        """
        raise NotImplementedError("Implement in sprint 2 (ADR-002, NFR-COST-004)")
