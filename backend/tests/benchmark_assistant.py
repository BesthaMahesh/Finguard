import time
from backend.rag.embeddings import FinGuardEmbeddingFunction
from backend.rag.chroma_client import get_knowledge_collection
from backend.rag.retriever import PolicyRetriever
from backend.agents.llm_client import llm_client

def benchmark():
    queries = [
        "What are the red flags for account takeover under the indexed fraud policies?",
        "What criteria require human investigator review?",
        "What is the four-eyes principle, and when does it apply?"
    ]
    print("=== RISK ASSISTANT PIPELINE BENCHMARK ===")
    
    for i, query in enumerate(queries, 1):
        print(f"\n[Test Query {i}]: {query}")
        start_e2e = time.perf_counter()
        
        t0 = time.perf_counter()
        embedder = FinGuardEmbeddingFunction()
        t1 = time.perf_counter()
        t_embed_init = (t1 - t0) * 1000
        
        t0 = time.perf_counter()
        emb = embedder.embed_documents([query])
        t1 = time.perf_counter()
        t_embed_calc = (t1 - t0) * 1000
        
        t0 = time.perf_counter()
        citations = PolicyRetriever.search_policies(query=query, top_k=2)
        t1 = time.perf_counter()
        t_retrieval = (t1 - t0) * 1000
        
        t0 = time.perf_counter()
        context_str = "\n\n".join([f"[{c['document_id']} | {c['section']}]: {c['excerpt']}" for c in citations])
        system_prompt = (
            "You are FinGuard AI Risk Assistant, an enterprise copilot for financial crime analysts and investigators.\n"
            "Strictly ground your response in the provided compliance and policy guidelines."
        )
        user_prompt = f"User Query: {query}\n\nRetrieved Policy Evidence:\n{context_str}\n\nProvide a structured answer:"
        t1 = time.perf_counter()
        t_context = (t1 - t0) * 1000
        
        t0 = time.perf_counter()
        llm_resp = llm_client.generate_completion(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=300)
        t1 = time.perf_counter()
        t_llm = (t1 - t0) * 1000
        
        t_total = (time.perf_counter() - start_e2e) * 1000
        
        print(f"  1. Embedder Init:     {t_embed_init:.2f} ms")
        print(f"  2. Query Embedding:   {t_embed_calc:.2f} ms")
        print(f"  3. Policy Retrieval:  {t_retrieval:.2f} ms (Found {len(citations)} citations)")
        print(f"  4. Context Construct: {t_context:.2f} ms")
        print(f"  5. LLM Call:          {t_llm:.2f} ms (Provider: {llm_resp.get('provider')}, Model: {llm_resp.get('model')})")
        print(f"  --> Total E2E Latency: {t_total:.2f} ms")

if __name__ == "__main__":
    benchmark()
