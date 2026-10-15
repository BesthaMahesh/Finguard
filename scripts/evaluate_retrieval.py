import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag.retriever import PolicyRetriever

EVALUATION_DATASET = [
    {
        "query": "What are the FATF recommendations regarding customer due diligence and wire transfers?",
        "expected_sources": ["fattdata.pdf", "rbi_kyc_aml_master_direction.md", "anti_money_laundering_guide.md"],
        "expected_categories": ["aml_kyc", "regulations"],
        "is_answerable": True
    },
    {
        "query": "What are the RBI Master Direction requirements on Know Your Customer and identification of beneficial ownership?",
        "expected_sources": ["frauddata.pdf", "rbi_kyc_aml_master_direction.md"],
        "expected_categories": ["regulations"],
        "is_answerable": True
    },
    {
        "query": "What is the FATF guidance on beneficial ownership and transparency of legal arrangements?",
        "expected_sources": ["ftfe2.pdf"],
        "expected_categories": ["research"],
        "is_answerable": True
    },
    {
        "query": "What is the procedure for investigating rapid account liquidation and high-value wire transfers?",
        "expected_sources": ["sample_transaction_fraud_investigation_procedure.md", "anti_money_laundering_guide.md", "fraud_typologies_playbook.md"],
        "expected_categories": ["fraud_patterns", "internal_policies"],
        "is_answerable": True
    },
    {
        "query": "What are the simulation mechanics and schema attributes of the PaySim synthetic dataset?",
        "expected_sources": ["paysim_financial_dataset_guide.md"],
        "expected_categories": ["dataset_documentation"],
        "is_answerable": True
    },
    {
        "query": "What are the intergalactic trade tariffs on lunar asteroid mining colonies in Alpha Centauri?",
        "expected_sources": [],
        "expected_categories": [],
        "is_answerable": False
    }
]

def run_retrieval_evaluation():
    print("=" * 70)
    print("FIN GUARD RAG BENCHMARK EVALUATION (Recall@K & MRR)")
    print("=" * 70)

    top_k = 3
    recalls = []
    reciprocal_ranks = []
    insufficient_evidence_checks = []

    for idx, item in enumerate(EVALUATION_DATASET):
        q = item["query"]
        expected = item["expected_sources"]
        is_answerable = item["is_answerable"]

        citations = PolicyRetriever.search_policies(query=q, top_k=top_k, min_relevance_score=0.45)
        retrieved_sources = [c["source_file"] for c in citations]

        if is_answerable:
            # Hit count
            hits = [s for s in retrieved_sources if s in expected]
            hit_k = 1.0 if hits else 0.0
            recalls.append(hit_k)

            # Reciprocal Rank (MRR)
            rr = 0.0
            for rank_idx, s in enumerate(retrieved_sources):
                if s in expected:
                    rr = 1.0 / (rank_idx + 1)
                    break
            reciprocal_ranks.append(rr)

            print(f"\n[Test {idx+1}] Query: {q[:60]}...")
            print(f"  Expected: {expected}")
            print(f"  Retrieved: {retrieved_sources}")
            print(f"  Recall@{top_k}: {hit_k:.2f} | Reciprocal Rank: {rr:.3f}")
        else:
            # Out of domain query: must return 0 citations
            passed = len(citations) == 0
            insufficient_evidence_checks.append(passed)
            print(f"\n[Test {idx+1}] Out-of-Domain Query: {q[:60]}...")
            print(f"  Citations Returned: {len(citations)} (Correct Insufficient Evidence: {passed})")

    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    ood_accuracy = sum(1 for p in insufficient_evidence_checks if p) / len(insufficient_evidence_checks) if insufficient_evidence_checks else 0.0

    print("\n" + "=" * 70)
    print("FINAL EVALUATION METRICS REPORT")
    print("=" * 70)
    print(f"Total Test Cases Evaluated:       {len(EVALUATION_DATASET)}")
    print(f"Answerable Queries Evaluated:    {len(recalls)}")
    print(f"Recall@{top_k}:                         {avg_recall * 100:.1f}%")
    print(f"Mean Reciprocal Rank (MRR):      {mrr:.3f}")
    print(f"Hallucination Guardrail (OOD):   {ood_accuracy * 100:.1f}%")
    print("=" * 70 + "\n")

    return {
        "recall_at_k": avg_recall,
        "mrr": mrr,
        "ood_accuracy": ood_accuracy
    }

if __name__ == "__main__":
    run_retrieval_evaluation()
