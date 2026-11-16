import time
import math
from datetime import datetime, timezone
from typing import List, Dict, Any
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.ml.leakage_guard import LeakageGuard

def data_quality_agent(state: InvestigationState) -> InvestigationState:
    """
    Deterministic Data Quality & Ledger Integrity Agent.
    Reconciles sender/recipient balance changes against transaction amount,
    detects impossible merchant balances and non-finite values, and audits feature leakage.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    issues: List[Dict[str, Any]] = []
    flags: List[str] = []

    tx_type = str(tx.get("type", "")).upper()
    dest = str(tx.get("nameDest", tx.get("name_dest", ""))).strip()
    is_merchant_dest = dest.startswith("M")

    # Extract numerical fields with fallback support for both snake_case and camelCase
    try:
        amount = float(tx.get("amount", 0.0))
        old_orig = float(tx.get("oldbalanceOrg", tx.get("old_balance_org", 0.0)))
        new_orig = float(tx.get("newbalanceOrig", tx.get("new_balance_orig", 0.0)))
        old_dest = float(tx.get("oldbalanceDest", tx.get("old_balance_dest", 0.0)))
        new_dest = float(tx.get("newbalanceDest", tx.get("new_balance_dest", 0.0)))
    except (ValueError, TypeError):
        amount, old_orig, new_orig, old_dest, new_dest = 0.0, 0.0, 0.0, 0.0, 0.0

    # 1. Non-finite or negative value detection
    raw_nums = [amount, old_orig, new_orig, old_dest, new_dest]
    if any(math.isnan(n) or math.isinf(n) for n in raw_nums) or any(n < 0 for n in [old_orig, new_orig, old_dest, new_dest]) or amount <= 0:
        flags.append("NEGATIVE_OR_NONFINITE_VALUES")
        issues.append({
            "flag": "NEGATIVE_OR_NONFINITE_VALUES",
            "message": "Transaction contains non-positive amount, negative balances, or non-finite numbers."
        })

    # 2. Impossible Merchant Balance (PaySim semantics: M-accounts are terminal endpoints with zero balance)
    if is_merchant_dest and (old_dest > 0.0 or new_dest > 0.0):
        flags.append("IMPOSSIBLE_MERCHANT_BALANCE")
        issues.append({
            "flag": "IMPOSSIBLE_MERCHANT_BALANCE",
            "message": f"Merchant destination '{dest}' has nonzero balance (old: ${old_dest:,.2f}, new: ${new_dest:,.2f}). PaySim merchant accounts must be 0.0.",
            "old_balance_dest": old_dest,
            "new_balance_dest": new_dest
        })

    # 3. Deterministic Ledger Reconciliation
    # Outbound: old_orig - amount should equal new_orig
    # Inbound (CASH_IN): old_orig + amount should equal new_orig
    origin_variance = 0.0
    if tx_type in ("TRANSFER", "CASH_OUT", "PAYMENT", "DEBIT"):
        origin_variance = round((old_orig - amount) - new_orig, 2)
    elif tx_type == "CASH_IN":
        origin_variance = round((old_orig + amount) - new_orig, 2)

    dest_variance = 0.0
    if not is_merchant_dest and tx_type in ("TRANSFER", "CASH_IN"):
        dest_variance = round((new_dest - old_dest) - amount, 2)

    abs_orig_var = abs(origin_variance)
    abs_dest_var = abs(dest_variance)

    if abs_orig_var > 10000.0 or abs_dest_var > 10000.0:
        flags.append("LEDGER_VARIANCE_MAJOR")
        issues.append({
            "flag": "LEDGER_VARIANCE_MAJOR",
            "message": f"Major unexplained ledger discrepancy detected. Origin variance: ${origin_variance:,.2f}, Destination variance: ${dest_variance:,.2f}.",
            "origin_variance": origin_variance,
            "dest_variance": dest_variance,
            "threshold": 10000.0
        })
    elif abs_orig_var > 1.0 or abs_dest_var > 1.0:
        flags.append("LEDGER_VARIANCE_MINOR")
        issues.append({
            "flag": "LEDGER_VARIANCE_MINOR",
            "message": f"Minor unexplained ledger variance (>1.0 currency unit). Origin variance: ${origin_variance:,.2f}, Destination variance: ${dest_variance:,.2f}.",
            "origin_variance": origin_variance,
            "dest_variance": dest_variance,
            "threshold": 1.0
        })

    # 4. Target Feature Leakage Guard
    is_clean, violations = LeakageGuard.audit_features(list(tx.keys()))
    if not is_clean:
        flags.append("FEATURE_LEAKAGE_DETECTED")
        for v in violations:
            issues.append({"flag": "FEATURE_LEAKAGE", "message": v})

    quality_status = "FLAGGED" if issues else "PASSED"
    duration = (time.time() - start_time) * 1000.0

    timeline = list(state.get("timeline", []))
    flag_summary = f"{len(issues)} flags ({', '.join(flags)})" if issues else "Zero flags. Ledger fully reconciled."
    timeline.append(AgentTimelineStep(
        agent="Data Quality Agent",
        status="COMPLETED" if not issues else "FLAGGED",
        duration_ms=round(duration, 2),
        output_summary=f"Quality check {quality_status}: {flag_summary}",
        timestamp=datetime.now(timezone.utc).isoformat()
    ))

    return {
        **state,
        "data_quality_report": {
            "status": quality_status,
            "flags": flags,
            "issues": issues,
            "origin_variance": origin_variance,
            "dest_variance": dest_variance,
            "leakage_audit": "PASSED" if is_clean else "VIOLATIONS",
            "checked_at": datetime.now(timezone.utc).isoformat()
        },
        "timeline": timeline
    }
