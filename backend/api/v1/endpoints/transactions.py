from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.db.session import get_db
from backend.db.models import Transaction
from backend.schemas.transaction import TransactionResponse, TransactionListResponse
from backend.ml.model_service import model_service
from backend.security.jwt_auth import get_current_user
from backend.security.rbac import check_permission

router = APIRouter(prefix="/transactions", tags=["Transaction Intelligence"])

@router.get("", response_model=TransactionListResponse)
def list_transactions(
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_fraud: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("id", regex="^(id|amount|risk_score|step|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_permission(current_user["role"], "view_transactions")

    query = db.query(Transaction)
    if type:
        query = query.filter(Transaction.type == type.upper())
    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level.upper())
    if status:
        query = query.filter(Transaction.status == status.upper())
    if is_fraud is not None:
        query = query.filter(Transaction.is_fraud == is_fraud)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.name_orig.like(search_fmt),
                Transaction.name_dest.like(search_fmt),
            )
        )

    total = query.count()

    order_col = getattr(Transaction, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(asc(order_col))

    items = query.offset(offset).limit(limit).all()

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset
    )

@router.get("/{transaction_id}")
def get_transaction_detail(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_permission(current_user["role"], "view_transactions")
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found.")

    tx_dict = {
        "id": tx.id,
        "step": tx.step,
        "type": tx.type,
        "amount": float(tx.amount or 0.0),
        "name_orig": tx.name_orig,
        "old_balance_org": float(tx.old_balance_org or 0.0),
        "new_balance_orig": float(tx.new_balance_orig or 0.0),
        "name_dest": tx.name_dest,
        "old_balance_dest": float(tx.old_balance_dest or 0.0),
        "new_balance_dest": float(tx.new_balance_dest or 0.0),
        "is_fraud": tx.is_fraud,
        "is_flagged_fraud": tx.is_flagged_fraud,
        "predicted_fraud": tx.predicted_fraud,
        "fraud_probability": float(tx.fraud_probability) if tx.fraud_probability is not None else None,
        "risk_score": float(tx.risk_score) if tx.risk_score is not None else None,
        "risk_level": tx.risk_level or "LOW",
        "status": tx.status or "UNREVIEWED",
        "created_at": tx.created_at.isoformat() if tx.created_at else None
    }

    # Evaluate dynamic SHAP features and explainability
    try:
        analysis = model_service.predict_transaction(tx_dict)
        raw_rules = analysis.get("rule_flags", [])
        if not raw_rules and tx.rule_flags:
            import json
            try:
                db_rules = json.loads(tx.rule_flags) if isinstance(tx.rule_flags, str) else tx.rule_flags
                if isinstance(db_rules, list):
                    raw_rules = [{"name": str(r).replace("_", " "), "rule_id": str(r), "penalty": 15, "description": "Triggered rule pattern"} for r in db_rules]
            except Exception:
                pass
        tx_dict["rule_flags"] = raw_rules
        tx_dict["feature_contributions"] = analysis.get("feature_contributions", [])
        if tx_dict["fraud_probability"] is None:
            tx_dict["fraud_probability"] = analysis.get("fraud_probability", 0.0)
        if tx_dict["risk_score"] is None:
            tx_dict["risk_score"] = analysis.get("risk_score", 0.0)
    except Exception as e:
        tx_dict["rule_flags"] = []
        tx_dict["feature_contributions"] = []

    # Associated investigation case, if one exists
    from backend.db.models import InvestigationCase, AuditEvent
    case = db.query(InvestigationCase).filter(InvestigationCase.transaction_id == tx.id).first()
    tx_dict["investigation"] = {
        "id": case.id,
        "case_number": case.case_number,
        "title": case.title,
        "status": case.status,
        "priority": case.priority,
        "assigned_to": case.assigned_to,
        "disposition": case.disposition,
        "disposition_notes": case.disposition_notes,
        "reviewed_by": case.reviewed_by,
        "created_at": case.created_at.isoformat() if case.created_at else None
    } if case else None

    # Relevant audit trail entries
    audits = db.query(AuditEvent).filter(
        (AuditEvent.target_id == str(tx.id)) |
        (AuditEvent.target_id == (case.case_number if case else "")) |
        (AuditEvent.target_id == (case.id if case else ""))
    ).order_by(desc(AuditEvent.timestamp)).limit(5).all()

    tx_dict["audit_history"] = [
        {
            "id": a.id,
            "action": a.action,
            "actor_id": a.actor_id,
            "actor_role": a.actor_role,
            "outcome": a.outcome,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None
        }
        for a in audits
    ]

    return tx_dict

