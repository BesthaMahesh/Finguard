import time
from datetime import datetime, timezone
from backend.agents.agent_state import InvestigationState, AgentTimelineStep

def supervisor_agent_plan(state: InvestigationState) -> InvestigationState:
    """
    Supervisor Agent (Initial Step):
    Interprets request, assigns correlation ID, and coordinates workflow execution path.
    """
    start_time = time.time()
    role = state.get("current_user_role", "analyst")
    correlation_id = state.get("correlation_id", "")
    
    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))
    timeline.append(AgentTimelineStep(
        agent="Supervisor Agent",
        status="PLANNING_INITIATED",
        duration_ms=round(duration, 2),
        output_summary=f"Orchestrating investigation workflow [Role: {role}, Correlation: {correlation_id[:8]}...]",
        timestamp=datetime.now(timezone.utc).isoformat()
    ))

    return {
        **state,
        "workflow_next_step": "INTAKE",
        "timeline": timeline
    }

def supervisor_agent_route(state: InvestigationState) -> str:
    """
    Conditional routing node:
    Determines if additional in-depth investigation and human review checkpoint are required.
    CRITICAL POLICY: If any data quality flags, ledger variances, or rule violations exist,
    the workflow MUST route to full forensic investigation (Investigation and Policy agents NOT skipped).
    """
    risk = state.get("risk_assessment", {})
    score = float(risk.get("composite_risk_score", 0.0))
    
    dq = state.get("data_quality_report", {})
    dq_flags = dq.get("flags", [])
    
    prediction = state.get("model_prediction", {})
    rule_flags_raw = prediction.get("rule_flags", [])
    rule_flags = [r for r in rule_flags_raw if r.get("rule_id") != "SAFEGUARD_VERIFIED_MERCHANT"]

    # Fast-track only when low risk score (< 30.0) AND completely free of data quality or rule flags
    if score < 30.0 and not dq_flags and not rule_flags:
        return "ROUTE_FAST_TRACK"
    
    # Elevated risk, data quality issues, or rule flags proceed through full forensic track
    return "ROUTE_FULL_INVESTIGATION"
