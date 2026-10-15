import time
from datetime import datetime
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.db.session import SessionLocal
from backend.db.models import Transaction

def transaction_intake_agent(state: InvestigationState) -> InvestigationState:
    """
    Validates transaction inputs and retrieves existing records if transaction_id is provided.
    """
    start_time = time.time()
    tx_id = state.get("transaction_id")
    raw_data = state.get("raw_transaction_data", {})
    validated = {}

    if tx_id:
        db = SessionLocal()
        try:
            tx = db.query(Transaction).filter_by(id=tx_id).first()
            if tx:
                validated = {
                    "id": tx.id,
                    "step": tx.step,
                    "type": tx.type,
                    "amount": tx.amount,
                    "nameOrig": tx.name_orig,
                    "oldbalanceOrg": tx.old_balance_org,
                    "newbalanceOrig": tx.new_balance_orig,
                    "nameDest": tx.name_dest,
                    "oldbalanceDest": tx.old_balance_dest,
                    "newbalanceDest": tx.new_balance_dest,
                    "historical_fraud_label": tx.is_fraud
                }
        finally:
            db.close()

    if not validated:
        # Construct from raw_transaction_data
        validated = {
            "id": raw_data.get("id"),
            "step": int(raw_data.get("step", 1)),
            "type": str(raw_data.get("type", "TRANSFER")).upper(),
            "amount": float(raw_data.get("amount", 0.0)),
            "nameOrig": str(raw_data.get("nameOrig", raw_data.get("name_orig", "C_UNKNOWN"))),
            "oldbalanceOrg": float(raw_data.get("oldbalanceOrg", raw_data.get("old_balance_org", 0.0))),
            "newbalanceOrig": float(raw_data.get("newbalanceOrig", raw_data.get("new_balance_orig", 0.0))),
            "nameDest": str(raw_data.get("nameDest", raw_data.get("name_dest", "C_UNKNOWN"))),
            "oldbalanceDest": float(raw_data.get("oldbalanceDest", raw_data.get("old_balance_dest", 0.0))),
            "newbalanceDest": float(raw_data.get("newbalanceDest", raw_data.get("new_balance_dest", 0.0))),
            "historical_fraud_label": raw_data.get("is_fraud", 0)
        }

    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))
    timeline.append(AgentTimelineStep(
        agent="Transaction Intake Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=f"Ingested transaction {validated.get('type')} of ${validated.get('amount', 0):,.2f}",
        timestamp=datetime.utcnow().isoformat()
    ))

    return {
        **state,
        "intake_status": "VALIDATED",
        "validated_transaction": validated,
        "timeline": timeline
    }
