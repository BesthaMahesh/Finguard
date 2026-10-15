import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from backend.core.config import settings

logger = logging.getLogger(__name__)

# In-memory Trace Store for Observability Center UI
_IN_MEMORY_TRACES: List[Dict[str, Any]] = []
MAX_SAVED_TRACES = 200

class InMemorySpanExporter(SpanExporter):
    def export(self, spans) -> SpanExportResult:
        for span in spans:
            trace_id = format(span.context.trace_id, "032x")
            span_id = format(span.context.span_id, "016x")
            parent_id = format(span.parent.span_id, "016x") if span.parent else None
            
            duration_ms = (span.end_time - span.start_time) / 1_000_000.0 if span.end_time and span.start_time else 0.0
            
            trace_entry = {
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_id": parent_id,
                "name": span.name,
                "duration_ms": round(duration_ms, 2),
                "status": span.status.status_code.name if span.status else "UNSET",
                "attributes": dict(span.attributes) if span.attributes else {},
                "timestamp": datetime.utcfromtimestamp(span.start_time / 1_000_000_000.0).isoformat() if span.start_time else datetime.utcnow().isoformat()
            }
            _IN_MEMORY_TRACES.insert(0, trace_entry)
            if len(_IN_MEMORY_TRACES) > MAX_SAVED_TRACES:
                _IN_MEMORY_TRACES.pop()
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass

# Initialize OpenTelemetry Tracer
resource = Resource.create(attributes={"service.name": settings.OTEL_SERVICE_NAME})
provider = TracerProvider(resource=resource)
provider.add_span_processor(SimpleSpanProcessor(InMemorySpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(settings.OTEL_SERVICE_NAME)

def get_recent_traces(limit: int = 50) -> List[Dict[str, Any]]:
    return _IN_MEMORY_TRACES[:limit]

def record_custom_span(name: str, duration_ms: float, attributes: Dict[str, Any], status: str = "OK"):
    """Allows recorded trace tracking when outside explicit context managers."""
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    entry = {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_id": None,
        "name": name,
        "duration_ms": round(duration_ms, 2),
        "status": status,
        "attributes": attributes,
        "timestamp": datetime.utcnow().isoformat()
    }
    _IN_MEMORY_TRACES.insert(0, entry)
    if len(_IN_MEMORY_TRACES) > MAX_SAVED_TRACES:
        _IN_MEMORY_TRACES.pop()
    return trace_id
