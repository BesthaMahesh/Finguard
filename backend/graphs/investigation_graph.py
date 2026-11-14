import logging
import uuid
import time
from typing import Dict, Any, Optional, AsyncGenerator
from langgraph.graph import StateGraph, END

from backend.agents.agent_state import InvestigationState
from backend.agents.supervisor import supervisor_agent_plan, supervisor_agent_route
from backend.agents.intake import transaction_intake_agent
from backend.agents.data_quality import data_quality_agent
from backend.agents.fraud_detector import fraud_detection_agent
from backend.agents.market_credit_risk import market_credit_risk_agent
from backend.agents.risk_assessment import risk_assessment_agent
from backend.agents.investigator import investigation_agent
from backend.agents.policy_compliance import policy_compliance_agent
from backend.agents.explainability import explainability_agent
from backend.agents.audit_reporter import audit_reporting_agent
from backend.observability.tracer import tracer, record_custom_span

logger = logging.getLogger(__name__)

# Complete metadata registry for all 10 specialized LangGraph agents
AGENT_REGISTRY = [
    {
        "id": "supervisor_plan",
        "label": "Supervisor Agent",
        "role": "Orchestrator: Evaluates intent, assigns correlation ID, and dynamically routes workflow."
    },
    {
        "id": "intake",
        "label": "Transaction Intake Agent",
        "role": "Validator: Validates payload schema, formats decimals, and unpacks account numbers."
    },
    {
        "id": "data_quality",
        "label": "Data Quality Agent",
        "role": "LeakageGuard: Checks balance signs and ensures zero target label leakage."
    },
    {
        "id": "fraud_detector",
        "label": "Fraud Detection Agent",
        "role": "ML Classifier: Runs Random Forest inference and evaluates deterministic fraud rules."
    },
    {
        "id": "market_credit_risk",
        "label": "Market & Credit Risk Agent",
        "role": "Risk Quant: Evaluates portfolio volatility, exposure ratio, and parametric 95% VaR."
    },
    {
        "id": "risk_assessment",
        "label": "Risk Assessment Agent",
        "role": "Score Synthesizer: Blends ML probabilities and rule penalties into a 0-100 composite risk score."
    },
    {
        "id": "investigator",
        "label": "Investigation Agent",
        "role": "Forensic Analyst: Examines rapid balance liquidation deltas and counterparty relationship graphs."
    },
    {
        "id": "policy_compliance",
        "label": "Policy & Compliance Agent",
        "role": "Regulatory RAG: Queries vector store to pull statutory citations (FATF Rec 16, AML-04)."
    },
    {
        "id": "explainability",
        "label": "Explainability Agent",
        "role": "Narrative Generator: Synthesizes TreeSHAP feature attributions and policies into an objective report via Groq LLM."
    },
    {
        "id": "audit_reporter",
        "label": "Audit & Reporting Agent",
        "role": "Ledger Sealer: Packages the forensic docket, masks PII, and seals a SHA-256 chained audit record."
    }
]

def build_investigation_graph() -> StateGraph:
    """
    Constructs the 10-Agent LangGraph workflow with explicit typed state,
    conditional risk routing, policy grounding, and human-checkpoint determination.
    """
    builder = StateGraph(InvestigationState)

    # 1. Register Nodes
    builder.add_node("supervisor_plan", supervisor_agent_plan)
    builder.add_node("intake", transaction_intake_agent)
    builder.add_node("data_quality", data_quality_agent)
    builder.add_node("fraud_detector", fraud_detection_agent)
    builder.add_node("market_credit_risk", market_credit_risk_agent)
    builder.add_node("risk_assessment", risk_assessment_agent)
    builder.add_node("investigator", investigation_agent)
    builder.add_node("policy_compliance", policy_compliance_agent)
    builder.add_node("explainability", explainability_agent)
    builder.add_node("audit_reporter", audit_reporting_agent)

    # 2. Set Entry Point
    builder.set_entry_point("supervisor_plan")

    # 3. Core Linear Ingestion & ML Assessment
    builder.add_edge("supervisor_plan", "intake")
    builder.add_edge("intake", "data_quality")
    builder.add_edge("data_quality", "fraud_detector")
    builder.add_edge("fraud_detector", "market_credit_risk")
    builder.add_edge("market_credit_risk", "risk_assessment")

    # 4. Conditional Branch: Fast-Track (Low Risk < 30) skips Investigator & Policy Compliance
    builder.add_conditional_edges(
        "risk_assessment",
        supervisor_agent_route,
        {
            "ROUTE_FAST_TRACK": "explainability",
            "ROUTE_FULL_INVESTIGATION": "investigator"
        }
    )

    # 5. Deep Investigation Branch
    builder.add_edge("investigator", "policy_compliance")
    builder.add_edge("policy_compliance", "explainability")

    # 6. Exit Convergence
    builder.add_edge("explainability", "audit_reporter")
    builder.add_edge("audit_reporter", END)

    return builder.compile()

# Singleton compiled workflow instance
investigation_workflow = build_investigation_graph()

def create_initial_investigation_state(
    transaction_id: Optional[int] = None,
    raw_transaction_data: Optional[Dict[str, Any]] = None,
    user_query: Optional[str] = None,
    user_role: str = "analyst",
    correlation_id: Optional[str] = None
) -> InvestigationState:
    corr_id = correlation_id or str(uuid.uuid4())
    return {
        "correlation_id": corr_id,
        "transaction_id": transaction_id,
        "raw_transaction_data": raw_transaction_data or {},
        "user_query": user_query,
        "current_user_role": user_role,
        "intake_status": "PENDING",
        "validated_transaction": {},
        "data_quality_report": {},
        "market_credit_risk": {},
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

def execute_investigation(
    transaction_id: Optional[int] = None,
    raw_transaction_data: Optional[Dict[str, Any]] = None,
    user_query: Optional[str] = None,
    user_role: str = "analyst"
) -> InvestigationState:
    """
    Executes the full multi-agent investigation workflow with OpenTelemetry tracing synchronously.
    """
    initial_state = create_initial_investigation_state(
        transaction_id=transaction_id,
        raw_transaction_data=raw_transaction_data,
        user_query=user_query,
        user_role=user_role
    )
    correlation_id = initial_state["correlation_id"]

    with tracer.start_as_current_span("langgraph_investigation_workflow") as span:
        span.set_attribute("finguard.correlation_id", correlation_id)
        span.set_attribute("finguard.transaction_id", str(transaction_id or "ad-hoc"))
        span.set_attribute("finguard.user_role", user_role)

        try:
            final_state = investigation_workflow.invoke(initial_state)
            span.set_attribute("finguard.risk_score", final_state.get("risk_assessment", {}).get("composite_risk_score", 0.0))
            span.set_attribute("finguard.requires_human_review", final_state.get("requires_human_review", False))
            
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
