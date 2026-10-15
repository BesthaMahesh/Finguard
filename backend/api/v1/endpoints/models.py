import os
import json
from fastapi import APIRouter, Depends, HTTPException
from backend.core.config import settings
from backend.governance.model_cards import ModelGovernance
from backend.security.jwt_auth import get_current_user

router = APIRouter(prefix="/models", tags=["Model Intelligence & Governance"])

@router.get("")
def get_model_registry(current_user: dict = Depends(get_current_user)):
    """Returns active models and model card."""
    model_card = ModelGovernance.get_model_card()
    metrics_path = os.path.join(settings.MODEL_ARTIFACTS_DIR, "metrics.json")
    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            metrics = json.load(f)

    return {
        "active_model": metrics.get("model_version", "v1.2.0-rf-enterprise"),
        "model_card": model_card,
        "metrics_summary": {
            "pr_auc": metrics.get("pr_auc"),
            "roc_auc": metrics.get("roc_auc"),
            "f1_score": metrics.get("f1_score"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "threshold": metrics.get("threshold", settings.FRAUD_THRESHOLD),
        }
    }

@router.get("/evaluation")
def get_model_evaluation(current_user: dict = Depends(get_current_user)):
    """Returns detailed evaluation report including confusion matrix, PR curve, and feature importances."""
    metrics_path = os.path.join(settings.MODEL_ARTIFACTS_DIR, "metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="Model evaluation metrics not found. Please train model.")

    with open(metrics_path, "r") as f:
        metrics = json.load(f)

    return metrics
