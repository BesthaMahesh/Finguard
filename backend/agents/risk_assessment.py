import time
from datetime import datetime, timezone
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.core.decision_policy import evaluate_decision_policy

def risk_assessment_agent(state: InvestigationState) -> InvestigationState:
    """
    Synthesizes model predictions, rule violations, and data quality flags.
    Enforces statutory rule floors and determines human review requirements via Unified Decision Policy.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    prediction = state.get("model_prediction", {})
    dq_report = state.get("data_quality_report", {})

    raw_score = float(prediction.get("risk_score", 0.0))
    dq_flags = dq_report.get("flags", [])
    rule_flags_raw = prediction.get("rule_flags", [])
    rule_ids = [r.get("rule_id", "") if isinstance(r, dict) else str(r) for r in rule_flags_raw]

    # Enforce statutory rule floors for data quality and ledger variance
    floor = 0.0
    if any(f in ("LEDGER_VARIANCE_MAJOR", "IMPOSSIBLE_MERCHANT_BALANCE", "NEGATIVE_OR_NONFINITE_VALUES") for f in dq_flags + rule_ids):
        floor = 70.0
    elif any(f == "LEDGER_VARIANCE_MINOR" for f in dq_flags + rule_ids):
        floor = 40.0

    composite_score = round(min(100.0, max(raw_score, floor)), 1)

    # Evaluate unified decision policy
    policy_verdict = evaluate_decision_policy(
        risk_score=composite_score,
        rule_flags=rule_ids,
        data_quality_flags=dq_flags,
        transaction=tx
    )

    assessment = {
        "composite_risk_score": composite_score,
        "operational_risk_level": policy_verdict.risk_tier,
        "requires_human_review": policy_verdict.requires_human_review,
        "decision": policy_verdict.decision,
        "checkpoint_reason": policy_verdict.summary_reason if policy_verdict.requires_human_review else None,
        "decision_support_statement": "AI decision support score. Must not be used as standalone proof of crime."
    }

    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))
    timeline.append(AgentTimelineStep(
        agent="Risk Assessment Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=f"Score: {composite_score}/100 ({policy_verdict.risk_tier}) | Decision: {policy_verdict.decision} | Human Review: {policy_verdict.requires_human_review}",
        timestamp=datetime.now(timezone.utc).isoformat()
    ))

    return {
        **state,
        "risk_assessment": assessment,
        "requires_human_review": policy_verdict.requires_human_review,
        "review_checkpoint_reason": policy_verdict.summary_reason if policy_verdict.requires_human_review else None,
        "timeline": timeline
    }
