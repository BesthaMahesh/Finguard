import time
from datetime import datetime
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.agents.llm_client import llm_client

def explainability_agent(state: InvestigationState) -> InvestigationState:
    """
    Summarizes model feature contributions and supporting evidence into an objective,
    explainable investigation summary without unsubstantiated causal claims.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    risk = state.get("risk_assessment", {})
    features = state.get("feature_attributions", [])
    citations = state.get("policy_citations", [])

    top_features_desc = ", ".join(
        [f"{f.get('display_name')}: {f.get('feature_value')} ({f.get('impact')})" for f in features[:4]]
    )
    
    citation_text = ""
    if citations:
        citation_text = f"Governing Policy: {citations[0].get('document_id')} ({citations[0].get('section')}) - '{citations[0].get('excerpt', '')[:120]}...'"

    prompt = (
        f"Provide a concise, 2-3 sentence objective financial risk explanation docket for an investigator.\n"
        f"Transaction Details: Type: {tx.get('type')}, Amount: ${tx.get('amount', 0):,.2f}, Origin: {tx.get('nameOrig')}, Destination: {tx.get('nameDest')}.\n"
        f"Risk Score: {risk.get('composite_risk_score')}/100 ({risk.get('operational_risk_level')}).\n"
        f"Key Model Signals: {top_features_desc}.\n"
        f"Policy Grounding: {citation_text}.\n"
        f"STRICT CONSTRAINT: Do not state that the entity committed a crime or that fraud is proven. State observations and risk factors objectively."
    )

    system_prompt = (
        "You are an expert financial crimes intelligence explainability specialist. "
        "Summarize risk indicators objectively with strict adherence to evidence and policies."
    )

    llm_resp = llm_client.generate_completion(system_prompt=system_prompt, user_prompt=prompt, max_tokens=250)
    explanation = llm_resp.get("content", "").strip()

    if not explanation:
        # High quality objective deterministic fallback
        explanation = (
            f"Transaction evaluated with a composite risk score of {risk.get('composite_risk_score')}/100 ({risk.get('operational_risk_level')}). "
            f"Elevated risk signals stem primarily from {top_features_desc or 'transaction patterns'}. "
            f"{citation_text} Triage flagged for standard investigative review."
        )

    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))
    timeline.append(AgentTimelineStep(
        agent="Explainability Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=f"Synthesized objective risk narrative ({llm_resp.get('provider')})",
        timestamp=datetime.utcnow().isoformat()
    ))

    return {
        **state,
        "explanation_summary": explanation,
        "tokens_consumed": state.get("tokens_consumed", 0) + llm_resp.get("tokens_used", 0),
        "timeline": timeline
    }
