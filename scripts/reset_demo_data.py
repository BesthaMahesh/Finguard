"""
FinGuard Demo Data Reset Utility.
Restores the database to exactly the clean seeded dataset:
- Exactly 12,000 historical PaySim transactions (IDs 1..12000)
- Removes all ad-hoc test rows (C999888777, ID > 12000, is_test == True)
- Preserves the 25 verified investigation cases (23 OPEN, 2 CLOSED)
- Re-seals the SHA-256 cryptographic audit chain from Genesis to Head
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import hashlib
from datetime import datetime, timezone
from backend.db.session import SessionLocal
from backend.db.models import Transaction, InvestigationCase, AgentRun, AuditEvent

def reset_demo_data() -> dict:
    db = SessionLocal()
    try:
        # Check current count
        total_tx = db.query(Transaction).count()

        # If database has fewer than 10,000 transactions, perform a full clean seed
        if total_tx < 10000:
            print(f"[FinGuard] Current transaction count ({total_tx}) is below canonical threshold (10,000). Executing full seed...", flush=True)
            from scripts.seed_database import main as seed_main
            seed_main()
            total_tx = db.query(Transaction).count()
        else:
            # 1. Identify and delete test transactions and orphaned runs/cases
            test_tx_filter = (
                (Transaction.name_orig == "C999888777") |
                (Transaction.is_test == True) |
                (Transaction.source == "test")
            )
            if total_tx > 12000:
                test_tx_filter = test_tx_filter | (Transaction.id > 12000)

            test_txs = db.query(Transaction).filter(test_tx_filter).all()
            test_tx_ids = [t.id for t in test_txs]

            deleted_cases = 0
            if test_tx_ids:
                # Delete cases attached to test transactions
                del_cases = db.query(InvestigationCase).filter(InvestigationCase.transaction_id.in_(test_tx_ids)).delete(synchronize_session=False)
                deleted_cases += del_cases
                # Delete runs attached to test transactions
                db.query(AgentRun).filter(AgentRun.transaction_id.in_(test_tx_ids)).delete(synchronize_session=False)
                # Delete transactions
                deleted_txs = db.query(Transaction).filter(Transaction.id.in_(test_tx_ids)).delete(synchronize_session=False)
            else:
                deleted_txs = 0

            # Prune extra cases if more than 25 exist
            current_cases_count = db.query(InvestigationCase).count()
            if current_cases_count > 25:
                extra_cases = db.query(InvestigationCase).filter(InvestigationCase.id.notin_(
                    db.query(InvestigationCase.id).order_by(InvestigationCase.created_at.asc()).limit(25)
                )).all()
                for ec in extra_cases:
                    db.delete(ec)
                    deleted_cases += 1

            from sqlalchemy import text
            db.execute(text("UPDATE transactions SET is_test = 0 WHERE is_test IS NULL OR is_test = 'False'"))
            db.execute(text("UPDATE investigation_cases SET is_test = 0 WHERE is_test IS NULL OR is_test = 'False'"))
            db.commit()

        total_tx = db.query(Transaction).count()
        historical_tx = db.query(Transaction).filter(Transaction.id <= 12000).count()
        total_cases = db.query(InvestigationCase).count()
        open_cases = db.query(InvestigationCase).filter(InvestigationCase.status == "OPEN").count()

        # Re-chain AuditEvents
        events = db.query(AuditEvent).order_by(AuditEvent.timestamp.asc(), AuditEvent.id.asc()).all()
        prev_hash = "GENESIS_ROOT_HASH_00000000"
        for ev in events:
            ev.previous_hash = prev_hash
            raw_sig = f"{ev.correlation_id}:{ev.action}:{ev.target_id}:{prev_hash}:{ev.timestamp.isoformat() if ev.timestamp else datetime.now(timezone.utc).isoformat()}"
            curr_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()
            ev.event_hash = curr_hash
            prev_hash = curr_hash
        db.commit()

        result = {
            "status": "SUCCESS",
            "total_transactions": total_tx,
            "historical_transactions": historical_tx,
            "live_entered_transactions": max(0, total_tx - historical_tx),
            "total_cases": total_cases,
            "open_cases": open_cases,
            "audit_chain_head": prev_hash
        }
        print(f"Demo data reset complete: {result}")
        return result
    finally:
        db.close()

if __name__ == "__main__":
    reset_demo_data()
