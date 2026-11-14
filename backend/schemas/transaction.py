from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime

ALLOWED_TRANSACTION_TYPES = {"PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"}

class TransactionBase(BaseModel):
    step: int = Field(default=1, ge=1, description="Simulation or batch step number")
    type: str = Field(..., description="PAYMENT, TRANSFER, CASH_OUT, DEBIT, CASH_IN")
    amount: float = Field(..., gt=0.0, description="Transaction amount must be strictly positive")
    name_orig: str = Field(..., min_length=2, description="Origin account identifier")
    old_balance_org: float = Field(..., ge=0.0, description="Sender pre-transaction balance")
    new_balance_orig: float = Field(..., ge=0.0, description="Sender post-transaction balance")
    name_dest: str = Field(..., min_length=2, description="Destination account identifier")
    old_balance_dest: float = Field(default=0.0, ge=0.0, description="Recipient pre-transaction balance")
    new_balance_dest: float = Field(default=0.0, ge=0.0, description="Recipient post-transaction balance")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        upper = v.upper().strip()
        if upper not in ALLOWED_TRANSACTION_TYPES:
            raise ValueError(f"Invalid transaction type '{v}'. Allowed types: {', '.join(sorted(ALLOWED_TRANSACTION_TYPES))}")
        return upper

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0.0:
            raise ValueError("Transaction amount must be strictly greater than zero.")
        return round(v, 2)

class TransactionCreate(TransactionBase):
    @model_validator(mode="after")
    def validate_ledger_consistency(self):
        t = self.type
        old_org = self.old_balance_org
        new_org = self.new_balance_orig

        # Outbound types: money leaves the sender
        if t in {"PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT"}:
            if new_org > old_org:
                raise ValueError(
                    f"Impossible ledger: Origin balance cannot increase from ${old_org:,.2f} to ${new_org:,.2f} on outbound {t} transaction."
                )
            if new_org > round(old_org - self.amount, 2) + 0.01:
                raise ValueError(
                    f"Impossible ledger discrepancy: For {t} of ${self.amount:,.2f}, origin balance cannot decrease by less than the transferred amount (old: ${old_org:,.2f}, new: ${new_org:,.2f})."
                )
        elif t == "CASH_IN":
            if new_org < old_org:
                raise ValueError(
                    f"Impossible ledger: Origin balance cannot decrease from ${old_org:,.2f} to ${new_org:,.2f} on inbound CASH_IN transaction."
                )
        return self

class TransactionResponse(TransactionBase):
    id: int
    is_fraud: Optional[int] = None  # None for newly created transactions (ground truth unknown)
    is_flagged_fraud: Optional[int] = 0
    predicted_fraud: Optional[int] = None
    fraud_probability: Optional[float] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = "LOW"
    status: Optional[str] = "UNREVIEWED"
    rule_flags: Optional[Any] = None
    case_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    limit: int
    offset: int
