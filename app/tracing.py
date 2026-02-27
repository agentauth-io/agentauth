"""
AgentAuth OpenTelemetry Tracing

End-to-end distributed tracing for observability.
Exports traces to OTLP-compatible backends (Jaeger, Grafana Tempo, etc.)
"""

import logging
import os
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode

from app.config import get_settings

settings = get_settings()

# Global tracer
_tracer: trace.Tracer | None = None
_initialized: bool = False


def init_tracing(app=None, service_name: str = "agentauth") -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing.

    Call this once at application startup.
    """
    global _tracer, _initialized

    if _initialized:
        return _tracer

    # Create resource with service name
    resource = Resource.create(
        {
            SERVICE_NAME: service_name,
            "service.version": "0.2.0",
            "deployment.environment": settings.environment,
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add exporters based on configuration
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if otlp_endpoint:
        # Use OTLP exporter for production
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logging.info(f"OpenTelemetry: OTLP exporter configured for {otlp_endpoint}")
        except ImportError:
            logging.warning("OpenTelemetry: OTLP exporter not available, using console")
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    elif settings.debug:
        # Use console exporter for development
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logging.debug("OpenTelemetry: Console exporter enabled (debug mode)")

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Instrument libraries
    if app:
        FastAPIInstrumentor.instrument_app(app)
        logging.info("OpenTelemetry: FastAPI instrumented")

    try:
        HTTPXClientInstrumentor().instrument()
        logging.info("OpenTelemetry: HTTPX instrumented")
    except Exception as e:
        # HTTPX instrumentation is optional, log for debugging
        logging.debug(f"OpenTelemetry: Failed to instrument HTTPX: {e}")

    try:
        from app.models.database import engine

        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        logging.info("OpenTelemetry: SQLAlchemy instrumented")
    except Exception as e:
        # SQLAlchemy instrumentation is optional, log for debugging
        logging.debug(f"OpenTelemetry: Failed to instrument SQLAlchemy: {e}")

    _tracer = trace.get_tracer(__name__)
    _initialized = True

    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(__name__)
    return _tracer


@contextmanager
def trace_span(
    name: str, attributes: dict | None = None, record_exception: bool = True
):
    """
    Context manager for creating traced spans.

    Usage:
        with trace_span("validate_token", {"token_id": token.id}):
            # ... do work
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        try:
            yield span
        except Exception as e:
            if record_exception:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def trace_function(name: str | None = None, attributes: dict | None = None):
    """
    Decorator for tracing functions.

    Usage:
        @trace_function("validate_consent")
        async def validate_consent(consent_id: str):
            ...
    """

    def decorator(func):
        import asyncio
        import functools

        span_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_span(span_name, attributes):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_span(span_name, attributes):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def add_span_attributes(**attributes):
    """Add attributes to the current span."""
    span = trace.get_current_span()
    for key, value in attributes.items():
        if value is not None:
            span.set_attribute(key, str(value))


def add_span_event(name: str, attributes: dict | None = None):
    """Add an event to the current span."""
    span = trace.get_current_span()
    span.add_event(name, attributes=attributes or {})


def set_span_error(message: str, exception: Exception | None = None):
    """Mark current span as error."""
    span = trace.get_current_span()
    if exception:
        span.record_exception(exception)
    span.set_status(Status(StatusCode.ERROR, message))


def get_trace_id() -> str | None:
    """Get the current trace ID for correlation."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return None


def get_span_id() -> str | None:
    """Get the current span ID."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return None


# Predefined span names for consistency
class SpanNames:
    """Standard span names for consistent tracing."""

    AUTHORIZE = "authorize_transaction"
    VALIDATE_TOKEN = (
        "validate_token"  # nosec: B105 - This is a span name, not a password
    )
    CHECK_CONSENT = "check_consent"
    APPLY_RULES = "apply_rules"
    VELOCITY_CHECK = "velocity_check"
    CREATE_AUTH_CODE = "create_auth_code"
    VERIFY_AUTH = "verify_authorization"
    CACHE_GET = "cache.get"
    CACHE_SET = "cache.set"
    DB_QUERY = "db.query"
