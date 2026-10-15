import time
from datetime import datetime
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
        timestamp=datetime.utcnow().isoformat()
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
    """
    risk = state.get("risk_assessment", {})
    score = risk.get("composite_risk_score", 0.0)
    
    # If transaction is LOW risk (e.g. routine merchant payment < 30 score),
    # route directly to reporting to optimize latency and token costs
    if score < 30.0:
        return "ROUTE_FAST_TRACK"
    
    # Medium, High, or Critical risk proceeds through full deep investigation & policy grounding
    return "ROUTE_FULL_INVESTIGATION"
