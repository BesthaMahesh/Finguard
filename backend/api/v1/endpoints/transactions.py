import io
import csv
import json
import time
import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.db.session import get_db, SessionLocal
from backend.db.models import Transaction, InvestigationCase, AuditEvent
from backend.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    ALLOWED_TRANSACTION_TYPES
)
from backend.ml.model_service import model_service
from backend.security.jwt_auth import get_current_user
from backend.security.rbac import check_permission
from backend.observability.tracer import tracer

router = APIRouter(prefix="/transactions", tags=["Transaction Intelligence"])

# In-memory sliding-window rate limiter: max 60 transactions per minute per user
_user_submission_timestamps: Dict[str, List[float]] = defaultdict(list)

def _enforce_rate_limit(username: str, max_requests: int = 60, window_seconds: float = 60.0):
    now = time.time()
    timestamps = _user_submission_timestamps[username]
    # Prune old timestamps
    _user_submission_timestamps[username] = [ts for ts in timestamps if now - ts < window_seconds]
    if len(_user_submission_timestamps[username]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: maximum {max_requests} transactions per minute per account."
        )
    _user_submission_timestamps[username].append(now)

@router.get("", response_model=TransactionListResponse)
def list_transactions(
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_fraud: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("id", pattern="^(id|amount|risk_score|step|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
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

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Submits and ingests a new transaction into the platform.
    Validates ledger integrity, evaluates ML fraud & risk scores,
    auto-generates an investigation case if risk is High/Critical,
    and logs an immutable SHA-256 chained AuditEvent.
    Ground-truth is explicitly set to None (unknown).
    """
    check_permission(current_user["role"], "view_transactions")
    _enforce_rate_limit(current_user.get("username", "anonymous"))

    # 1. Run Machine Learning & Heuristic Risk Inference
    tx_dict_for_eval = {
        "step": tx_in.step,
        "type": tx_in.type,
        "amount": tx_in.amount,
        "nameOrig": tx_in.name_orig,
        "oldbalanceOrg": tx_in.old_balance_org,
        "newbalanceOrig": tx_in.new_balance_orig,
        "nameDest": tx_in.name_dest,
        "oldbalanceDest": tx_in.old_balance_dest,
        "newbalanceDest": tx_in.new_balance_dest
    }

    try:
        analysis = model_service.predict_transaction(tx_dict_for_eval)
        fraud_prob = float(analysis.get("fraud_probability", 0.0))
        pred_fraud = int(analysis.get("predicted_fraud", 0))
        risk_score = float(analysis.get("risk_score", 0.0))
        risk_level = str(analysis.get("risk_level", "LOW"))
        rules_list = analysis.get("rule_flags", [])
        rule_flags_str = json.dumps([r.get("rule_id", r.get("name", "")) for r in rules_list])
    except Exception as e:
        fraud_prob = 0.0
        pred_fraud = 0
        risk_score = 10.0
        risk_level = "LOW"
        rule_flags_str = "[]"

    # 2. Persist new Transaction with ground_truth = None
    new_tx = Transaction(
        step=tx_in.step,
        type=tx_in.type,
        amount=tx_in.amount,
        name_orig=tx_in.name_orig,
        old_balance_org=tx_in.old_balance_org,
        new_balance_orig=tx_in.new_balance_orig,
        name_dest=tx_in.name_dest,
        old_balance_dest=tx_in.old_balance_dest,
        new_balance_dest=tx_in.new_balance_dest,
        is_fraud=None,  # Unknown ground truth for real incoming transactions
        is_flagged_fraud=pred_fraud,
        predicted_fraud=pred_fraud,
        fraud_probability=fraud_prob,
        risk_score=risk_score,
        risk_level=risk_level,
        status="UNDER_INVESTIGATION" if risk_score >= 65.0 else "UNREVIEWED",
        rule_flags=rule_flags_str
    )
    db.add(new_tx)
    db.flush()  # Populates new_tx.id

    # 3. If risk >= High (>= 65.0), automatically create an open investigation case
    created_case_id: Optional[str] = None
    if risk_score >= 65.0 or risk_level in ("HIGH", "CRITICAL"):
        case_num = f"CASE-FG-{new_tx.id:06d}"
        new_case = InvestigationCase(
            case_number=case_num,
            transaction_id=new_tx.id,
            title=f"Suspicious {new_tx.type} - ${new_tx.amount:,.2f} from {new_tx.name_orig}",
            status="OPEN",
            priority="CRITICAL" if risk_score >= 85.0 else "HIGH",
            assigned_to="Financial Crime Unit (AI Triage)",
            risk_score=risk_score,
            summary=(
                f"Autonomous risk alert: Transaction #{new_tx.id} ({new_tx.type} of ${new_tx.amount:,.2f}) "
                f"scored composite risk {risk_score:.1f}/100 ({risk_level}). Flagged for 4-Eyes Investigator review."
            ),
            model_features_json=json.dumps(analysis.get("feature_contributions", [])),
            policy_citations_json="[]",
            agent_workflow_trace_json="[]"
        )
        db.add(new_case)
        created_case_id = case_num

    # 4. Record AuditEvent with SHA-256 Hash Chain
    prev_ev = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).first()
    prev_hash = prev_ev.event_hash if (prev_ev and prev_ev.event_hash) else "GENESIS_ROOT_HASH_00000000"
    now_utc = datetime.now(timezone.utc)
    corr_id = f"TX-INGEST-{new_tx.id}"
    action_name = "TRANSACTION_CREATED"
    event_raw = f"{corr_id}:{action_name}:{new_tx.id}:{prev_hash}:{now_utc.isoformat()}"
    curr_hash = hashlib.sha256(event_raw.encode("utf-8")).hexdigest()

    audit_ev = AuditEvent(
        correlation_id=corr_id,
        actor_id=current_user.get("username", "system"),
        actor_role=current_user.get("role", "analyst"),
        action=action_name,
        target_type="TRANSACTION",
        target_id=str(new_tx.id),
        outcome="SUCCESS",
        policy_version_applied="1.0",
        event_hash=curr_hash,
        previous_hash=prev_hash,
        timestamp=now_utc,
        details_json=json.dumps({
            "transaction_id": new_tx.id,
            "type": new_tx.type,
            "amount": new_tx.amount,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "case_created": created_case_id
        })
    )
    db.add(audit_ev)
    db.commit()
    db.refresh(new_tx)

    resp = TransactionResponse.model_validate(new_tx)
    resp.case_id = created_case_id
    return resp

@router.post("/upload-csv")
async def upload_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Bulk transaction CSV upload (Administrator only).
    Parses, validates each row against ledger consistency checks,
    evaluates risk models, and commits in a transaction with error reporting.
    """
    norm_role = current_user.get("role", "").upper()
    if norm_role not in ("ADMIN", "ADMINISTRATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bulk CSV upload requires Administrator privileges."
        )

    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except Exception:
        decoded = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded))
    
    required_cols = {"type", "amount", "name_orig", "old_balance_org", "new_balance_orig", "name_dest"}
    if not reader.fieldnames or not required_cols.issubset({c.strip().lower() for c in reader.fieldnames}):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV missing mandatory headers. Required: {', '.join(sorted(required_cols))}"
        )

    inserted_count = 0
    errors = []
    created_tx_ids = []

    for row_idx, raw_row in enumerate(reader, start=1):
        # Normalize column keys
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}
        try:
            step = int(row.get("step") or 1)
            t_type = row.get("type", "").upper()
            amt = float(row.get("amount", 0))
            name_o = row.get("name_orig", "")
            old_o = float(row.get("old_balance_org") or row.get("oldbalanceorg") or 0)
            new_o = float(row.get("new_balance_orig") or row.get("newbalanceorig") or 0)
            name_d = row.get("name_dest", "")
            old_d = float(row.get("old_balance_dest") or row.get("oldbalancedest") or 0)
            new_d = float(row.get("new_balance_dest") or row.get("newbalancedest") or 0)

            # Validate using TransactionCreate schema
            tx_data = TransactionCreate(
                step=step,
                type=t_type,
                amount=amt,
                name_orig=name_o,
                old_balance_org=old_o,
                new_balance_orig=new_o,
                name_dest=name_d,
                old_balance_dest=old_d,
                new_balance_dest=new_d
            )

            # ML evaluation
            eval_dict = {
                "step": tx_data.step, "type": tx_data.type, "amount": tx_data.amount,
                "nameOrig": tx_data.name_orig, "oldbalanceOrg": tx_data.old_balance_org,
                "newbalanceOrig": tx_data.new_balance_orig, "nameDest": tx_data.name_dest,
                "oldbalanceDest": tx_data.old_balance_dest, "newbalanceDest": tx_data.new_balance_dest
            }
            analysis = model_service.predict_transaction(eval_dict)
            risk_score = float(analysis.get("risk_score", 0.0))
            risk_level = str(analysis.get("risk_level", "LOW"))
            fraud_prob = float(analysis.get("fraud_probability", 0.0))
            pred_fraud = int(analysis.get("predicted_fraud", 0))

            tx_entity = Transaction(
                step=tx_data.step,
                type=tx_data.type,
                amount=tx_data.amount,
                name_orig=tx_data.name_orig,
                old_balance_org=tx_data.old_balance_org,
                new_balance_orig=tx_data.new_balance_orig,
                name_dest=tx_data.name_dest,
                old_balance_dest=tx_data.old_balance_dest,
                new_balance_dest=tx_data.new_balance_dest,
                is_fraud=None,
                is_flagged_fraud=pred_fraud,
                predicted_fraud=pred_fraud,
                fraud_probability=fraud_prob,
                risk_score=risk_score,
                risk_level=risk_level,
                status="UNDER_INVESTIGATION" if risk_score >= 65.0 else "UNREVIEWED",
                rule_flags=json.dumps([r.get("rule_id", "") for r in analysis.get("rule_flags", [])])
            )
            db.add(tx_entity)
            db.flush()
            created_tx_ids.append(tx_entity.id)
            inserted_count += 1

            if risk_score >= 65.0:
                case_num = f"CASE-FG-{tx_entity.id:06d}"
                c = InvestigationCase(
                    case_number=case_num,
                    transaction_id=tx_entity.id,
                    title=f"Suspicious {tx_entity.type} - ${tx_entity.amount:,.2f} from {tx_entity.name_orig}",
                    status="OPEN",
                    priority="CRITICAL" if risk_score >= 85.0 else "HIGH",
                    assigned_to="Financial Crime Unit (AI Triage)",
                    risk_score=risk_score,
                    summary=f"Bulk Ingestion Risk Alert: Transaction #{tx_entity.id} scored risk {risk_score:.1f}/100.",
                    model_features_json=json.dumps(analysis.get("feature_contributions", [])),
                    policy_citations_json="[]",
                    agent_workflow_trace_json="[]"
                )
                db.add(c)

        except Exception as e:
            errors.append({"row": row_idx, "error": str(e)})

    # Commit audit log
    if inserted_count > 0:
        prev_ev = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).first()
        prev_hash = prev_ev.event_hash if (prev_ev and prev_ev.event_hash) else "GENESIS_ROOT_HASH_00000000"
        now_utc = datetime.now(timezone.utc)
        corr_id = f"BULK-CSV-{int(now_utc.timestamp())}"
        action_name = "TRANSACTIONS_BULK_CSV_UPLOAD"
        event_raw = f"{corr_id}:{action_name}:{inserted_count}:{prev_hash}:{now_utc.isoformat()}"
        curr_hash = hashlib.sha256(event_raw.encode("utf-8")).hexdigest()

        audit_ev = AuditEvent(
            correlation_id=corr_id,
            actor_id=current_user.get("username", "admin"),
            actor_role=current_user.get("role", "administrator"),
            action=action_name,
            target_type="BATCH_TRANSACTIONS",
            target_id=str(inserted_count),
            outcome="SUCCESS" if not errors else "PARTIAL_SUCCESS",
            policy_version_applied="1.0",
            event_hash=curr_hash,
            previous_hash=prev_hash,
            timestamp=now_utc,
            details_json=json.dumps({
                "inserted_count": inserted_count,
                "error_count": len(errors),
                "created_tx_ids": created_tx_ids[:20]
            })
        )
        db.add(audit_ev)
        db.commit()

    return {
        "status": "COMPLETED",
        "total_rows": row_idx if 'row_idx' in locals() else 0,
        "inserted_count": inserted_count,
        "error_count": len(errors),
        "errors": errors[:50]
    }

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

    try:
        analysis = model_service.predict_transaction(tx_dict)
        raw_rules = analysis.get("rule_flags", [])
        if not raw_rules and tx.rule_flags:
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
    except Exception:
        tx_dict["rule_flags"] = []
        tx_dict["feature_contributions"] = []

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
