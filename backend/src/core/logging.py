"""Structured logging setup using structlog (JSON output).

Implements NFR-OBS-002: all logs are structured JSON with mandatory fields and
automatic masking of sensitive keys (passwords, tokens, API keys).
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor, WrappedLogger

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

_MASK = "***REDACTED***"


def _mask_sensitive(_logger: WrappedLogger, _method: str, event_dict: EventDict) -> EventDict:
    """structlog processor that redacts SENSITIVE_KEYS at any depth."""

    def walk(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                k: (_MASK if k.lower() in SENSITIVE_KEYS else walk(v)) for k, v in value.items()
            }
        if isinstance(value, list):
            return [walk(v) for v in value]
        return value

    masked: EventDict = walk(event_dict)
    return masked


def _add_trace_context(_logger: WrappedLogger, _method: str, event_dict: EventDict) -> EventDict:
    """Inject the current OpenTelemetry trace_id / span_id if available."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context() if span else None
        if ctx and ctx.is_valid:
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
    except Exception:
        pass
    return event_dict


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Configure structlog processors and stdlib logging."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # stdlib root logger to stdout (so Docker / Promtail can pick it up).
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_trace_context,
        _mask_sensitive,
    ]

    renderer: Processor = (
        structlog.processors.JSONRenderer()
        if json_output
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
