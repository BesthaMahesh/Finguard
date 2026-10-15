import time
from datetime import datetime
from backend.agents.agent_state import InvestigationState, AgentTimelineStep

def risk_assessment_agent(state: InvestigationState) -> InvestigationState:
    """
    Synthesizes model predictions, rule violations, and operational risk priority.
    Determines if human-in-the-loop review is mandatory.
    """
    start_time = time.time()
    prediction = state.get("model_prediction", {})
    risk_score = prediction.get("risk_score", 0.0)
    risk_level = prediction.get("risk_level", "LOW")
    requires_human_review = prediction.get("requires_human_review", False)

    checkpoint_reason = None
    if requires_human_review:
        if risk_score >= 85.0:
            checkpoint_reason = "CRITICAL Risk Score (>= 85.0) requires mandatory 4-Eyes Investigator authorization."
        else:
            checkpoint_reason = "HIGH Risk Score (>= 65.0) flagged for Senior Investigator disposition."

    assessment = {
        "composite_risk_score": risk_score,
        "operational_risk_level": risk_level,
        "requires_human_review": requires_human_review,
        "checkpoint_reason": checkpoint_reason,
        "decision_support_statement": "AI decision support score. Must not be used as standalone proof of crime."
    }

    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))
    timeline.append(AgentTimelineStep(
        agent="Risk Assessment Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=f"Score: {risk_score}/100 ({risk_level}) | Human Review Required: {requires_human_review}",
        timestamp=datetime.utcnow().isoformat()
    ))

    return {
        **state,
        "risk_assessment": assessment,
        "requires_human_review": requires_human_review,
        "review_checkpoint_reason": checkpoint_reason,
        "timeline": timeline
    }
