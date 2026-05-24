"""Custom application exceptions and FastAPI exception handlers."""

from __future__ import annotations


class PassionError(Exception):
    """Base class for all application errors."""


class BudgetExceededError(PassionError):
    """Raised when the daily LLM budget cap is hit (NFR-COST-002)."""


class GuardrailViolationError(PassionError):
    """Raised when an LLM output violates a hard guardrail (US-016)."""


class IntegrationError(PassionError):
    """Raised when an external integration (Hevy, Cronometer) fails."""


class SyncError(IntegrationError):
    """Raised when a data sync fails after all retries."""
