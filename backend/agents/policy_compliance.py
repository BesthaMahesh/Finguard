"""
FinGuard Policy & Compliance Agent.
Retrieves temporally applicable regulatory guidelines, official AML standards,
and internal risk procedures matching event dates and jurisdiction.
"""

import time
from datetime import datetime, timezone
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.rag.retriever import PolicyRetriever

def policy_compliance_agent(state: InvestigationState) -> InvestigationState:
    """
    Policy & Compliance Agent:
    Retrieves regulatory guidelines, official AML standards, and internal risk procedures
    matching transaction attributes, event dates, and risk severity.
    Distinguishes official statutory directives from internal policies and research papers.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    risk = state.get("risk_assessment", {})
    role = state.get("current_user_role", "analyst")
    
    # Extract event date if available
    event_date = tx.get("event_date")
    if not event_date and tx.get("created_at"):
        try:
            ca = str(tx.get("created_at"))
            event_date = ca.split("T")[0].split(" ")[0]
        except Exception:
            event_date = None

    jurisdiction = tx.get("jurisdiction", "GLOBAL")

    # Construct targeted regulatory query
    tx_type = tx.get("type", "TRANSFER")
    amount = tx.get("amount", 0)
    query = f"{tx_type} rapid liquidation customer due diligence wire transfer threshold {amount}"
    
    # Retrieve top grounded policy citations with temporal and access filtering
    citations = PolicyRetriever.search_policies(
        query=query,
        top_k=3,
        min_relevance_score=0.40,
        event_date=event_date,
        jurisdiction=jurisdiction,
        user_role=role
    )

    # Classify retrieved evidence by provenance
    official_count = sum(1 for c in citations if c.get("source_type") == "official_regulation")
    internal_count = sum(1 for c in citations if c.get("source_type") == "sample_internal_policy")
    research_count = sum(1 for c in citations if c.get("source_type") == "research")

    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))

    requires_human_review = state.get("requires_human_review", False)
    checkpoint_reason = state.get("review_checkpoint_reason")

    if citations:
        primary_ref = citations[0]["citation_location"]
        primary_ver = citations[0].get("version", "1.0")
        summary_text = (
            f"Grounded with {len(citations)} citations ({official_count} official, "
            f"{internal_count} internal, {research_count} research). Primary: {primary_ref} (v{primary_ver})"
        )
    else:
        summary_text = "No direct policy citations met the 0.40 relevance threshold; flagging for mandatory policy triage."
        requires_human_review = True
        checkpoint_reason = checkpoint_reason or "Policy applicability could not be established; manual review required."

    timeline.append(AgentTimelineStep(
        agent="Policy & Compliance Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=summary_text,
        timestamp=datetime.now(timezone.utc).isoformat()
    ))

    return {
        **state,
        "policy_citations": citations,
        "requires_human_review": requires_human_review,
        "review_checkpoint_reason": checkpoint_reason,
        "timeline": timeline
    }
