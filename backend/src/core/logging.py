"""Structured logging setup using structlog (JSON output).

Implements NFR-OBS-002: all logs are structured JSON with mandatory fields and
automatic masking of sensitive keys (passwords, tokens, API keys).
"""

from __future__ import annotations

# Keys whose values must always be masked in logs (NFR-PRIV-004).
SENSITIVE_KEYS = frozenset(
    {
        "password",
        "system_password",
        "jwt_secret",
        "anthropic_api_key",
        "gemini_api_key",
        "hevy_api_key",
        "health_ingest_token",
        "access_token",
        "authorization",
    }
)


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Configure structlog processors and stdlib logging.

    TODO(sprint-1): wire structlog processors, mask SENSITIVE_KEYS, add
    trace_id correlation from OpenTelemetry context.
    """
    raise NotImplementedError("Implement in sprint 1 (US-005, NFR-OBS-002)")
