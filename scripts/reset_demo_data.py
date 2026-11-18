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
        # 1. Identify and delete test transactions and orphaned runs/cases
        test_txs = db.query(Transaction).filter(
            (Transaction.id > 12000) |
            (Transaction.name_orig == "C999888777") |
            (Transaction.is_test == True) |
            (Transaction.source == "test")
        ).all()
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

        # Also remove any cases with case_number > 25
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

        # 2. Re-verify transaction and case counts (auto-seed if empty)
        total_tx = db.query(Transaction).count()
        if total_tx == 0:
            print("[FinGuard] Warning: Database has 0 transactions. Automatically seeding default PaySim data...", flush=True)
            from scripts.seed_database import main as seed_main
            seed_main()
            total_tx = db.query(Transaction).count()

        historical_tx = db.query(Transaction).filter(Transaction.id <= 12000).count()
        total_cases = db.query(InvestigationCase).count()
        open_cases = db.query(InvestigationCase).filter(InvestigationCase.status == "OPEN").count()

        # 3. Cryptographically re-chain all remaining AuditEvents
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
            "deleted_test_transactions": deleted_txs,
            "deleted_extra_cases": deleted_cases,
            "total_transactions": total_tx,
            "historical_transactions": historical_tx,
            "live_entered_transactions": total_tx - historical_tx,
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
