from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes

from auth_app.src.core.config import app_config


def configure_tracer(app) -> None:
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create(
                {ResourceAttributes.SERVICE_NAME: "auth_service"}
            )
        )
    )

    jaeger_exporter = JaegerExporter(
        collector_endpoint=app_config.jaeger_url + "api/traces"
    )

    trace.get_tracer_provider().add_span_processor(  # type: ignore
        BatchSpanProcessor(jaeger_exporter)
    )

    # from opentelemetry.sdk.trace.export import (ConsoleSpanExporter,
    # SimpleSpanProcessor)
    # trace.get_tracer_provider().add_span_processor(
    #     SimpleSpanProcessor(ConsoleSpanExporter())
    # ) # консоль

    FastAPIInstrumentor.instrument_app(app)
