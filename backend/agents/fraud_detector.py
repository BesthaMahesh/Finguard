import time
from datetime import datetime
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.ml.model_service import model_service

def fraud_detection_agent(state: InvestigationState) -> InvestigationState:
    """
    Executes trained Random Forest model inference and transparent deterministic rules.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    
    # Run prediction service
    prediction = model_service.predict_transaction(tx)
    duration = (time.time() - start_time) * 1000.0

    timeline = list(state.get("timeline", []))
    timeline.append(AgentTimelineStep(
        agent="Fraud Detection Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=f"ML Fraud Prob: {prediction['fraud_probability']:.4f} | Triggered Rules: {len(prediction['rule_flags'])}",
        timestamp=datetime.utcnow().isoformat()
    ))

    return {
        **state,
        "model_prediction": prediction,
        "feature_attributions": prediction.get("feature_contributions", []),
        "timeline": timeline
    }
