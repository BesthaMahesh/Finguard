import os
import sys
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.config import settings
from backend.db.session import engine, SessionLocal
from backend.db.models import Base, User, ModelMetadata
from backend.security.jwt_auth import DEMO_USERS
from backend.data.ingestion import DataIngestionPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("seed_database")

def main():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Seed users if not existing
        for username, uinfo in DEMO_USERS.items():
            existing = db.query(User).filter_by(username=username).first()
            if not existing:
                user = User(
                    id=uinfo["id"],
                    username=uinfo["username"],
                    email=uinfo["email"],
                    hashed_password=uinfo["password_hash"],
                    full_name=uinfo["full_name"],
                    role=uinfo["role"],
                    is_active=True
                )
                db.add(user)
        db.commit()
        logger.info("Users seeded successfully.")

        # Seed Model Metadata from trained metrics
        metrics_file = os.path.join(settings.MODEL_ARTIFACTS_DIR, "metrics.json")
        if os.path.exists(metrics_file):
            with open(metrics_file, "r") as f:
                metrics_data = json.load(f)

            existing_meta = db.query(ModelMetadata).filter_by(model_version=metrics_data["model_version"]).first()
            if not existing_meta:
                meta = ModelMetadata(
                    model_version=metrics_data["model_version"],
                    algorithm=metrics_data["algorithm"],
                    pr_auc=metrics_data["pr_auc"],
                    roc_auc=metrics_data["roc_auc"],
                    f1_score=metrics_data["f1_score"],
                    precision=metrics_data["precision"],
                    recall=metrics_data["recall"],
                    threshold=metrics_data["threshold"],
                    confusion_matrix_json=json.dumps(metrics_data["confusion_matrix"]),
                    feature_importance_json=json.dumps(metrics_data["feature_importance"]),
                    is_active=True
                )
                db.add(meta)
                db.commit()
                logger.info("Model governance metadata registered.")

        # Run Data Ingestion from PaySim
        csv_path = settings.DATASET_RAW_PATH
        if os.path.exists(csv_path):
            pipeline = DataIngestionPipeline(db)
            res = pipeline.ingest_from_csv(csv_path, max_records=12000)
            logger.info(f"PaySim data seeded: {res['ingested_count']} transactions, {res['cases_created']} cases created.")
        else:
            logger.warning(f"PaySim raw dataset not found at {csv_path}. Transactions table remains empty for manual ingestion.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
