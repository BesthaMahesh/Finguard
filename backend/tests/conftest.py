import pytest
import os
import sys
import json
import logging

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.db.session import engine, SessionLocal, Base
from backend.db.init_users import init_default_accounts
from backend.db.models import User, Transaction, InvestigationCase, AuditEvent, ModelMetadata
from backend.core.config import settings

logger = logging.getLogger("pytest_conftest")

@pytest.fixture(scope="session", autouse=True)
def initialize_test_suite():
    """
    Session-level autouse fixture ensuring a complete, valid test environment:
    1. Creates all database tables on the configured engine.
    2. Provisions default user accounts (user, admin, analyst, investigator, auditor).
    3. Provisions baseline transactions and investigation cases if database is fresh.
    4. Registers model governance metadata.
    5. Ingests knowledge base markdown policies into ChromaDB if not already indexed.
    """
    # 1. Create tables
    Base.metadata.create_all(bind=engine)

    # 2. Seed default users
    init_default_accounts()

    db = SessionLocal()
    try:
        # 3. Seed baseline transactions if empty
        tx_count = db.query(Transaction).count()
        if tx_count == 0:
            for i in range(1, 26):
                is_fraud = 1 if i in (5, 10, 199) else 0
                risk_score = 95.0 if is_fraud else 12.0
                tx = Transaction(
                    id=i,
                    step=1,
                    type="TRANSFER" if i % 2 == 0 else "PAYMENT",
                    amount=150.0 * i,
                    name_orig=f"C{100000+i}",
                    old_balance_org=2000.0 * i,
                    new_balance_orig=2000.0 * i - (150.0 * i if i % 2 != 0 else 0),
                    name_dest=f"M{200000+i}" if i % 2 != 0 else f"C{200000+i}",
                    old_balance_dest=0.0,
                    new_balance_dest=0.0 if i % 2 != 0 else 150.0 * i,
                    is_fraud=is_fraud,
                    risk_score=risk_score,
                    risk_level="CRITICAL" if is_fraud else "LOW",
                    status="UNDER_INVESTIGATION" if is_fraud else "CLEARED",
                    source="seed",
                    is_test=False
                )
                db.add(tx)
            db.commit()

        # 4. Seed baseline investigation cases if empty
        case_count = db.query(InvestigationCase).count()
        if case_count == 0:
            for i in range(1, 26):
                is_crit = i in (5, 10)
                status = "CLOSED_RESOLVED" if i > 23 else "OPEN"
                c = InvestigationCase(
                    id=f"CASE-FG-{i:06d}",
                    case_number=f"CASE-FG-{i:06d}",
                    transaction_id=i,
                    title=f"Review: Transaction #{i}",
                    status=status,
                    priority="HIGH" if is_crit else "LOW",
                    assigned_to="Financial Crime Unit (AI Triage)",
                    risk_score=95.0 if is_crit else 12.0,
                    summary=f"Automated risk alert: Transaction #{i} scored risk {95.0 if is_crit else 12.0}/100.",
                    submitted_by="system",
                    is_test=False,
                    source="seed"
                )
                db.add(c)
            db.commit()

        # 4b. Ensure CASE-FG-000199 exists for RBAC matrix validation
        c199 = db.query(InvestigationCase).filter_by(case_number="CASE-FG-000199").first()
        if not c199:
            tx199 = db.query(Transaction).filter_by(id=199).first()
            if not tx199:
                tx199 = Transaction(
                    id=199,
                    step=1,
                    type="TRANSFER",
                    amount=500000.0,
                    name_orig="C19900001",
                    old_balance_org=500000.0,
                    new_balance_orig=0.0,
                    name_dest="C19900002",
                    old_balance_dest=0.0,
                    new_balance_dest=500000.0,
                    is_fraud=1,
                    risk_score=98.0,
                    risk_level="CRITICAL",
                    status="UNDER_INVESTIGATION",
                    source="seed",
                    is_test=False
                )
                db.add(tx199)
                db.commit()
            c199 = InvestigationCase(
                id="CASE-FG-000199",
                case_number="CASE-FG-000199",
                transaction_id=199,
                title="Review: Transaction #199",
                status="OPEN",
                priority="CRITICAL",
                assigned_to="Financial Crime Unit (AI Triage)",
                risk_score=98.0,
                summary="Critical fraud alert for test case #199",
                submitted_by="system",
                is_test=False,
                source="seed"
            )
            db.add(c199)
            db.commit()

        # 5. Register model governance metadata
        meta_count = db.query(ModelMetadata).count()
        if meta_count == 0:
            metrics_file = os.path.join(settings.MODEL_ARTIFACTS_DIR, "metrics.json")
            if os.path.exists(metrics_file):
                with open(metrics_file, "r") as f:
                    metrics_data = json.load(f)
            else:
                metrics_data = {
                    "model_version": "v1.2.0-rf-enterprise",
                    "algorithm": "RandomForestClassifier",
                    "pr_auc": 0.9449,
                    "roc_auc": 0.9844,
                    "f1_score": 0.9412,
                    "precision": 1.0,
                    "recall": 0.8889,
                    "threshold": 0.65,
                    "confusion_matrix": [[100, 0], [0, 100]],
                    "feature_importance": {"amount": 0.5}
                }
            meta = ModelMetadata(
                model_version=metrics_data.get("model_version", "v1.2.0-rf-enterprise"),
                algorithm=metrics_data.get("algorithm", "RandomForestClassifier"),
                pr_auc=metrics_data.get("pr_auc", 0.9449),
                roc_auc=metrics_data.get("roc_auc", 0.9844),
                f1_score=metrics_data.get("f1_score", 0.9412),
                precision=metrics_data.get("precision", 1.0),
                recall=metrics_data.get("recall", 0.8889),
                threshold=metrics_data.get("threshold", 0.65),
                confusion_matrix_json=json.dumps(metrics_data.get("confusion_matrix", {})),
                feature_importance_json=json.dumps(metrics_data.get("feature_importance", {})),
                is_active=True
            )
            db.add(meta)
            db.commit()

        # 6. Ensure initial genesis audit event exists
        audit_count = db.query(AuditEvent).count()
        if audit_count == 0:
            ev = AuditEvent(
                correlation_id="CORR-GENESIS-000000",
                actor_id="system",
                actor_role="system",
                action="SYSTEM_INIT",
                target_type="PLATFORM",
                target_id="genesis",
                outcome="SUCCESS",
                previous_hash="GENESIS_ROOT_HASH_00000000",
                event_hash="41361f4d2e5bd47a029468c84709aba28521b3d40664037766e2dc015f01e670"
            )
            db.add(ev)
            db.commit()

    finally:
        db.close()

    # 7. Ensure ChromaDB has knowledge indexed
    try:
        from backend.rag.manifest import ManifestManager
        mgr = ManifestManager()
        stats = mgr.get_summary_statistics()
        if stats.get("total_indexed", 0) < 5:
            from backend.rag.ingestion_pipeline import KnowledgeIngestionPipeline
            pipeline = KnowledgeIngestionPipeline(target_dirs=["./knowledge_base", "./backend/rag/knowledge_base"])
            pipeline.run_incremental_ingestion()
    except Exception as e:
        logger.warning(f"ChromaDB knowledge pre-indexing notice: {e}")
