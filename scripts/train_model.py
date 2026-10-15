import os
import sys
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ml.pipeline import ModelPipeline
from backend.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("train_model")

def main():
    csv_path = settings.DATASET_RAW_PATH
    if not os.path.exists(csv_path):
        logger.error(f"PaySim dataset not found at {csv_path}. Please place the dataset in root directory.")
        sys.exit(1)

    logger.info(f"Initiating FinGuard model training on {csv_path}...")
    pipeline = ModelPipeline(model_dir=settings.MODEL_ARTIFACTS_DIR)
    metrics = pipeline.train_and_evaluate(csv_path=csv_path, sample_size=150000, threshold=settings.FRAUD_THRESHOLD)
    logger.info("Training and evaluation completed successfully!")
    logger.info(f"Model Metrics: PR-AUC={metrics['pr_auc']}, ROC-AUC={metrics['roc_auc']}, F1={metrics['f1_score']}")

if __name__ == "__main__":
    main()
