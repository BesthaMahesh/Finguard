"""
Market & Credit Risk Agent (Node 5 in FinGuard 10-Agent Architecture).
Evaluates origin account liquidity exposure, portfolio volatility, and parametric 95% Value at Risk (VaR),
providing an explainable credit risk grade and liquidity stress score.
"""
import time
from datetime import datetime, timezone
from typing import Dict, Any
from backend.agents.agent_state import InvestigationState, AgentTimelineStep

def market_credit_risk_agent(state: InvestigationState) -> InvestigationState:
    """
    Evaluates account-level exposure, liquidity depletion deltas, and parametric 1-day 95% VaR.
    Calculates credit risk grade (AAA to CCC/D) without introducing target leakage.
    """
    start_time = time.time()
    tx = state.get("validated_transaction") or state.get("raw_transaction_data", {})
    
    amount = float(tx.get("amount", 0.0) or 0.0)
    old_balance = float(tx.get("oldbalanceOrg") if tx.get("oldbalanceOrg") is not None else tx.get("old_balance_org", 0.0) or 0.0)
    new_balance = float(tx.get("newbalanceOrig") if tx.get("newbalanceOrig") is not None else tx.get("new_balance_orig", 0.0) or 0.0)
    tx_type = str(tx.get("type", "PAYMENT")).upper()

    # 1. Liquidity Stress & Exposure Ratio
    available_funds = max(old_balance, 1.0)
    exposure_ratio = min(1.0, amount / available_funds) if available_funds > 0 else 1.0

    # 2. Portfolio / Account Volatility Estimation
    # Under standard retail banking, baseline daily volatility is ~2.5%
    # Sudden high drain or rapid liquidation elevates modeled exposure volatility
    if exposure_ratio >= 0.8:
        effective_volatility = 0.125  # 12.5% daily stress volatility
    elif exposure_ratio >= 0.4:
        effective_volatility = 0.065  # 6.5% daily moderate volatility
    else:
        effective_volatility = 0.025  # 2.5% baseline stable volatility

    # 3. Parametric 95% 1-Day Value at Risk (VaR)
    # VaR_95 = 1.645 * Volatility * Exposure Base
    balance_base = max(old_balance, amount)
    var_95_1day = round(1.645 * effective_volatility * balance_base, 2)

    # 4. Credit Risk Scoring (0 to 100) & Qualitative Rating Grade
    credit_score = 10.0
    if new_balance < 0:
        credit_score += 65.0  # Overdraft / negative equity exposure
    elif new_balance == 0 and amount > 5000:
        credit_score += 45.0  # Complete account drain
    elif exposure_ratio > 0.75:
        credit_score += 35.0  # Severe liquidity stress
    elif exposure_ratio > 0.40:
        credit_score += 20.0

    if tx_type in ("TRANSFER", "CASH_OUT") and amount > 50000:
        credit_score += 25.0

    credit_score = min(100.0, max(5.0, round(credit_score, 1)))

    if credit_score < 25.0:
        grade = "AAA (Prime / Low Risk)"
    elif credit_score < 50.0:
        grade = "A- (Moderate Exposure)"
    elif credit_score < 75.0:
        grade = "BBB (Elevated Credit Stress)"
    else:
        grade = "CCC/D (High Default / Exhaustion Risk)"

    summary_text = (
        f"Parametric 95% 1-Day VaR: ${var_95_1day:,.2f} | Exposure Ratio: {exposure_ratio * 100:.1f}% | "
        f"Credit Rating: {grade} (Score: {credit_score}/100)"
    )

    market_risk_data = {
        "var_95_1day": var_95_1day,
        "exposure_ratio": round(exposure_ratio, 4),
        "effective_volatility": round(effective_volatility, 4),
        "credit_risk_score": credit_score,
        "credit_risk_grade": grade,
        "liquidity_exhaustion": new_balance <= 0.0 and old_balance > 0.0,
        "summary": summary_text
    }

    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))
    timeline.append(AgentTimelineStep(
        agent="Market & Credit Risk Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=summary_text,
        timestamp=datetime.now(timezone.utc).isoformat()
    ))

    return {
        **state,
        "market_credit_risk": market_risk_data,
        "timeline": timeline
    }

