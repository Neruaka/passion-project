"""OpenTelemetry tracing + Prometheus metrics initialization.

Implements NFR-OBS-003 (metrics) and NFR-OBS-004 (tracing). Auto-instruments
FastAPI, SQLAlchemy, Celery, and HTTPX. Exposes custom business metrics
(llm_tokens_used_total, llm_cost_eur_total, sync_success_total, etc).
"""

from __future__ import annotations


def setup_observability(service_name: str) -> None:
    """Initialize tracing + metrics. Call once at app startup.

    TODO(sprint-1): configure OTel exporter to Tempo, Prometheus client,
    custom metric collectors.
    """
    raise NotImplementedError("Implement in sprint 1 (NFR-OBS-003/004)")
