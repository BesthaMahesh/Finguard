"""
FinGuard Unified Decision Policy Engine (Single Source of Truth).
Maps composite risk scores, tiers, and rule/data quality flags to:
- decision (APPROVE / REVIEW / MANDATORY_REVIEW / ESCALATE)
- requires_human_review (bool)
- case_created (bool)
- case priority (LOW / MEDIUM / HIGH / CRITICAL)
- case title (Neutral, accurate, descriptive)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DecisionPolicyResult(BaseModel):
    decision: str  # APPROVE | REVIEW | MANDATORY_REVIEW | ESCALATE
    risk_tier: str  # LOW | MEDIUM | HIGH | CRITICAL
    priority: str   # LOW | MEDIUM | HIGH | CRITICAL
    requires_human_review: bool
    case_created: bool
    title: str
    summary_reason: str

def evaluate_decision_policy(
    risk_score: float,
    rule_flags: Optional[List[str]] = None,
    data_quality_flags: Optional[List[str]] = None,
    transaction: Optional[Dict[str, Any]] = None
) -> DecisionPolicyResult:
    """
    Unified deterministic evaluation of operational decisions and case requirements.
    Guarantees strict mathematical consistency across all platform layers.
    """
    all_flags = list(rule_flags or []) + list(data_quality_flags or [])
    # Filter out positive safeguards and informational status tags
    flags = [f for f in all_flags if not f.startswith("SAFEGUARD_") and f not in ("INFO", "PASSED")]
    tx = transaction or {}
    tx_type = str(tx.get("type", "TRANSACTION")).upper()
    amount = float(tx.get("amount", 0.0))

    # Identify primary flag description for neutral case title
    primary_reason = "routine flow"
    has_major_discrepancy = any("MAJOR" in f or "IMPOSSIBLE" in f for f in flags)
    has_minor_discrepancy = any("MINOR" in f for f in flags)
    has_liquidation = any("LIQUIDATION" in f or "DRAIN" in f for f in flags)

    if has_major_discrepancy:
        primary_reason = "ledger variance major"
    elif has_liquidation:
        primary_reason = "rapid account liquidation"
    elif has_minor_discrepancy:
        primary_reason = "ledger variance minor"
    elif flags:
        primary_reason = flags[0].lower().replace("_", " ")

    # Map by operational severity and rule floors
    if risk_score >= 85.0:
        return DecisionPolicyResult(
            decision="ESCALATE",
            risk_tier="CRITICAL",
            priority="CRITICAL",
            requires_human_review=True,
            case_created=True,
            title=f"Critical Escalation: {tx_type} ${amount:,.2f} - {primary_reason}",
            summary_reason=f"Composite risk {risk_score:.1f}/100 exceeds critical threshold (85.0). Immediate forensic triage required."
        )
    elif risk_score >= 65.0 or has_major_discrepancy:
        return DecisionPolicyResult(
            decision="MANDATORY_REVIEW",
            risk_tier="HIGH",
            priority="HIGH",
            requires_human_review=True,
            case_created=True,
            title=f"Mandatory Review: {tx_type} ${amount:,.2f} - {primary_reason}",
            summary_reason=f"High risk score ({risk_score:.1f}/100) or major ledger discrepancy requires mandatory 4-Eyes verification."
        )
    elif risk_score >= 35.0 or has_minor_discrepancy or flags:
        return DecisionPolicyResult(
            decision="REVIEW",
            risk_tier="MEDIUM",
            priority="MEDIUM",
            requires_human_review=True,
            case_created=True,
            title=f"Review: {tx_type} ${amount:,.2f} - {primary_reason}",
            summary_reason=f"Elevated risk indicators ({risk_score:.1f}/100) flagged for secondary investigator review."
        )
    else:
        # Strictly LOW risk with no rule violations -> APPROVE, NO case created
        return DecisionPolicyResult(
            decision="APPROVE",
            risk_tier="LOW",
            priority="LOW",
            requires_human_review=False,
            case_created=False,
            title=f"Cleared: {tx_type} ${amount:,.2f}",
            summary_reason=f"Routine transaction cleared with composite risk score of {risk_score:.1f}/100. Fast-track approval granted."
        )

def generate_next_case_number(db) -> str:
    """
    Generates the next sequential Case ID from its own monotonic sequence (CASE-FG-000001...),
    completely independent of transaction ID.
    """
    from backend.db.models import InvestigationCase
    count = db.query(InvestigationCase).count()
    candidate = count + 1
    while db.query(InvestigationCase).filter_by(case_number=f"CASE-FG-{candidate:06d}").first() is not None:
        candidate += 1
    return f"CASE-FG-{candidate:06d}"

