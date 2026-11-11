from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class RiskAnalyzeRequest(BaseModel):
    transaction_id: Optional[int] = None
    step: Optional[int] = 1
    type: Optional[str] = Field("TRANSFER", description="Transaction type")
    amount: Optional[float] = Field(None, ge=0.0)
    name_orig: Optional[str] = Field(None, description="Origin account ID")
    old_balance_org: Optional[float] = Field(0.0, ge=0.0)
    new_balance_orig: Optional[float] = Field(0.0, ge=0.0)
    name_dest: Optional[str] = Field(None, description="Destination account ID")
    old_balance_dest: Optional[float] = Field(0.0, ge=0.0)
    new_balance_dest: Optional[float] = Field(0.0, ge=0.0)
    use_multi_agent: bool = Field(True, description="Run through full 9-agent LangGraph workflow")

class RiskAnalyzeResponse(BaseModel):
    transaction_id: Optional[int] = None
    fraud_probability: float
    predicted_fraud: int
    risk_score: float
    risk_level: str
    requires_human_review: bool
    review_checkpoint_reason: Optional[str] = None
    rule_flags: List[Dict[str, Any]]
    feature_contributions: List[Dict[str, Any]]
    explanation_summary: Optional[str] = None
    policy_citations: Optional[List[Dict[str, Any]]] = None
    workflow_timeline: Optional[List[Dict[str, Any]]] = None
    correlation_id: str
