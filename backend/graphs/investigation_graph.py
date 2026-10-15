import logging
import uuid
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END

from backend.agents.agent_state import InvestigationState
from backend.agents.supervisor import supervisor_agent_plan, supervisor_agent_route
from backend.agents.intake import transaction_intake_agent
from backend.agents.data_quality import data_quality_agent
from backend.agents.fraud_detector import fraud_detection_agent
from backend.agents.risk_assessment import risk_assessment_agent
from backend.agents.investigator import investigation_agent
from backend.agents.policy_compliance import policy_compliance_agent
from backend.agents.explainability import explainability_agent
from backend.agents.audit_reporter import audit_reporting_agent
from backend.observability.tracer import tracer, record_custom_span

logger = logging.getLogger(__name__)

def build_investigation_graph() -> StateGraph:
    """
    Constructs the 9-Agent LangGraph workflow with explicit typed state,
    conditional risk routing, policy grounding, and human-checkpoint determination.
    """
    builder = StateGraph(InvestigationState)

    # Register Nodes
    builder.add_node("supervisor_plan", supervisor_agent_plan)
    builder.add_node("intake", transaction_intake_agent)
    builder.add_node("data_quality", data_quality_agent)
    builder.add_node("fraud_detector", fraud_detection_agent)
    builder.add_node("risk_assessment", risk_assessment_agent)
    builder.add_node("investigator", investigation_agent)
    builder.add_node("policy_compliance", policy_compliance_agent)
    builder.add_node("explainability", explainability_agent)
    builder.add_node("audit_reporter", audit_reporting_agent)

    # Set Entry Point
    builder.set_entry_point("supervisor_plan")

    # Linear Core Ingestion & Analysis Path
    builder.add_edge("supervisor_plan", "intake")
    builder.add_edge("intake", "data_quality")
    builder.add_edge("data_quality", "fraud_detector")
    builder.add_edge("fraud_detector", "risk_assessment")

    # Conditional Branch based on Risk Severity
    builder.add_conditional_edges(
        "risk_assessment",
        supervisor_agent_route,
        {
            "ROUTE_FAST_TRACK": "audit_reporter",
            "ROUTE_FULL_INVESTIGATION": "investigator"
        }
    )

    # In-depth Forensic Path
    builder.add_edge("investigator", "policy_compliance")
    builder.add_edge("policy_compliance", "explainability")
    builder.add_edge("explainability", "audit_reporter")

    # Exit
    builder.add_edge("audit_reporter", END)

    return builder.compile()

# Singleton compiled workflow instance
investigation_workflow = build_investigation_graph()

def execute_investigation(
    transaction_id: Optional[int] = None,
    raw_transaction_data: Optional[Dict[str, Any]] = None,
    user_query: Optional[str] = None,
    user_role: str = "analyst"
) -> InvestigationState:
    """
    Executes the full multi-agent investigation workflow with OpenTelemetry tracing.
    """
    correlation_id = str(uuid.uuid4())
    initial_state: InvestigationState = {
        "correlation_id": correlation_id,
        "transaction_id": transaction_id,
        "raw_transaction_data": raw_transaction_data or {},
        "user_query": user_query,
        "current_user_role": user_role,
        "intake_status": "PENDING",
        "validated_transaction": {},
        "data_quality_report": {},
        "model_prediction": {},
        "risk_assessment": {},
        "investigation_evidence": {},
        "policy_citations": [],
        "explanation_summary": "",
        "feature_attributions": [],
        "workflow_next_step": "",
        "requires_human_review": False,
        "review_checkpoint_reason": None,
        "final_report": {},
        "timeline": [],
        "tokens_consumed": 0,
        "error": None
    }

    with tracer.start_as_current_span("langgraph_investigation_workflow") as span:
        span.set_attribute("finguard.correlation_id", correlation_id)
        span.set_attribute("finguard.transaction_id", str(transaction_id or "ad-hoc"))
        span.set_attribute("finguard.user_role", user_role)

        try:
            final_state = investigation_workflow.invoke(initial_state)
            span.set_attribute("finguard.risk_score", final_state.get("risk_assessment", {}).get("composite_risk_score", 0.0))
            span.set_attribute("finguard.requires_human_review", final_state.get("requires_human_review", False))
            
            # Record in-memory span trace for UI observability
            total_duration = sum(step["duration_ms"] for step in final_state.get("timeline", []))
            record_custom_span(
                name="LangGraph:MultiAgentInvestigation",
                duration_ms=total_duration,
                attributes={
                    "correlation_id": correlation_id,
                    "agents_invoked": len(final_state.get("timeline", [])),
                    "risk_score": final_state.get("risk_assessment", {}).get("composite_risk_score", 0.0),
                    "human_review": final_state.get("requires_human_review", False)
                }
            )
            return final_state
        except Exception as e:
            logger.error(f"Investigation workflow failed: {e}", exc_info=True)
            initial_state["error"] = str(e)
            span.record_exception(e)
            return initial_state
