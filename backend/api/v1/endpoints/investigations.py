from typing import Optional
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.session import get_db
from backend.db.models import InvestigationCase, Transaction, AuditEvent, generate_uuid
from backend.schemas.investigation import (
    InvestigationCaseResponse,
    InvestigationListResponse,
    InvestigationCreate,
    InvestigationReviewRequest
)
from backend.graphs.investigation_graph import execute_investigation
from backend.security.jwt_auth import get_current_user
from backend.security.rbac import check_permission

router = APIRouter(prefix="/investigations", tags=["Investigation Workbench & Cases"])

@router.get("", response_model=InvestigationListResponse)
def list_investigations(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(InvestigationCase)
    if status:
        query = query.filter(InvestigationCase.status == status.upper())
    if priority:
        query = query.filter(InvestigationCase.priority == priority.upper())

    total = query.count()
    items = query.order_by(desc(InvestigationCase.created_at)).offset(offset).limit(limit).all()

    return InvestigationListResponse(
        items=[InvestigationCaseResponse.model_validate(c) for c in items],
        total=total
    )

@router.get("/{investigation_id}", response_model=InvestigationCaseResponse)
def get_investigation_case(
    investigation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    case = db.query(InvestigationCase).filter(
        (InvestigationCase.id == investigation_id) | (InvestigationCase.case_number == investigation_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Investigation case not found")
    return InvestigationCaseResponse.model_validate(case)

@router.post("", response_model=InvestigationCaseResponse)
def create_investigation_case(
    req: InvestigationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_permission(current_user["role"], "create_case")

    # If transaction_id is provided, find it
    tx = None
    if req.transaction_id:
        tx = db.query(Transaction).filter_by(id=req.transaction_id).first()

    # Execute multi-agent investigation workflow
    agent_result = execute_investigation(
        transaction_id=req.transaction_id,
        raw_transaction_data=req.raw_transaction_data,
        user_query=req.user_query,
        user_role=current_user["role"]
    )

    risk_assess = agent_result.get("risk_assessment", {})
    score = risk_assess.get("composite_risk_score", 50.0)
    tx_id_val = tx.id if tx else (req.transaction_id or 1)

    case_num = f"CASE-FG-{datetime.utcnow().strftime('%y%m%d')}-{tx_id_val:04d}"
    title = f"Risk Investigation: {agent_result.get('validated_transaction', {}).get('type', 'TRANSFER')} (${agent_result.get('validated_transaction', {}).get('amount', 0):,.2f})"

    new_case = InvestigationCase(
        case_number=case_num,
        transaction_id=tx_id_val,
        title=title,
        status="OPEN",
        priority=risk_assess.get("operational_risk_level", "HIGH"),
        assigned_to=current_user["username"],
        risk_score=score,
        summary=agent_result.get("explanation_summary") or "Investigation case initiated.",
        model_features_json=json.dumps(agent_result.get("feature_attributions", [])),
        policy_citations_json=json.dumps(agent_result.get("policy_citations", [])),
        agent_workflow_trace_json=json.dumps(agent_result.get("timeline", []))
    )

    db.add(new_case)
    if tx:
        tx.status = "UNDER_INVESTIGATION"
    db.commit()
    db.refresh(new_case)

    return InvestigationCaseResponse.model_validate(new_case)

@router.post("/{investigation_id}/review", response_model=InvestigationCaseResponse)
def submit_investigation_review(
    investigation_id: str,
    req: InvestigationReviewRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_permission(current_user["role"], "update_disposition")

    case = db.query(InvestigationCase).filter(
        (InvestigationCase.id == investigation_id) | (InvestigationCase.case_number == investigation_id)
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Investigation case '{investigation_id}' not found.")

    # Idempotent re-submission check: if identical disposition was already recorded, return safely
    if case.disposition == req.disposition and case.disposition_notes == req.disposition_notes:
        return InvestigationCaseResponse.model_validate(case)

    case.disposition = req.disposition
    case.disposition_notes = req.disposition_notes
    case.reviewed_by = current_user["username"]
    case.reviewed_at = datetime.utcnow()
    case.status = "CLOSED_RESOLVED" if req.disposition != "DISMISS_FALSE_POSITIVE" else "CLOSED_FALSE_POSITIVE"

    if case.transaction:
        if req.disposition == "DISMISS_FALSE_POSITIVE":
            case.transaction.status = "CLEARED"
        elif req.disposition in ("ESCALATE_TO_SAR", "FREEZE_ACCOUNT"):
            case.transaction.status = "CONFIRMED_FRAUD"
        elif req.disposition == "REQUEST_ADDITIONAL_KYC":
            case.transaction.status = "UNDER_INVESTIGATION"

    # Audit log entry for human-in-the-loop review
    audit = AuditEvent(
        correlation_id=generate_uuid(),
        actor_id=current_user["username"],
        actor_role=current_user["role"],
        action="INVESTIGATION_HUMAN_REVIEW_DISPOSITION",
        target_type="INVESTIGATION_CASE",
        target_id=case.case_number,
        outcome="SUCCESS",
        details_json=json.dumps({
            "disposition": req.disposition,
            "notes": req.disposition_notes,
            "case_id": case.id,
            "transaction_id": case.transaction_id,
            "reviewed_by": current_user["username"],
            "reviewed_at": datetime.utcnow().isoformat()
        })
    )
    db.add(audit)
    db.commit()
    db.refresh(case)

    return InvestigationCaseResponse.model_validate(case)
