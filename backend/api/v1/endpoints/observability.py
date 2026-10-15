import os
import json
from fastapi import APIRouter, Depends
from backend.observability.metrics import metrics_collector
from backend.observability.tracer import get_recent_traces
from backend.core.config import settings
from backend.security.jwt_auth import get_current_user
from backend.security.rbac import check_permission, verify_role_permission

router = APIRouter(prefix="/observability", tags=["Observability & Telemetry"])

@router.get("/summary")
def get_observability_summary(current_user: dict = Depends(get_current_user)):
    # Verify that the user has at minimum health view permission
    check_permission(current_user["role"], "view_health")
    
    role = current_user["role"]
    has_observability = verify_role_permission(role, "view_observability")
    has_detailed_telemetry = verify_role_permission(role, "view_detailed_telemetry")

    # Active model version
    metrics_path = os.path.join(settings.MODEL_ARTIFACTS_DIR, "metrics.json")
    model_version = "v1.2.0-rf-enterprise"
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                model_version = json.load(f).get("model_version", model_version)
        except Exception:
            pass

    metrics = metrics_collector.get_summary()

    # Tiered response based on documented RBAC matrix
    if has_detailed_telemetry:
        traces = get_recent_traces(limit=25)
        return {
            **metrics,
            "access_tier": "ADMINISTRATIVE_TELEMETRY",
            "active_model_version": model_version,
            "telemetry_status": "ACTIVE (OpenTelemetry Tracer + In-Memory Exporter)",
            "otel_service_name": settings.OTEL_SERVICE_NAME,
            "recent_traces": traces
        }
    elif has_observability:
        return {
            **metrics,
            "access_tier": "OPERATIONAL_METRICS",
            "active_model_version": model_version,
            "telemetry_status": "ACTIVE (Operational Metrics Stream)",
            "otel_service_name": settings.OTEL_SERVICE_NAME,
            "recent_traces": [],
            "notice": "Raw OpenTelemetry trace collection is restricted to Administrator accounts."
        }
    else:
        # Standard USER tier: basic service availability and health metrics
        return {
            "uptime_seconds": metrics.get("uptime_seconds", 0),
            "request_count": metrics.get("request_count", 0),
            "error_count": metrics.get("error_count", 0),
            "average_latency_ms": metrics.get("average_latency_ms", 0.0),
            "p95_latency_ms": metrics.get("p95_latency_ms", 0.0),
            "access_tier": "STANDARD_HEALTH",
            "service_status": "HEALTHY",
            "active_model_version": model_version,
            "telemetry_status": "Active (Standard Operational Telemetry)",
            "otel_service_name": settings.OTEL_SERVICE_NAME,
            "recent_traces": [],
            "notice": "Your account role ('USER') has access to basic operational health. Advanced trace analysis is reserved for Analyst and Administrator roles."
        }

