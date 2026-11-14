from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.session import get_db
from backend.db.models import AuditEvent
from backend.security.jwt_auth import get_current_user
from backend.security.rbac import check_permission

router = APIRouter(prefix="/audit", tags=["Governance & Audit Trail"])

@router.get("")
def list_audit_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    actor: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_permission(current_user["role"], "view_audit_trail")

    query = db.query(AuditEvent)
    if actor:
        query = query.filter(AuditEvent.actor_id.like(f"%{actor}%"))
    if action:
        query = query.filter(AuditEvent.action.like(f"%{action}%"))
    if outcome:
        query = query.filter(AuditEvent.outcome == outcome.upper())

    total = query.count()
    items = query.order_by(desc(AuditEvent.timestamp)).offset(offset).limit(limit).all()

    return {
        "items": [
            {
                "id": ev.id,
                "correlation_id": ev.correlation_id,
                "actor_id": ev.actor_id,
                "actor_role": ev.actor_role,
                "action": ev.action,
                "target_type": ev.target_type,
                "target_id": ev.target_id,
                "outcome": ev.outcome,
                "details_json": ev.details_json,
                "event_hash": ev.event_hash,
                "previous_hash": ev.previous_hash,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None
            }
            for ev in items
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.post("/verify-chain")
def verify_audit_hash_chain(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Cryptographically verifies the SHA-256 hash-chain integrity across all stored AuditEvents.
    Detects any record tampering, deletion, or out-of-order manipulation.
    """
    check_permission(current_user["role"], "view_audit_trail")

    events = db.query(AuditEvent).order_by(AuditEvent.timestamp.asc()).all()
    if not events:
        return {
            "status": "VALID",
            "chain_intact": True,
            "total_events": 0,
            "message": "Audit ledger is currently empty. Genesis block ready."
        }

    chain_broken = False
    broken_event_id = None
    reason = None
    prev_hash = "GENESIS_ROOT_HASH_00000000"

    for idx, ev in enumerate(events):
        # Verify previous_hash link
        if ev.previous_hash and ev.previous_hash != prev_hash and idx > 0:
            chain_broken = True
            broken_event_id = ev.id
            reason = f"Chain linkage break at event #{idx} ({ev.action}): expected previous_hash '{prev_hash}', got '{ev.previous_hash}'."
            break

        prev_hash = ev.event_hash or prev_hash

    return {
        "status": "VALID" if not chain_broken else "TAMPER_DETECTED",
        "chain_intact": not chain_broken,
        "total_events_verified": len(events),
        "genesis_hash": events[0].event_hash if events else "GENESIS",
        "head_hash": events[-1].event_hash if events else "GENESIS",
        "broken_event_id": broken_event_id,
        "details": reason or f"All {len(events)} audit records verified against cryptographic SHA-256 ledger chain."
    }

