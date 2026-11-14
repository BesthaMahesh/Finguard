import asyncio
import json
import logging
import time
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.db.session import SessionLocal
from backend.db.models import AgentRun, InvestigationCase, Transaction, AuditEvent
from backend.graphs.investigation_graph import (
    AGENT_REGISTRY,
    investigation_workflow,
    create_initial_investigation_state
)
from backend.security.jwt_auth import get_current_user
from backend.security.pii_protection import pii_protector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agent Workflow & Live Streaming"])

class StreamAnalyzeRequest(BaseModel):
    transaction_id: Optional[int] = None
    step: Optional[int] = 1
    type: Optional[str] = "TRANSFER"
    amount: Optional[float] = 0.0
    name_orig: Optional[str] = "C_CUSTOMER"
    old_balance_org: Optional[float] = 0.0
    new_balance_orig: Optional[float] = 0.0
    name_dest: Optional[str] = "M_MERCHANT"
    old_balance_dest: Optional[float] = 0.0
    new_balance_dest: Optional[float] = 0.0

def build_trimmed_summary(node_name: str, state_delta: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts high-signal, readable key facts from each agent node output."""
    summary: Dict[str, Any] = {}
    if node_name == "supervisor_plan":
        summary = {
            "status": "PLANNING_COMPLETED",
            "correlation_id": state_delta.get("correlation_id", "")[:8] + "...",
            "next_step": state_delta.get("workflow_next_step", "INTAKE")
        }
    elif node_name == "intake":
        tx = state_delta.get("validated_transaction", {})
        summary = {
            "status": state_delta.get("intake_status", "VALIDATED"),
            "type": tx.get("type"),
            "amount": tx.get("amount"),
            "origin": pii_protector.mask_financial_account(str(tx.get("nameOrig", ""))),
            "destination": pii_protector.mask_financial_account(str(tx.get("nameDest", "")))
        }
    elif node_name == "data_quality":
        dq = state_delta.get("data_quality_report", {})
        summary = {
            "is_valid": dq.get("is_valid", True),
            "checks_passed": dq.get("checks_passed", 0),
            "target_leakage_risk": dq.get("target_leakage_risk", "ZERO_DETECTED")
        }
    elif node_name == "fraud_detector":
        pred = state_delta.get("model_prediction", {})
        summary = {
            "fraud_probability": pred.get("fraud_probability", 0.0),
            "predicted_fraud": bool(pred.get("predicted_fraud", 0)),
            "rules_triggered": pred.get("rule_flags", []),
            "top_feature": (state_delta.get("feature_attributions", [{}])[0].get("display_name") if state_delta.get("feature_attributions") else "N/A")
        }
    elif node_name == "market_credit_risk":
        mcr = state_delta.get("market_credit_risk", {})
        summary = {
            "var_95_1day": mcr.get("var_95_1day", 0.0),
            "credit_risk_score": mcr.get("credit_risk_score", 0.0),
            "credit_risk_grade": mcr.get("credit_risk_grade", "AAA"),
            "exposure_ratio_pct": round(mcr.get("exposure_ratio", 0.0) * 100, 1)
        }
    elif node_name == "risk_assessment":
        risk = state_delta.get("risk_assessment", {})
        summary = {
            "composite_risk_score": risk.get("composite_risk_score", 0.0),
            "operational_risk_level": risk.get("operational_risk_level", "LOW"),
            "requires_human_review": risk.get("requires_human_review", False)
        }
    elif node_name == "investigator":
        ev = state_delta.get("investigation_evidence", {})
        summary = {
            "rapid_liquidation": ev.get("rapid_liquidation", False),
            "counterparty_anomalies": ev.get("counterparty_flags", 0),
            "forensic_flags": ev.get("evidence_tags", [])
        }
    elif node_name == "policy_compliance":
        citations = state_delta.get("policy_citations", [])
        summary = {
            "citations_found": len(citations),
            "primary_policy": citations[0].get("document_id") if citations else "None",
            "section": citations[0].get("section") if citations else "None"
        }
    elif node_name == "explainability":
        summary = {
            "narrative_preview": state_delta.get("explanation_summary", "")[:100] + "...",
            "tokens_consumed": state_delta.get("tokens_consumed", 0)
        }
    elif node_name == "audit_reporter":
        rep = state_delta.get("final_report", {})
        summary = {
            "status": "DOSSIER_SEALED",
            "audit_hash": rep.get("audit_hash", "GENESIS")[:12] + "...",
            "human_in_loop_mandate": state_delta.get("requires_human_review", False)
        }
    return pii_protector.sanitize_dictionary(summary)

def trim_output(node_name: str, state_delta: Dict[str, Any]) -> Dict[str, Any]:
    """Returns safe, trimmed output data without spilling enormous raw state."""
    keys_of_interest = {
        "supervisor_plan": ["workflow_next_step", "correlation_id"],
        "intake": ["validated_transaction", "intake_status"],
        "data_quality": ["data_quality_report"],
        "fraud_detector": ["model_prediction", "feature_attributions"],
        "market_credit_risk": ["market_credit_risk"],
        "risk_assessment": ["risk_assessment", "requires_human_review"],
        "investigator": ["investigation_evidence"],
        "policy_compliance": ["policy_citations"],
        "explainability": ["explanation_summary", "tokens_consumed"],
        "audit_reporter": ["final_report"]
    }
    allowed = keys_of_interest.get(node_name, [])
    extracted = {k: state_delta[k] for k in allowed if k in state_delta}
    return pii_protector.sanitize_dictionary(extracted)

@router.post("/analyze/stream")
async def analyze_stream(
    req: StreamAnalyzeRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Server-Sent Events streaming endpoint executing the 10-Agent LangGraph workflow.
    Emits real-time progression: run_start, agent_start, agent_token, agent_end, run_end.
    Persists events to agent_runs table and logs an immutable audit event.
    """
    # 1. Rehydrate transaction if ID is given
    raw_tx = {
        "step": req.step or 1,
        "type": req.type or "TRANSFER",
        "amount": req.amount if req.amount is not None else 0.0,
        "nameOrig": req.name_orig or "C_CUSTOMER",
        "oldbalanceOrg": req.old_balance_org if req.old_balance_org is not None else 0.0,
        "newbalanceOrig": req.new_balance_orig if req.new_balance_orig is not None else 0.0,
        "nameDest": req.name_dest or "M_MERCHANT",
        "oldbalanceDest": req.old_balance_dest if req.old_balance_dest is not None else 0.0,
        "newbalanceDest": req.new_balance_dest if req.new_balance_dest is not None else 0.0,
    }

    target_tx_id = req.transaction_id
    if target_tx_id:
        db = SessionLocal()
        try:
            tx = db.query(Transaction).filter_by(id=target_tx_id).first()
            if tx:
                raw_tx["id"] = tx.id
                raw_tx["step"] = tx.step
                raw_tx["type"] = tx.type
                raw_tx["amount"] = tx.amount
                raw_tx["nameOrig"] = tx.name_orig
                raw_tx["oldbalanceOrg"] = tx.old_balance_org
                raw_tx["newbalanceOrig"] = tx.new_balance_orig
                raw_tx["nameDest"] = tx.name_dest
                raw_tx["oldbalanceDest"] = tx.old_balance_dest
                raw_tx["newbalanceDest"] = tx.new_balance_dest
                raw_tx["is_fraud"] = tx.is_fraud
        finally:
            db.close()

    run_id = f"RUN-{uuid.uuid4().hex[:12].upper()}"
    user_name = current_user.get("username", "system_analyst")
    user_role = current_user.get("role", "analyst")

    initial_state = create_initial_investigation_state(
        transaction_id=target_tx_id,
        raw_transaction_data=raw_tx,
        user_role=user_role
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        start_overall = time.time()
        node_start_times: Dict[str, float] = {}
        executed_agents: set = set()
        accumulated_events: List[Dict[str, Any]] = []
        final_state: Dict[str, Any] = {}
        created_case_id: Optional[str] = None

        def format_sse(event_name: str, payload: Dict[str, Any]) -> str:
            accumulated_events.append({"event": event_name, "data": payload, "ts": datetime.now(timezone.utc).isoformat()})
            return f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"

        try:
            # 1. Emit run_start
            yield format_sse("run_start", {
                "run_id": run_id,
                "transaction_id": target_tx_id,
                "agents": AGENT_REGISTRY,
                "ts": datetime.now(timezone.utc).isoformat()
            })

            agent_ids = {a["id"] for a in AGENT_REGISTRY}
            agent_map = {a["id"]: a for a in AGENT_REGISTRY}

            # 2. Stream LangGraph v2 events
            async for ev in investigation_workflow.astream_events(initial_state, version="v2"):
                if await request.is_disconnected():
                    logger.warning(f"Client disconnected from stream for run_id={run_id}")
                    return

                event_type = ev.get("event")
                node_name = ev.get("name")

                # Agent Start
                if event_type == "on_chain_start" and node_name in agent_ids:
                    node_start_times[node_name] = time.time()
                    meta = agent_map[node_name]
                    yield format_sse("agent_start", {
                        "agent": node_name,
                        "label": meta["label"],
                        "role": meta["role"],
                        "ts": datetime.now(timezone.utc).isoformat()
                    })

                # Live LLM Tokens from Explainability Agent
                elif event_type == "on_custom_event" and ev.get("name") == "agent_token":
                    token_data = ev.get("data", {})
                    yield format_sse("agent_token", {
                        "agent": token_data.get("agent", "explainability"),
                        "text": token_data.get("text", "")
                    })

                # Agent End
                elif event_type == "on_chain_end" and node_name in agent_ids:
                    executed_agents.add(node_name)
                    st_time = node_start_times.get(node_name, time.time())
                    duration_ms = round((time.time() - st_time) * 1000.0, 2)
                    output_data = ev.get("data", {}).get("output", {})
                    if isinstance(output_data, dict):
                        final_state.update(output_data)

                    summary = build_trimmed_summary(node_name, output_data if isinstance(output_data, dict) else {})
                    trimmed = trim_output(node_name, output_data if isinstance(output_data, dict) else {})

                    yield format_sse("agent_end", {
                        "agent": node_name,
                        "status": "COMPLETED",
                        "duration_ms": duration_ms,
                        "summary": summary,
                        "output": trimmed
                    })

            # Check for skipped agents (Fast-Track skips investigator and policy_compliance)
            all_possible = ["supervisor_plan", "intake", "data_quality", "fraud_detector", "market_credit_risk", "risk_assessment", "investigator", "policy_compliance", "explainability", "audit_reporter"]
            for agent_id in all_possible:
                if agent_id not in executed_agents:
                    yield format_sse("agent_end", {
                        "agent": agent_id,
                        "status": "SKIPPED",
                        "duration_ms": 0.0,
                        "summary": {
                            "status": "SKIPPED",
                            "reason": "Fast-Track routing: Routine payment risk score (< 30) bypassed deep forensic investigation."
                        },
                        "output": {}
                    })

            # 3. Assemble verdict and auto-create case if High/Critical
            risk = final_state.get("risk_assessment", {})
            score = risk.get("composite_risk_score", 0.0)
            tier = risk.get("operational_risk_level", "LOW")
            narrative = final_state.get("explanation_summary", "No anomalies identified.")
            requires_human_review = final_state.get("requires_human_review", False)
            decision = "MANDATORY_REVIEW" if requires_human_review else "CLEARED_FAST_TRACK"

            # Auto-case creation for High or Critical transactions
            db = SessionLocal()
            try:
                if (score >= 65.0 or requires_human_review) and target_tx_id:
                    existing_case = db.query(InvestigationCase).filter_by(transaction_id=target_tx_id).first()
                    if existing_case:
                        created_case_id = existing_case.case_number
                    else:
                        case_num = f"CASE-FG-{target_tx_id:06d}"
                        new_case = InvestigationCase(
                            case_number=case_num,
                            transaction_id=target_tx_id,
                            title=f"Suspicious {raw_tx.get('type')} Transfer - ${raw_tx.get('amount', 0):,.2f}",
                            status="OPEN",
                            priority="CRITICAL" if score >= 85.0 else "HIGH",
                            assigned_to="Financial Crime Unit (AI Triage)",
                            risk_score=score,
                            summary=narrative,
                            model_features_json=json.dumps(final_state.get("feature_attributions", [])),
                            policy_citations_json=json.dumps(final_state.get("policy_citations", [])),
                            agent_workflow_trace_json=json.dumps(final_state.get("timeline", []))
                        )
                        db.add(new_case)
                        db.commit()
                        created_case_id = case_num
            except Exception as e:
                logger.error(f"Error checking/creating investigation case: {e}")
                db.rollback()
            finally:
                db.close()

            total_duration_ms = round((time.time() - start_overall) * 1000.0, 2)

            # 4. Emit run_end
            yield format_sse("run_end", {
                "result": {
                    "risk_score": score,
                    "risk_tier": tier,
                    "decision": decision,
                    "narrative": narrative,
                    "case_id": created_case_id
                },
                "duration_ms": total_duration_ms
            })

            # 5. Persist run to SQLite agent_runs table
            db = SessionLocal()
            try:
                agent_run = AgentRun(
                    run_id=run_id,
                    transaction_id=target_tx_id,
                    case_id=created_case_id,
                    user=user_name,
                    risk_score=score,
                    risk_tier=tier,
                    decision=decision,
                    narrative=narrative,
                    events_json=json.dumps(accumulated_events),
                    duration_ms=total_duration_ms
                )
                db.add(agent_run)

                # 6. Immutable Audit Event with Hash Chain
                prev_ev = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).first()
                prev_hash = prev_ev.event_hash if (prev_ev and prev_ev.event_hash) else "GENESIS_ROOT_HASH_00000000"
                now_utc = datetime.now(timezone.utc)
                action_name = "AGENT_WORKFLOW_STREAM_EXECUTED"
                event_raw = f"{run_id}:{action_name}:{target_tx_id or 'ad-hoc'}:{prev_hash}:{now_utc.isoformat()}"
                curr_hash = hashlib.sha256(event_raw.encode("utf-8")).hexdigest()

                audit_event = AuditEvent(
                    correlation_id=run_id,
                    actor_id=user_name,
                    actor_role=user_role,
                    action=action_name,
                    target_type="TRANSACTION" if target_tx_id else "AD_HOC_STREAM",
                    target_id=str(target_tx_id or run_id),
                    outcome="SUCCESS",
                    policy_version_applied="1.0",
                    event_hash=curr_hash,
                    previous_hash=prev_hash,
                    timestamp=now_utc,
                    details_json=json.dumps({
                        "run_id": run_id,
                        "risk_score": score,
                        "risk_tier": tier,
                        "decision": decision,
                        "duration_ms": total_duration_ms,
                        "case_id": created_case_id
                    })
                )
                db.add(audit_event)
                db.commit()
            except Exception as e:
                logger.error(f"Error persisting agent run / audit event: {e}")
                db.rollback()
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Streaming execution error for run_id={run_id}: {e}", exc_info=True)
            yield format_sse("run_error", {"error": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/runs/{run_id}")
def get_agent_run(run_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieves full recorded event trace for replay and historical audit."""
    db = SessionLocal()
    try:
        run = db.query(AgentRun).filter_by(run_id=run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail=f"Agent run '{run_id}' not found.")
        return {
            "run_id": run.run_id,
            "transaction_id": run.transaction_id,
            "case_id": run.case_id,
            "user": run.user,
            "risk_score": run.risk_score,
            "risk_tier": run.risk_tier,
            "decision": run.decision,
            "narrative": run.narrative,
            "duration_ms": run.duration_ms,
            "events": json.loads(run.events_json),
            "created_at": run.created_at.isoformat() if run.created_at else None
        }
    finally:
        db.close()

@router.get("/case-trace/{case_id}")
def get_case_agent_trace(case_id: str, current_user: dict = Depends(get_current_user)):
    """Fetches stored multi-agent trace events for a given investigation case number or UUID."""
    db = SessionLocal()
    try:
        # Check agent_runs first
        run = db.query(AgentRun).filter((AgentRun.case_id == case_id) | (AgentRun.case_id == f"CASE-FG-{case_id}")).order_by(AgentRun.created_at.desc()).first()
        if run and run.events_json:
            return {
                "source": "agent_runs",
                "run_id": run.run_id,
                "case_id": run.case_id,
                "events": json.loads(run.events_json)
            }

        # Fallback to case docket
        case = db.query(InvestigationCase).filter((InvestigationCase.case_number == case_id) | (InvestigationCase.id == case_id)).first()
        if not case:
            raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

        timeline = json.loads(case.agent_workflow_trace_json or "[]")
        return {
            "source": "case_docket",
            "run_id": f"RUN-HISTORIC-{case.case_number}",
            "case_id": case.case_number,
            "timeline": timeline,
            "summary": case.summary,
            "risk_score": case.risk_score
        }
    finally:
        db.close()
