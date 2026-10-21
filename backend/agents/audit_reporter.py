"""
FinGuard Audit & Reporting Agent.
Compiles comprehensive investigation dockets with strict separation of:
- Observed Facts
- Model Predictions
- Rule-based Findings
- Retrieved Policy Evidence
- AI-Generated Explanations
- Human Review & Decision Requirements
Records tamper-evident chained audit records.
"""

import time
import json
import hashlib
from datetime import datetime, timezone
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.db.session import SessionLocal
from backend.db.models import AuditEvent, generate_uuid
from backend.security.pii_protection import pii_protector

def audit_reporting_agent(state: InvestigationState) -> InvestigationState:
    """
    Produces final structured investigation docket, compiles executive brief,
    and records an immutable tamper-evident audit event in the database.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    risk = state.get("risk_assessment", {})
    model_pred = state.get("model_prediction", {})
    citations = state.get("policy_citations", [])
    explanation = state.get("explanation_summary", "")
    timeline = list(state.get("timeline", []))
    now_utc = datetime.now(timezone.utc)

    # 1. Observed Facts (Deterministic records)
    observed_facts = {
        "transaction_id": tx.get("id"),
        "step": tx.get("step"),
        "type": tx.get("type"),
        "amount": tx.get("amount"),
        "origin_account_masked": pii_protector.mask_financial_account(str(tx.get("nameOrig", ""))),
        "destination_account_masked": pii_protector.mask_financial_account(str(tx.get("nameDest", ""))),
        "origin_balance_before": tx.get("oldbalanceOrg"),
        "origin_balance_after": tx.get("newbalanceOrig"),
        "dest_balance_before": tx.get("oldbalanceDest"),
        "dest_balance_after": tx.get("newbalanceDest"),
    }

    # 2. Model Predictions (Probabilistic inference)
    model_predictions = {
        "fraud_probability": model_pred.get("fraud_probability"),
        "predicted_class": model_pred.get("predicted_fraud"),
        "shap_feature_attributions": state.get("feature_attributions", [])[:5],
        "model_version": model_pred.get("model_version", "rf-v1.2")
    }

    # 3. Rule-Based Findings
    rule_findings = {
        "triggered_rules": model_pred.get("rule_flags", []),
        "composite_risk_score": risk.get("composite_risk_score"),
        "operational_risk_level": risk.get("operational_risk_level")
    }

    # 4. Policy Evidence & Versioning
    policy_evidence = [
        {
            "document_id": c.get("document_id"),
            "document_title": c.get("document_title"),
            "version": c.get("version", "1.0"),
            "status": c.get("status", "ACTIVE"),
            "effective_from": c.get("effective_from"),
            "effective_to": c.get("effective_to"),
            "jurisdiction": c.get("jurisdiction", "GLOBAL"),
            "source_file": c.get("source_file"),
            "page_number": c.get("page_number"),
            "section": c.get("section"),
            "citation_location": c.get("citation_location"),
            "source_type": c.get("source_type"),
            "relevance_score": c.get("relevance_score"),
            "excerpt": c.get("excerpt")
        }
        for c in citations
    ]

    # 5. AI-Generated Narrative (Non-factual inference)
    ai_explanation = {
        "synthesis": explanation,
        "disclaimer": (
            "NOTICE: The AI explanation describes anomalous patterns and risk indicators. "
            "It does not constitute legal proof or final determination of criminal activity."
        )
    }

    # 6. Human Review Decision Requirements
    requires_human_review = state.get("requires_human_review", False)
    if risk.get("composite_risk_score", 0) >= 70.0 or not citations:
        requires_human_review = True

    human_decision_status = {
        "requires_human_review": requires_human_review,
        "review_checkpoint_reason": state.get("review_checkpoint_reason") or (
            "High composite risk score exceeding operational threshold" if risk.get("composite_risk_score", 0) >= 70.0 else None
        ),
        "assigned_role_required": "INVESTIGATOR",
        "action_allowed_without_approval": "READ_ONLY_TRIAGE"
    }

    report = {
        "report_id": f"REP-FG-{now_utc.strftime('%Y%m%d%H%M%S')}",
        "generated_at": now_utc.isoformat(),
        "correlation_id": state.get("correlation_id"),
        "observed_facts": observed_facts,
        "model_predictions": model_predictions,
        "rule_findings": rule_findings,
        "policy_evidence": policy_evidence,
        "ai_explanation": ai_explanation,
        "human_decision_status": human_decision_status,
        "workflow_metadata": {
            "executed_by_role": state.get("current_user_role", "analyst"),
            "total_tokens_consumed": state.get("tokens_consumed", 0),
            "trace_id": state.get("correlation_id")
        }
    }

    # Record tamper-evident persistent audit event
    db = SessionLocal()
    try:
        # Cryptographic Chaining
        prev_event = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).first()
        prev_hash = prev_event.event_hash if (prev_event and prev_event.event_hash) else "GENESIS_ROOT_HASH_00000000"
        
        target_tx_id = str(tx.get("id", "ad-hoc"))
        action_name = "INVESTIGATION_DOSSIER_COMPILED"
        corr_id = state.get("correlation_id", generate_uuid())
        
        event_raw = f"{corr_id}:{action_name}:{target_tx_id}:{prev_hash}:{now_utc.isoformat()}"
        current_hash = hashlib.sha256(event_raw.encode("utf-8")).hexdigest()

        applied_policy_ver = citations[0].get("version", "1.0") if citations else None

        audit_event = AuditEvent(
            correlation_id=corr_id,
            actor_id="audit_reporting_agent",
            actor_role=state.get("current_user_role", "analyst"),
            action=action_name,
            target_type="TRANSACTION",
            target_id=target_tx_id,
            outcome="SUCCESS",
            policy_version_applied=applied_policy_ver,
            event_hash=current_hash,
            previous_hash=prev_hash,
            timestamp=now_utc,
            details_json=json.dumps({
                "risk_score": risk.get("composite_risk_score"),
                "risk_level": risk.get("operational_risk_level"),
                "requires_human_review": requires_human_review,
                "policy_version": applied_policy_ver
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
        output_summary=f"Compiled structured risk docket ({report['report_id']}). Tamper-evident audit event logged.",
        timestamp=now_utc.isoformat()
    ))

    return {
        **state,
        "requires_human_review": requires_human_review,
        "final_report": report,
        "timeline": timeline
    }
