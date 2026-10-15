from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class InvestigationCreate(BaseModel):
    transaction_id: Optional[int] = None
    raw_transaction_data: Optional[Dict[str, Any]] = None
    user_query: Optional[str] = None
    priority: str = Field("HIGH", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")

class InvestigationReviewRequest(BaseModel):
    disposition: str = Field(
        ...,
        pattern="^(ESCALATE_TO_SAR|FREEZE_ACCOUNT|CONFIRMED_FRAUD_FREEZE|REQUEST_ADDITIONAL_KYC|REQUEST_ADDITIONAL_EVIDENCE|DISMISS_FALSE_POSITIVE|APPROVE_FALSE_POSITIVE)$"
    )
    disposition_notes: str = Field(..., min_length=5)

    @field_validator("disposition", mode="before")
    @classmethod
    def normalize_disposition(cls, v: str) -> str:
        if not isinstance(v, str):
            return v
        mapping = {
            "CONFIRMED_FRAUD_FREEZE": "FREEZE_ACCOUNT",
            "APPROVE_FALSE_POSITIVE": "DISMISS_FALSE_POSITIVE",
            "REQUEST_ADDITIONAL_EVIDENCE": "REQUEST_ADDITIONAL_KYC",
        }
        return mapping.get(v.strip(), v.strip())

class InvestigationCaseResponse(BaseModel):
    id: str
    case_number: str
    transaction_id: int
    title: str
    status: str
    priority: str
    assigned_to: str
    risk_score: float
    summary: str
    model_features_json: Optional[str] = None
    policy_citations_json: Optional[str] = None
    agent_workflow_trace_json: Optional[str] = None
    disposition: Optional[str] = None
    disposition_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InvestigationListResponse(BaseModel):
    items: List[InvestigationCaseResponse]
    total: int
