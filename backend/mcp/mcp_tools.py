import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError

from backend.db.session import SessionLocal
from backend.db.models import Transaction, InvestigationCase, AuditEvent, generate_uuid
from backend.ml.model_service import model_service
from backend.rag.retriever import PolicyRetriever

logger = logging.getLogger(__name__)

# Pydantic Schemas for MCP Tool Input Validation
class TransactionLookupInput(BaseModel):
    transaction_id: int = Field(..., description="Unique integer ID of the transaction")

class AccountLookupInput(BaseModel):
    account_id: str = Field(..., min_length=3, max_length=50, description="Synthetic account identifier (e.g., C1234567 or M9876543)")

class RiskCalculateInput(BaseModel):
    step: int = Field(1, ge=1)
    type: str = Field(..., description="Transaction type (PAYMENT, TRANSFER, CASH_OUT, DEBIT, CASH_IN)")
    amount: float = Field(..., ge=0.0)
    name_orig: str = Field(..., min_length=2)
    old_balance_org: float = Field(..., ge=0.0)
    new_balance_orig: float = Field(..., ge=0.0)
    name_dest: str = Field(..., min_length=2)
    old_balance_dest: float = Field(..., ge=0.0)
    new_balance_dest: float = Field(..., ge=0.0)

class PolicySearchInput(BaseModel):
    query: str = Field(..., min_length=3, description="Search query for financial crime regulations or policies")
    top_k: int = Field(3, ge=1, le=10)

class CaseCreationInput(BaseModel):
    transaction_id: int
    title: str = Field(..., min_length=5)
    summary: str = Field(..., min_length=10)
    priority: str = Field("HIGH", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")

class CaseDispositionInput(BaseModel):
    case_id: str
    disposition: str = Field(..., pattern="^(ESCALATE_TO_SAR|FREEZE_ACCOUNT|REQUEST_ADDITIONAL_KYC|DISMISS_FALSE_POSITIVE)$")
    disposition_notes: str = Field(..., min_length=5)

class AuditQueryInput(BaseModel):
    limit: int = Field(20, ge=1, le=100)
    correlation_id: Optional[str] = None

class FinGuardMCPTools:
    """
    Standardized, permission-checked tools exposing FinGuard capabilities
    compliant with Model Context Protocol (MCP) conventions.
    """

    @staticmethod
    def log_tool_audit(action: str, target: str, actor: str, role: str, outcome: str = "SUCCESS", details: dict = None):
        try:
            db = SessionLocal()
            audit = AuditEvent(
                correlation_id=generate_uuid(),
                actor_id=actor,
                actor_role=role,
                action=f"MCP_TOOL_{action}",
                target_type="MCP_SERVICE",
                target_id=target,
                outcome=outcome,
                details_json=json.dumps(details or {})
            )
            db.add(audit)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to record MCP tool audit: {e}")

    @classmethod
    def lookup_transaction(cls, args: dict, user_role: str = "analyst", username: str = "system_agent") -> dict:
        """Looks up a specific transaction by ID."""
        try:
            validated = TransactionLookupInput(**args)
        except ValidationError as e:
            return {"error": f"Validation error: {e.errors()}", "status": "INVALID_INPUT"}

        db = SessionLocal()
        try:
            tx = db.query(Transaction).filter_by(id=validated.transaction_id).first()
            if not tx:
                return {"error": f"Transaction {validated.transaction_id} not found", "status": "NOT_FOUND"}

            cls.log_tool_audit("LOOKUP_TRANSACTION", str(tx.id), username, user_role)
            return {
                "transaction_id": tx.id,
                "step": tx.step,
                "type": tx.type,
                "amount": tx.amount,
                "name_orig": tx.name_orig,
                "old_balance_org": tx.old_balance_org,
                "new_balance_orig": tx.new_balance_orig,
                "name_dest": tx.name_dest,
                "old_balance_dest": tx.old_balance_dest,
                "new_balance_dest": tx.new_balance_dest,
                "risk_score": tx.risk_score,
                "risk_level": tx.risk_level,
                "status": tx.status,
                "is_historical_fraud_label": tx.is_fraud
            }
        finally:
            db.close()

    @classmethod
    def lookup_account(cls, args: dict, user_role: str = "analyst", username: str = "system_agent") -> dict:
        """Looks up synthetic profile and aggregate transaction metrics for an account."""
        try:
            validated = AccountLookupInput(**args)
        except ValidationError as e:
            return {"error": f"Validation error: {e.errors()}", "status": "INVALID_INPUT"}

        acc_id = validated.account_id
        db = SessionLocal()
        try:
            outbound = db.query(Transaction).filter_by(name_orig=acc_id).all()
            inbound = db.query(Transaction).filter_by(name_dest=acc_id).all()

            total_txs = len(outbound) + len(inbound)
            total_sent = sum(t.amount for t in outbound)
            total_received = sum(t.amount for t in inbound)
            high_risk_count = sum(1 for t in (outbound + inbound) if (t.risk_score or 0) >= 70.0)

            cls.log_tool_audit("LOOKUP_ACCOUNT", acc_id, username, user_role)
            return {
                "account_id": acc_id,
                "account_classification": "MERCHANT_ENTITY" if acc_id.startswith("M") else "CUSTOMER_RETAIL_ACCOUNT",
                "synthetic_note": "Confidential synthetic entity generated from PaySim simulation.",
                "total_transactions": total_txs,
                "total_volume_sent": round(total_sent, 2),
                "total_volume_received": round(total_received, 2),
                "high_risk_flagged_count": high_risk_count,
                "recent_outbound_ids": [t.id for t in outbound[:5]],
                "recent_inbound_ids": [t.id for t in inbound[:5]]
            }
        finally:
            db.close()

    @classmethod
    def calculate_risk(cls, args: dict, user_role: str = "analyst", username: str = "system_agent") -> dict:
        """Calculates ML fraud probability, applies transparent rules, and returns SHAP attributions."""
        try:
            validated = RiskCalculateInput(**args)
        except ValidationError as e:
            return {"error": f"Validation error: {e.errors()}", "status": "INVALID_INPUT"}

        result = model_service.predict_transaction(validated.model_dump())
        cls.log_tool_audit("CALCULATE_RISK", f"{validated.type}_{validated.amount}", username, user_role)
        return result

    @classmethod
    def search_policies(cls, args: dict, user_role: str = "analyst", username: str = "system_agent") -> dict:
        """Retrieves policy and compliance guidelines with source citations."""
        try:
            validated = PolicySearchInput(**args)
        except ValidationError as e:
            return {"error": f"Validation error: {e.errors()}", "status": "INVALID_INPUT"}

        citations = PolicyRetriever.search_policies(validated.query, top_k=validated.top_k)
        cls.log_tool_audit("SEARCH_POLICIES", validated.query, username, user_role)
        return {"query": validated.query, "citations": citations}

    @classmethod
    def create_investigation_case(cls, args: dict, user_role: str = "analyst", username: str = "system_agent") -> dict:
        """Creates a new fraud investigation case docket."""
        try:
            validated = CaseCreationInput(**args)
        except ValidationError as e:
            return {"error": f"Validation error: {e.errors()}", "status": "INVALID_INPUT"}

        db = SessionLocal()
        try:
            tx = db.query(Transaction).filter_by(id=validated.transaction_id).first()
            if not tx:
                return {"error": f"Transaction {validated.transaction_id} not found", "status": "NOT_FOUND"}

            case_number = f"CASE-FG-{tx.id:06d}"
            existing = db.query(InvestigationCase).filter_by(case_number=case_number).first()
            if existing:
                return {"case_id": existing.id, "case_number": existing.case_number, "status": "ALREADY_EXISTS"}

            case = InvestigationCase(
                case_number=case_number,
                transaction_id=tx.id,
                title=validated.title,
                status="OPEN",
                priority=validated.priority,
                assigned_to=username,
                risk_score=tx.risk_score or 50.0,
                summary=validated.summary,
                created_at=datetime.utcnow()
            )
            db.add(case)
            tx.status = "UNDER_INVESTIGATION"
            db.commit()
            db.refresh(case)

            cls.log_tool_audit("CREATE_CASE", case.case_number, username, user_role)
            return {"case_id": case.id, "case_number": case.case_number, "status": "CREATED"}
        finally:
            db.close()

    @classmethod
    def update_case_disposition(cls, args: dict, user_role: str = "investigator", username: str = "system_agent") -> dict:
        """Updates case disposition with mandatory 4-Eyes governance verification."""
        from backend.security.rbac import normalize_role, UserRole
        from datetime import timezone
        role_norm = normalize_role(user_role)
        if role_norm not in (UserRole.INVESTIGATOR, UserRole.ADMIN, UserRole.ADMINISTRATOR):
            return {"error": "Unauthorized: Case disposition requires 'investigator' or 'administrator' role.", "status": "FORBIDDEN"}

        try:
            validated = CaseDispositionInput(**args)
        except ValidationError as e:
            return {"error": f"Validation error: {e.errors()}", "status": "INVALID_INPUT"}

        db = SessionLocal()
        try:
            case = db.query(InvestigationCase).filter_by(id=validated.case_id).first()
            if not case:
                return {"error": "Case not found", "status": "NOT_FOUND"}

            case.disposition = validated.disposition
            case.disposition_notes = validated.disposition_notes
            case.reviewed_by = username
            case.reviewed_at = datetime.now(timezone.utc)
            case.status = "CLOSED_RESOLVED" if validated.disposition != "DISMISS_FALSE_POSITIVE" else "CLOSED_FALSE_POSITIVE"

            # Update linked transaction status
            if case.transaction:
                if validated.disposition == "DISMISS_FALSE_POSITIVE":
                    case.transaction.status = "CLEARED"
                elif validated.disposition in ("ESCALATE_TO_SAR", "FREEZE_ACCOUNT"):
                    case.transaction.status = "CONFIRMED_FRAUD"

            db.commit()
            cls.log_tool_audit("UPDATE_DISPOSITION", case.case_number, username, user_role, details={
                "disposition": validated.disposition,
                "notes": validated.disposition_notes
            })
            return {"case_id": case.id, "case_number": case.case_number, "new_status": case.status, "disposition": case.disposition}
        finally:
            db.close()

    @classmethod
    def check_synthetic_watchlist(cls, args: dict, user_role: str = "analyst", username: str = "system_agent") -> dict:
        """
        Simulated sanctions/PEP screening adapter using clearly labeled synthetic data.
        Does not connect to real OFAC/sanctions bureaus.
        """
        name = str(args.get("entity_name", "")).strip().upper()
        # Synthetic mock watchlist
        SYNTHETIC_WATCHLIST = {
            "C1305486145": {"entity": "Simulated Entity A", "list": "MOCK-OFAC-SYNTHETIC-SPEC-01", "risk": "CRITICAL"},
            "C840083671": {"entity": "Simulated Entity B", "list": "MOCK-PEP-SYNTHETIC-SPEC-02", "risk": "HIGH"}
        }

        hit = SYNTHETIC_WATCHLIST.get(name)
        cls.log_tool_audit("WATCHLIST_CHECK", name, username, user_role, details={"match": bool(hit)})

        return {
            "query_entity": name,
            "disclaimer": "SYNTHETIC ADAPTER: Mock internal screening list for evaluation only. Not connected to real bureaus.",
            "is_sanctions_match": hit is not None,
            "details": hit or {"message": "No match found in synthetic evaluation watchlist."}
        }
