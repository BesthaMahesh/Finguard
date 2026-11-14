import time
from datetime import datetime, timezone
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.agents.llm_client import llm_client
from backend.observability.metrics import metrics_collector

try:
    from langchain_core.callbacks.manager import dispatch_custom_event
except ImportError:
    def dispatch_custom_event(*args, **kwargs):
        pass

def explainability_agent(state: InvestigationState) -> InvestigationState:
    """
    Summarizes model feature contributions and supporting evidence into an objective,
    explainable investigation summary without unsubstantiated causal claims.
    Emits live streaming tokens via dispatch_custom_event when invoked within an event stream.
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
        f"Risk Score: {risk.get('composite_risk_score', 0)}/100 ({risk.get('operational_risk_level', 'LOW')}).\n"
        f"Key Model Signals: {top_features_desc}.\n"
        f"Policy Grounding: {citation_text}.\n"
        f"STRICT CONSTRAINT: Do not state that the entity committed a crime or that fraud is proven. State observations and risk factors objectively."
    )

    system_prompt = (
        "You are an expert financial crimes intelligence explainability specialist. "
        "Summarize risk indicators objectively with strict adherence to evidence and policies."
    )

    explanation_tokens = []
    tokens_consumed = 0
    provider = "groq"

    # Try streaming from Groq
    if llm_client._get_client() is not None:
        try:
            for chunk in llm_client.stream_completion(system_prompt=system_prompt, user_prompt=prompt, max_tokens=250):
                explanation_tokens.append(chunk)
                try:
                    dispatch_custom_event("agent_token", {"agent": "explainability", "text": chunk})
                except Exception:
                    pass
            tokens_consumed = max(len(explanation_tokens) * 2, 60)
            metrics_collector.record_agent_run(latency_ms=(time.time() - start_time) * 1000.0, tokens_used=tokens_consumed)
        except Exception:
            explanation_tokens = []

    explanation = "".join(explanation_tokens).strip()

    if not explanation:
        # High quality objective deterministic fallback
        provider = "deterministic_rule_synthesizer"
        fallback_narrative = (
            f"Transaction evaluated with a composite risk score of {risk.get('composite_risk_score', 0)}/100 ({risk.get('operational_risk_level', 'LOW')}). "
            f"Elevated risk signals stem primarily from {top_features_desc or 'unusual transaction velocity and balance liquidation'}. "
            f"{citation_text} Triage flagged for standard investigative review."
        )
        explanation = fallback_narrative
        
        # Progressive streaming simulation for smooth UI rendering in offline/fallback mode
        words = fallback_narrative.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            try:
                dispatch_custom_event("agent_token", {"agent": "explainability", "text": chunk})
            except Exception:
                pass
            time.sleep(0.015)
        
        tokens_consumed = len(words)
        metrics_collector.record_agent_run(latency_ms=(time.time() - start_time) * 1000.0, tokens_used=tokens_consumed)

    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))
    timeline.append(AgentTimelineStep(
        agent="Explainability Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=f"Synthesized objective risk narrative ({provider})",
        timestamp=datetime.now(timezone.utc).isoformat()
    ))

    return {
        **state,
        "explanation_summary": explanation,
        "tokens_consumed": state.get("tokens_consumed", 0) + tokens_consumed,
        "timeline": timeline
    }
