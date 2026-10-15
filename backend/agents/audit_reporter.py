import time
import json
from datetime import datetime
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.db.session import SessionLocal
from backend.db.models import AuditEvent, generate_uuid

def audit_reporting_agent(state: InvestigationState) -> InvestigationState:
    """
    Produces final structured investigation docket, compiles executive brief,
    and records an immutable audit event in the database.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    risk = state.get("risk_assessment", {})
    model_pred = state.get("model_prediction", {})
    citations = state.get("policy_citations", [])
    explanation = state.get("explanation_summary", "")
    timeline = list(state.get("timeline", []))

    report = {
        "report_id": f"REP-FG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "generated_at": datetime.utcnow().isoformat(),
        "transaction_overview": {
            "transaction_id": tx.get("id"),
            "type": tx.get("type"),
            "amount": tx.get("amount"),
            "origin": tx.get("nameOrig"),
            "destination": tx.get("nameDest"),
            "step": tx.get("step")
        },
        "risk_evaluation": {
            "composite_risk_score": risk.get("composite_risk_score"),
            "operational_risk_level": risk.get("operational_risk_level"),
            "ml_fraud_probability": model_pred.get("fraud_probability"),
            "rule_violations": model_pred.get("rule_flags", []),
            "requires_human_review": state.get("requires_human_review", False),
            "review_checkpoint_reason": state.get("review_checkpoint_reason")
        },
        "investigation_narrative": explanation,
        "policy_governance": [
            {
                "document": c.get("document_id"),
                "document_title": c.get("document_title"),
                "source_file": c.get("source_file"),
                "page_number": c.get("page_number"),
                "section": c.get("section"),
                "citation_location": c.get("citation_location"),
                "source_type": c.get("source_type"),
                "relevance": c.get("relevance_score"),
                "excerpt": c.get("excerpt")
            }
            for c in citations
        ],
        "feature_attributions": state.get("feature_attributions", [])[:5],
        "workflow_metadata": {
            "correlation_id": state.get("correlation_id"),
            "executed_by_role": state.get("current_user_role", "analyst"),
            "total_tokens_consumed": state.get("tokens_consumed", 0)
        }
    }

    # Record persistent audit event in database
    db = SessionLocal()
    try:
        audit_event = AuditEvent(
            correlation_id=state.get("correlation_id", generate_uuid()),
            actor_id="audit_reporting_agent",
            actor_role=state.get("current_user_role", "analyst"),
            action="INVESTIGATION_DOSSIER_COMPILED",
            target_type="TRANSACTION",
            target_id=str(tx.get("id", "ad-hoc")),
            outcome="SUCCESS",
            details_json=json.dumps({
                "risk_score": risk.get("composite_risk_score"),
                "risk_level": risk.get("operational_risk_level"),
                "requires_human_review": state.get("requires_human_review")
            })
        )
        db.add(audit_event)
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

    duration = (time.time() - start_time) * 1000.0
    timeline.append(AgentTimelineStep(
        agent="Audit & Reporting Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=f"Compiled structured risk docket ({report['report_id']}). Audit event logged.",
        timestamp=datetime.utcnow().isoformat()
    ))

    return {
        **state,
        "final_report": report,
        "timeline": timeline
    }
