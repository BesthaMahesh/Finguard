import time
from typing import Dict, Any, List
from collections import deque
import threading

class MetricsCollector:
    """
    Collects performance, latency, agent invocations, token usage, and error metrics.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.request_count = 0
        self.error_count = 0
        self.latencies = deque(maxlen=200)
        self.ml_latencies = deque(maxlen=100)
        self.agent_runs = 0
        self.agent_latencies = deque(maxlen=100)
        self.total_tokens_used = 0
        self.estimated_llm_cost_usd = 0.0

    def record_request(self, latency_ms: float, is_error: bool = False):
        with self._lock:
            self.request_count += 1
            if is_error:
                self.error_count += 1
            self.latencies.append(latency_ms)

    def record_ml_inference(self, latency_ms: float):
        with self._lock:
            self.ml_latencies.append(latency_ms)

    def record_agent_run(self, latency_ms: float, tokens_used: int = 0):
        with self._lock:
            self.agent_runs += 1
            self.agent_latencies.append(latency_ms)
            self.total_tokens_used += tokens_used
            # Approx $0.59 per 1M tokens for Llama 3.3 70B on Groq
            self.estimated_llm_cost_usd += (tokens_used / 1_000_000.0) * 0.59

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            avg_latency = round(sum(self.latencies) / max(1, len(self.latencies)), 2)
            p95_latency = round(sorted(self.latencies)[int(len(self.latencies) * 0.95)] if self.latencies else 0.0, 2)
            avg_ml = round(sum(self.ml_latencies) / max(1, len(self.ml_latencies)), 2)
            avg_agent = round(sum(self.agent_latencies) / max(1, len(self.agent_latencies)), 2)
            error_rate = round((self.error_count / max(1, self.request_count)) * 100, 2)

            return {
                "total_requests": self.request_count,
                "total_errors": self.error_count,
                "error_rate_pct": error_rate,
                "avg_api_latency_ms": avg_latency,
                "p95_api_latency_ms": p95_latency,
                "avg_ml_inference_ms": avg_ml,
                "total_agent_workflows": self.agent_runs,
                "avg_agent_workflow_ms": avg_agent,
                "total_tokens_used": self.total_tokens_used,
                "estimated_llm_cost_usd": round(self.estimated_llm_cost_usd, 5),
                "slo_targets": {
                    "api_latency_slo_ms": 250.0,
                    "availability_slo_pct": 99.9,
                    "status": "HEALTHY" if error_rate < 1.0 else "DEGRADED"
                }
            }

metrics_collector = MetricsCollector()
