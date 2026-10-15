import time
from datetime import datetime
from backend.agents.agent_state import InvestigationState, AgentTimelineStep
from backend.db.session import SessionLocal
from backend.db.models import Transaction
from backend.rag.retriever import PolicyRetriever

def investigation_agent(state: InvestigationState) -> InvestigationState:
    """
    Investigation Agent:
    Examines transaction patterns, origin entity history, counterparty relationships,
    and retrieves relevant fraud pattern playbooks and investigation procedures.
    Keeps factual forensic evidence separate from ML model predictions.
    """
    start_time = time.time()
    tx = state.get("validated_transaction", {})
    name_orig = tx.get("nameOrig", "")
    name_dest = tx.get("nameDest", "")

    evidence = {
        "origin_entity": name_orig,
        "destination_entity": name_dest,
        "dest_is_merchant": name_dest.startswith("M"),
        "historical_origin_transactions": 0,
        "anomalies_detected": [],
        "retrieved_fraud_patterns": []
    }

    # Query database for entity history
    if name_orig:
        db = SessionLocal()
        try:
            prior_txs = db.query(Transaction).filter_by(name_orig=name_orig).count()
            evidence["historical_origin_transactions"] = prior_txs
        except Exception:
            pass
        finally:
            db.close()

    # Forensic pattern checks
    old_orig = tx.get("oldbalanceOrg", 0)
    new_orig = tx.get("newbalanceOrig", 0)
    amount = tx.get("amount", 0)

    if old_orig > 0 and new_orig == 0:
        evidence["anomalies_detected"].append("Complete Origin Liquidation Pattern")

    expected_new = old_orig - amount
    if abs(expected_new - new_orig) > 1.0:
        evidence["anomalies_detected"].append("Origin Ledger Accounting Variance")

    # Retrieve matching fraud pattern procedures from Knowledge Base
    pattern_query = f"{tx.get('type', 'TRANSFER')} rapid liquidation account takeover mule activity"
    retrieved_patterns = PolicyRetriever.search_policies(
        query=pattern_query,
        top_k=2,
        category="fraud_patterns",
        min_relevance_score=0.40
    )

    evidence["retrieved_fraud_patterns"] = [
        {
            "pattern_doc": p["document_title"],
            "section": p["section"],
            "source_location": p["citation_location"],
            "excerpt": p["excerpt"][:200]
        }
        for p in retrieved_patterns
    ]

    duration = (time.time() - start_time) * 1000.0
    timeline = list(state.get("timeline", []))
    timeline.append(AgentTimelineStep(
        agent="Investigation Agent",
        status="COMPLETED",
        duration_ms=round(duration, 2),
        output_summary=(
            f"Detected {len(evidence['anomalies_detected'])} pattern anomalies for {name_orig} -> {name_dest}. "
            f"Grounded with {len(evidence['retrieved_fraud_patterns'])} fraud typology patterns."
        ),
        timestamp=datetime.utcnow().isoformat()
    ))

    return {
        **state,
        "investigation_evidence": evidence,
        "timeline": timeline
    }
