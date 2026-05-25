"""OpenTelemetry tracing + Prometheus metrics initialization.

Implements NFR-OBS-003 (metrics) and NFR-OBS-004 (tracing). Auto-instruments
FastAPI and exposes a /metrics endpoint with custom business metrics
(passion_api_up, passion_http_requests_total, etc.).
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Gauge, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# --- Prometheus metrics (exposed at /metrics for direct scraping) ---
API_UP = Gauge("passion_api_up", "1 if the API process is up.")
HTTP_REQUESTS = Counter(
    "passion_http_requests_total",
    "Total HTTP requests, labelled.",
    ["method", "path", "status"],
)


class _PrometheusMiddleware(BaseHTTPMiddleware):
    """Increment HTTP_REQUESTS for every served request."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        # Use the route template (/api/v1/auth/login) when available; otherwise
        # use the raw path. Avoids cardinality explosion from IDs in URLs.
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        HTTP_REQUESTS.labels(
            method=request.method,
            path=path,
            status=str(response.status_code),
        ).inc()
        return response


def setup_observability(app: FastAPI, service_name: str = "passion-backend") -> None:
    """Initialize OTel (traces + metrics) and mount /metrics on the app.

    OTLP HTTP endpoint comes from OTEL_EXPORTER_OTLP_ENDPOINT (e.g.
    http://grafana-lgtm:4318). If unset, OTel exporters become no-ops but the
    Prometheus /metrics endpoint still works.
    """
    resource = Resource.create({SERVICE_NAME: service_name})
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    # Traces -> Tempo (via OTLP HTTP)
    tracer_provider = TracerProvider(resource=resource)
    if otlp_endpoint:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces"))
        )
    trace.set_tracer_provider(tracer_provider)

    # Metrics -> Mimir (via OTLP HTTP) — alongside Prometheus /metrics
    readers = []
    if otlp_endpoint:
        readers.append(
            PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=f"{otlp_endpoint}/v1/metrics"),
                export_interval_millis=15_000,
            )
        )
    meter_provider = MeterProvider(resource=resource, metric_readers=readers)
    metrics.set_meter_provider(meter_provider)

    # Auto-instrument FastAPI (creates spans + http_server_* metrics)
    FastAPIInstrumentor.instrument_app(app)

    # Prometheus request counter middleware (cheap, in-process)
    app.add_middleware(_PrometheusMiddleware)

    # Expose Prometheus exposition format
    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint() -> Response:
        return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

    # Mark the process as up (both for direct /metrics scrape and OTel push)
    API_UP.set(1)

    meter = metrics.get_meter(service_name)

    def _api_up_callback(_: CallbackOptions) -> list[Observation]:
        return [Observation(1)]

    meter.create_observable_gauge(
        name="passion_api_up",
        description="1 if the API process is up.",
        callbacks=[_api_up_callback],
    )
