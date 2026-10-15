from fastapi import APIRouter, Depends, HTTPException
from backend.schemas.risk import RiskAnalyzeRequest, RiskAnalyzeResponse
from backend.graphs.investigation_graph import execute_investigation
from backend.ml.model_service import model_service
from backend.security.jwt_auth import get_current_user
from backend.security.rbac import check_permission

router = APIRouter(prefix="/risk", tags=["Risk Intelligence & Scoring"])

@router.post("/analyze", response_model=RiskAnalyzeResponse)
def analyze_transaction_risk(
    request: RiskAnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    check_permission(current_user["role"], "run_risk_analysis")

    raw_tx = {
        "step": request.step or 1,
        "type": request.type,
        "amount": request.amount,
        "nameOrig": request.name_orig,
        "oldbalanceOrg": request.old_balance_org,
        "newbalanceOrig": request.new_balance_orig,
        "nameDest": request.name_dest,
        "oldbalanceDest": request.old_balance_dest,
        "newbalanceDest": request.new_balance_dest,
    }

    if request.use_multi_agent:
        # Full 9-Agent LangGraph workflow execution
        workflow_result = execute_investigation(
            transaction_id=request.transaction_id,
            raw_transaction_data=raw_tx,
            user_role=current_user["role"]
        )

        model_pred = workflow_result.get("model_prediction", {})
        risk_assess = workflow_result.get("risk_assessment", {})

        return RiskAnalyzeResponse(
            transaction_id=request.transaction_id,
            fraud_probability=model_pred.get("fraud_probability", 0.0),
            predicted_fraud=model_pred.get("predicted_fraud", 0),
            risk_score=risk_assess.get("composite_risk_score", 0.0),
            risk_level=risk_assess.get("operational_risk_level", "LOW"),
            requires_human_review=workflow_result.get("requires_human_review", False),
            review_checkpoint_reason=workflow_result.get("review_checkpoint_reason"),
            rule_flags=model_pred.get("rule_flags", []),
            feature_contributions=workflow_result.get("feature_attributions", []),
            explanation_summary=workflow_result.get("explanation_summary"),
            policy_citations=workflow_result.get("policy_citations", []),
            workflow_timeline=workflow_result.get("timeline", []),
            correlation_id=workflow_result.get("correlation_id", "")
        )
    else:
        # Fast model + rule prediction
        analysis = model_service.predict_transaction(raw_tx)
        return RiskAnalyzeResponse(
            transaction_id=request.transaction_id,
            fraud_probability=analysis["fraud_probability"],
            predicted_fraud=analysis["predicted_fraud"],
            risk_score=analysis["risk_score"],
            risk_level=analysis["risk_level"],
            requires_human_review=analysis["requires_human_review"],
            review_checkpoint_reason=None,
            rule_flags=analysis["rule_flags"],
            feature_contributions=analysis["feature_contributions"],
            explanation_summary=None,
            policy_citations=[],
            workflow_timeline=[],
            correlation_id="fast-inference"
        )
