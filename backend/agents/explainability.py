import time
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.agents.llm_client import llm_client
from backend.observability.metrics import metrics_collector

try:
    from langchain_core.callbacks.manager import dispatch_custom_event
except ImportError:
    def dispatch_custom_event(*args, **kwargs):
        pass

FORBIDDEN_WORDS_WHEN_FLAGGED = [
    "neutralized", "mitigated", "outweighed", "offset",
    "counterbalanced", "dismissed", "negated", "excused", "justified by"
]

def extract_numbers_from_text(text: str) -> List[float]:
    """Extracts raw numerical values from text, stripping currency signs and commas."""
    found = []
    # Match numbers with optional decimal point and optional commas
    matches = re.findall(r"(?:[\$]?)([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|\.[0-9]+|[0-9]+)", text)
    for m in matches:
        clean = m.replace(",", "").replace("$", "").strip()
        if clean:
            try:
                found.append(float(clean))
            except ValueError:
                pass
    return found

def validate_narrative(
    narrative: str,
    flags: List[str],
    allowed_numbers: List[float]
) -> Tuple[bool, str]:
    """
    Validates LLM explanation against strict factual and compliance rules:
    1. Must mention triggered rules / flags.
    2. Every number it contains must exist in the allowed structured facts.
    3. Must NOT contain phrases like 'neutralized', 'mitigated', 'outweighed' when flags exist.
    """
    if not narrative or len(narrative.strip()) < 15:
        return False, "Narrative is empty or excessively brief."

    narrative_lower = narrative.lower()

    # Rule 3: Forbidden mitigation phrases when flags exist
    if flags:
        for forbidden in FORBIDDEN_WORDS_WHEN_FLAGGED:
            if forbidden in narrative_lower:
                return False, f"Narrative contains forbidden risk-mitigation term: '{forbidden}'."

    # Rule 1: Mention every primary flag or rule concept
    for flag in flags:
        flag_norm = flag.lower().replace("_", " ")
        # Check either exact flag or constituent keywords
        keywords = [k for k in flag_norm.split() if k not in ("rule", "detected", "and", "or", "values")]
        if not any(kw in narrative_lower for kw in keywords):
            return False, f"Narrative failed to explicitly reference triggered finding: '{flag}'."

    # Rule 2: Numeric grounding check
    found_numbers = extract_numbers_from_text(narrative)
    # Check if numbers in narrative are approximately in allowed numbers
    for num in found_numbers:
        # Ignore common harmless small integers like 1, 2, 3, 4, 10, 100 (from percentage/scale)
        if num in (1.0, 2.0, 3.0, 4.0, 10.0, 100.0, 0.0):
            continue
        # Check against allowed list with small rounding tolerance
        is_allowed = any(abs(num - a) < 0.1 for a in allowed_numbers)
        if not is_allowed:
            return False, f"Narrative hallucinated number ({num}) not present in transaction facts."

    return True, "VALIDATED"

def build_deterministic_narrative(
    tx: Dict[str, Any],
    risk: Dict[str, Any],
    flags: List[str],
    features: List[Dict[str, Any]],
    citations: List[Dict[str, Any]],
    dq_report: Dict[str, Any]
) -> str:
    """Builds an objective, fully grounded deterministic investigation narrative."""
    score = risk.get("composite_risk_score", 0.0)
    tier = risk.get("operational_risk_level", "LOW")
    amount = float(tx.get("amount", 0.0))
    tx_type = tx.get("type", "TRANSACTION")
    name_orig = tx.get("nameOrig", tx.get("name_orig", "origin"))
    name_dest = tx.get("nameDest", tx.get("name_dest", "destination"))

    lines = []
    lines.append(
        f"Transaction #{tx.get('id', 'N/A')} ({tx_type} of ${amount:,.2f} from {name_orig} to {name_dest}) "
        f"evaluated with composite risk score {score:.1f}/100 ({tier})."
    )

    if flags:
        flag_str = ", ".join(flags)
        lines.append(f"Autonomous evaluation flagged statutory compliance violations: {flag_str}.")
        orig_var = dq_report.get("origin_variance")
        if orig_var is not None and abs(orig_var) > 1.0:
            lines.append(f"Accounting reconciliation detected unexplained origin ledger variance of ${orig_var:,.2f}.")

    if features:
        top_sig = ", ".join([f"{f.get('display_name')}: {f.get('feature_value')}" for f in features[:2]])
        lines.append(f"Top model attributions: {top_sig}.")

    if citations:
        c = citations[0]
        lines.append(f"Grounded in policy {c.get('document_id')} ({c.get('section', 'General')}).")

    if score >= 65.0 or flags:
        lines.append("Flagged for mandatory 4-Eyes investigator review.")
    else:
        lines.append("Routine transaction cleared under fast-track protocol.")

    return " ".join(lines)

def explainability_agent(state: InvestigationState) -> InvestigationState:
    """
    Explainability Agent:
    Receives ONLY structured facts (score, tier, triggered rules, flags with exact numbers,
    TreeSHAP top features, retrieved policy citations).
    Generates an objective summary via Groq LLM, executes a strict post-generation validator,
    and falls back to deterministic synthesis if validation fails.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    risk = state.get("risk_assessment", {})
    features = state.get("feature_attributions", [])
    citations = state.get("policy_citations", [])
    dq_report = state.get("data_quality_report", {})

    score = float(risk.get("composite_risk_score", 0.0))
    tier = risk.get("operational_risk_level", "LOW")
    tx_type = tx.get("type", "PAYMENT")
    amount = float(tx.get("amount", 0.0))
    old_orig = float(tx.get("oldbalanceOrg", tx.get("old_balance_org", 0.0)))
    new_orig = float(tx.get("newbalanceOrig", tx.get("new_balance_orig", 0.0)))
    old_dest = float(tx.get("oldbalanceDest", tx.get("old_balance_dest", 0.0)))
    new_dest = float(tx.get("newbalanceDest", tx.get("new_balance_dest", 0.0)))
    orig_var = dq_report.get("origin_variance", 0.0)
    dest_var = dq_report.get("dest_variance", 0.0)

    # Gather flags from data quality and model prediction
    dq_flags = dq_report.get("flags", [])
    pred_rules = state.get("model_prediction", {}).get("rule_flags", [])
    rule_ids = [r.get("rule_id", "") if isinstance(r, dict) else str(r) for r in pred_rules]
    all_flags = list(dict.fromkeys(dq_flags + rule_ids))
    all_flags = [f for f in all_flags if f != "SAFEGUARD_VERIFIED_MERCHANT"]

    # Allowed numerical facts for grounding validator
    allowed_numbers = [score, amount, old_orig, new_orig, old_dest, new_dest]
    if orig_var:
        allowed_numbers.extend([orig_var, abs(orig_var)])
    if dest_var:
        allowed_numbers.extend([dest_var, abs(dest_var)])
    for f in features:
        val = f.get("feature_value")
        if isinstance(val, (int, float)):
            allowed_numbers.append(float(val))

    top_features_desc = ", ".join(
        [f"{f.get('display_name')}: {f.get('feature_value')} ({f.get('impact')})" for f in features[:4]]
    )

    citation_text = ""
    if citations:
        c = citations[0]
        citation_text = f"Policy {c.get('document_id')} ({c.get('section', 'General')})"

    structured_facts = (
        f"FACTS:\n"
        f"- Transaction Type: {tx_type}\n"
        f"- Amount: ${amount:,.2f}\n"
        f"- Origin Account: {tx.get('nameOrig', tx.get('name_orig'))} (Old Balance: ${old_orig:,.2f}, New Balance: ${new_orig:,.2f})\n"
        f"- Destination Account: {tx.get('nameDest', tx.get('name_dest'))} (Old Balance: ${old_dest:,.2f}, New Balance: ${new_dest:,.2f})\n"
        f"- Origin Balance Variance: ${orig_var:,.2f}\n"
        f"- Destination Balance Variance: ${dest_var:,.2f}\n"
        f"- Composite Risk Score: {score:.1f}/100 ({tier})\n"
        f"- Triggered Rules & Flags: {', '.join(all_flags) if all_flags else 'None'}\n"
        f"- Top Model Signals: {top_features_desc or 'None'}\n"
        f"- Governing Policy: {citation_text or 'None'}"
    )

    system_prompt = (
        "You are FinGuard Explainability Specialist. Your mandate is to write a concise, 2-3 sentence objective explanation "
        "of the observed facts and risk indicators for an investigator docket.\n"
        "STRICT CONSTRAINTS:\n"
        "1. Explain ONLY the provided structured facts. Never speculate, assume intent, or declare criminal guilt.\n"
        "2. Do NOT re-judge or reduce the risk. If flags or variances exist, you MUST mention them.\n"
        "3. NEVER use words like 'neutralized', 'mitigated', 'outweighed', 'offset', or 'justified by' to excuse flagged anomalies.\n"
        "4. Include only the numbers provided in the facts."
    )

    user_prompt = f"{structured_facts}\n\nWrite an objective docket summary strictly following the constraints:"

    explanation = ""
    is_fallback = False
    validator_result = "UNCHECKED"
    tokens_consumed = 0
    provider = "groq"

    # Try LLM generation if available
    if llm_client._get_client() is not None:
        try:
            # First attempt
            resp = llm_client.generate_completion(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=220)
            candidate = resp.get("content", "").strip()
            tokens_consumed += resp.get("tokens_used", 0)

            valid, reason = validate_narrative(candidate, all_flags, allowed_numbers)
            if valid:
                explanation = candidate
                validator_result = "PASSED (1st attempt)"
            else:
                # Retry once with stricter repair prompt
                repair_prompt = (
                    f"{user_prompt}\n\n"
                    f"PREVIOUS DRAFT REJECTED: {reason}\n"
                    f"Rewrite immediately. You MUST mention {all_flags} and MUST NOT use any mitigating words."
                )
                resp2 = llm_client.generate_completion(system_prompt=system_prompt, user_prompt=repair_prompt, max_tokens=220)
                candidate2 = resp2.get("content", "").strip()
                tokens_consumed += resp2.get("tokens_used", 0)

                valid2, reason2 = validate_narrative(candidate2, all_flags, allowed_numbers)
                if valid2:
                    explanation = candidate2
                    validator_result = "PASSED (repaired)"
                else:
                    validator_result = f"FAILED: {reason2} -> Deterministic Fallback"
                    is_fallback = True
        except Exception as e:
            validator_result = f"LLM_ERROR: {e} -> Deterministic Fallback"
            is_fallback = True
    else:
        is_fallback = True
        validator_result = "OFFLINE -> Deterministic Fallback"

    if is_fallback or not explanation:
        provider = "deterministic_rule_synthesizer"
        explanation = build_deterministic_narrative(tx, risk, all_flags, features, citations, dq_report)
        is_fallback = True

    # Stream out the validated tokens smoothly to UI
    words = explanation.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        try:
            dispatch_custom_event("agent_token", {"agent": "explainability", "text": chunk})
        except Exception:
            pass
        if is_fallback:
            time.sleep(0.01)

    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))
    status_label = "FALLBACK_NARRATIVE" if is_fallback else "COMPLETED"
    timeline.append(AgentTimelineStep(
        agent="Explainability Agent",
        status=status_label,
        duration_ms=round(duration, 2),
        output_summary=f"Synthesized objective risk narrative ({provider}). Validator: {validator_result}",
        timestamp=datetime.now(timezone.utc).isoformat()
    ))

    return {
        **state,
        "explanation_summary": explanation,
        "explanation_validation": {
            "status": "VALIDATED" if not is_fallback else "FALLBACK",
            "is_fallback": is_fallback,
            "validator_result": validator_result,
            "provider": provider
        },
        "tokens_consumed": state.get("tokens_consumed", 0) + tokens_consumed,
        "timeline": timeline
    }
