import time
from datetime import datetime
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.ml.leakage_guard import LeakageGuard

def data_quality_agent(state: InvestigationState) -> InvestigationState:
    """
    Checks completeness, numerical bounds, balance sanity, and ensures no target leakage.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    issues = []

    # 1. Check required numerical fields
    amount = tx.get("amount", 0.0)
    if amount <= 0:
        issues.append("Non-positive transaction amount")

    old_orig = tx.get("oldbalanceOrg", 0.0)
    new_orig = tx.get("newbalanceOrig", 0.0)
    if old_orig < 0 or new_orig < 0:
        issues.append("Negative origin balance detected")

    # 2. Check leakage guard
    is_clean, violations = LeakageGuard.audit_features(list(tx.keys()))
    if not is_clean:
        issues.extend(violations)

    quality_status = "PASSED" if not issues else "FLAGS_DETECTED"
    duration = (time.time() - start_time) * 1000.0

    timeline = list(state.get("timeline", []))
    timeline.append(AgentTimelineStep(
        agent="Data Quality Agent",
        status=quality_status,
        duration_ms=round(duration, 2),
        output_summary=f"Quality check {quality_status}: {len(issues)} flags. Leakage audit verified.",
        timestamp=datetime.utcnow().isoformat()
    ))

    return {
        **state,
        "data_quality_report": {
            "status": quality_status,
            "issues": issues,
            "leakage_audit": "PASSED" if is_clean else "VIOLATIONS",
            "checked_at": datetime.utcnow().isoformat()
        },
        "timeline": timeline
    }
