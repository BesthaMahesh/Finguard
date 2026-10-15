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
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None
            }
            for ev in items
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }
