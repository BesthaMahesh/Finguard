import time
from datetime import datetime
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.rag.retriever import PolicyRetriever

def policy_compliance_agent(state: InvestigationState) -> InvestigationState:
    """
    Policy & Compliance Agent:
    Retrieves regulatory guidelines, official AML standards, and internal risk procedures
    matching transaction attributes and risk severity.
    Distinguishes official statutory directives from internal policies and research papers.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    risk = state.get("risk_assessment", {})
    
    # Construct targeted regulatory query
    tx_type = tx.get("type", "TRANSFER")
    amount = tx.get("amount", 0)
    query = f"{tx_type} rapid liquidation customer due diligence wire transfer threshold {amount}"
    
    # Retrieve top grounded policy citations
    citations = PolicyRetriever.search_policies(
        query=query,
        top_k=3,
        min_relevance_score=0.40
    )

    # Classify retrieved evidence by provenance
    official_count = sum(1 for c in citations if c.get("source_type") == "official_regulation")
    internal_count = sum(1 for c in citations if c.get("source_type") == "sample_internal_policy")
    research_count = sum(1 for c in citations if c.get("source_type") == "research")

    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))

    if citations:
        primary_ref = citations[0]["citation_location"]
        summary_text = (
            f"Grounded with {len(citations)} citations ({official_count} official, "
            f"{internal_count} internal policy, {research_count} research). Primary: {primary_ref}"
        )
    else:
        summary_text = "No direct policy citations met the 0.40 relevance threshold; using baseline threshold controls."

    timeline.append(AgentTimelineStep(
        agent="Policy & Compliance Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=summary_text,
        timestamp=datetime.utcnow().isoformat()
    ))

    return {
        **state,
        "policy_citations": citations,
        "timeline": timeline
    }
