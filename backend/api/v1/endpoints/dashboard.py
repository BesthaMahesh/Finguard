from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.db.session import get_db
from backend.db.models import Transaction, InvestigationCase, AuditEvent
from backend.security.jwt_auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Executive Risk Overview"])

@router.get("/summary")
def get_executive_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    total_txs = db.query(Transaction).count()
    flagged_review = db.query(Transaction).filter(Transaction.risk_score >= 65.0).count()
    historical_frauds = db.query(Transaction).filter(Transaction.is_fraud == 1).count()
    open_cases = db.query(InvestigationCase).filter(InvestigationCase.status == "OPEN").count()
    audit_events_count = db.query(AuditEvent).count()

    # Risk level distribution
    risk_dist = {
        "LOW": db.query(Transaction).filter(Transaction.risk_level == "LOW").count(),
        "MEDIUM": db.query(Transaction).filter(Transaction.risk_level == "MEDIUM").count(),
        "HIGH": db.query(Transaction).filter(Transaction.risk_level == "HIGH").count(),
        "CRITICAL": db.query(Transaction).filter(Transaction.risk_level == "CRITICAL").count(),
    }

    # Volume and fraud count by transaction type
    type_stats = []
    types_query = db.query(
        Transaction.type,
        func.count(Transaction.id),
        func.sum(Transaction.amount),
        func.sum(Transaction.is_fraud),
        func.avg(Transaction.risk_score)
    ).group_by(Transaction.type).all()

    for row in types_query:
        type_stats.append({
            "type": row[0],
            "count": int(row[1]),
            "total_volume": round(float(row[2] or 0), 2),
            "historical_fraud_count": int(row[3] or 0),
            "avg_risk_score": round(float(row[4] or 0), 1)
        })

    # Step volume timeline (sampled across step buckets)
    step_buckets = db.query(
        (Transaction.step % 24).label("hour"),
        func.count(Transaction.id).label("count"),
        func.sum(Transaction.is_fraud).label("frauds")
    ).group_by("hour").order_by("hour").all()

    temporal_timeline = [
        {"hour": int(r[0]), "transaction_volume": int(r[1]), "detected_anomalies": int(r[2] or 0)}
        for r in step_buckets
    ]

    return {
        "total_transactions_processed": total_txs,
        "transactions_flagged_for_review": flagged_review,
        "historical_dataset_fraud_count": historical_frauds,
        "historical_fraud_rate_pct": round((historical_frauds / max(1, total_txs)) * 100, 3),
        "open_investigation_cases": open_cases,
        "total_audit_events": audit_events_count,
        "risk_level_distribution": risk_dist,
        "transaction_type_breakdown": type_stats,
        "temporal_volume_timeline": temporal_timeline,
        "dataset_freshness": "PaySim Synthetic Multi-Agent Financial Log",
        "active_model_version": "v1.2.0-rf-enterprise"
    }
