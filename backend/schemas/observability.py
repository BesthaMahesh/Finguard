from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ObservabilitySummaryResponse(BaseModel):
    total_requests: int
    total_errors: int
    error_rate_pct: float
    avg_api_latency_ms: float
    p95_api_latency_ms: float
    avg_ml_inference_ms: float
    total_agent_workflows: int
    avg_agent_workflow_ms: float
    total_tokens_used: int
    estimated_llm_cost_usd: float
    slo_targets: Dict[str, Any]
    active_model_version: str
    telemetry_status: str = "ACTIVE (OpenTelemetry Tracer + In-Memory Exporter)"
    recent_traces: List[Dict[str, Any]]
