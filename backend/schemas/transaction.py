from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class TransactionBase(BaseModel):
    step: int = Field(..., ge=1)
    type: str = Field(..., description="PAYMENT, TRANSFER, CASH_OUT, DEBIT, CASH_IN")
    amount: float = Field(..., ge=0.0)
    name_orig: str
    old_balance_org: float = Field(..., ge=0.0)
    new_balance_orig: float = Field(..., ge=0.0)
    name_dest: str
    old_balance_dest: float = Field(..., ge=0.0)
    new_balance_dest: float = Field(..., ge=0.0)

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    is_fraud: int
    is_flagged_fraud: int
    predicted_fraud: Optional[int] = None
    fraud_probability: Optional[float] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = "LOW"
    status: Optional[str] = "UNREVIEWED"
    rule_flags: Optional[Any] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    limit: int
    offset: int
