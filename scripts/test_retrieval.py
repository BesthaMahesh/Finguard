import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag.retriever import PolicyRetriever

TEST_QUESTIONS = [
    {
        "id": "Q1",
        "question": "What are the FATF recommendations regarding customer due diligence and wire transfers?",
        "expected_docs": ["fattdata.pdf", "anti_money_laundering_guide.md"]
    },
    {
        "id": "Q2",
        "question": "What are the RBI Master Direction requirements on Know Your Customer and beneficial ownership verification?",
        "expected_docs": ["frauddata.pdf", "rbi_kyc_aml_master_direction.md"]
    },
    {
        "id": "Q3",
        "question": "What is the FATF guidance on beneficial ownership transparency of legal arrangements?",
        "expected_docs": ["ftfe2.pdf"]
    },
    {
        "id": "Q4",
        "question": "What is the procedure for investigating rapid account liquidation and high-value wire transfers?",
        "expected_docs": ["sample_transaction_fraud_investigation_procedure.md", "fraud_typologies_playbook.md"]
    },
    {
        "id": "Q5",
        "question": "What are the rules and regulations for Martian cryptocurrency interplanetary asteroid mining?",
        "expected_docs": []  # Out of domain query to test insufficient evidence
    }
]

def main():
    print("\n" + "=" * 70)
    print("FIN GUARD RAG RETRIEVAL & CITATION VERIFICATION")
    print("=" * 70)

    for item in TEST_QUESTIONS:
        qid = item["id"]
        q = item["question"]
        print(f"\n[{qid}] Query: {q}")
        
        resp = PolicyRetriever.answer_question_grounded(query=q, top_k=3, min_relevance_score=0.45)
        print(f"Has Evidence: {resp.has_evidence} (Results count: {resp.results_count})")
        
        if resp.citations:
            print("Retrieved Citations:")
            for idx, c in enumerate(resp.citations):
                page_str = f"Page {c.page_number}" if c.page_number else c.section
                print(f"  [{idx+1}] Document: {c.document_title} | File: {c.source_file} ({page_str})")
                print(f"      Relevance: {c.relevance_score:.3f} | Type: {c.source_type} | Category: {c.category}")
                print(f"      Excerpt: {c.excerpt[:130]}...")
        else:
            print("  No citations returned (Insufficient Evidence triggered as required).")

        print("\nSynthesis Response:")
        print(resp.synthesis[:350] + ("..." if len(resp.synthesis or "") > 350 else ""))
        print("-" * 70)

if __name__ == "__main__":
    main()
