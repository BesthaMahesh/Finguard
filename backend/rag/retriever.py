import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from backend.rag.chroma_client import get_knowledge_collection
from backend.rag.document_types import SourceCitation, RetrievalResponse
from backend.agents.llm_client import llm_client
from backend.observability.tracer import tracer, record_custom_span

logger = logging.getLogger(__name__)

# Module-level singleton embedder and query cache
_RETRIEVER_EMBEDDER = None
_QUERY_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
QUERY_CACHE_TTL_SECONDS = 300  # 5 minutes

class PolicyRetriever:
    """
    Enterprise RAG Retrieval and Grounding Service:
    - Semantic retrieval over ChromaDB vector embeddings
    - Metadata filtering by category, file type, source type, or document ID
    - Normalized similarity scoring (0.0 to 1.0) and threshold filtering
    - Deduplication of redundant passages
    - Strict provenance preservation (PDF page numbers, Markdown headings, source types)
    - Source-grounded answer synthesis with explicit insufficient-evidence guarantees
    """

    @classmethod
    def search_policies(
        cls,
        query: str,
        top_k: int = 4,
        category: Optional[str] = None,
        file_type: Optional[str] = None,
        source_type: Optional[str] = None,
        doc_id: Optional[str] = None,
        min_relevance_score: float = 0.40
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant document chunks and returns formatted source citations.
        """
        global _RETRIEVER_EMBEDDER, _QUERY_CACHE
        start_time = time.time()
        query = query.strip()
        if not query:
            return []

        # Check in-memory query cache
        cache_key = f"{query.lower()}||{top_k}||{category}||{file_type}||{source_type}||{doc_id}||{min_relevance_score}"
        if cache_key in _QUERY_CACHE:
            cached_time, cached_citations = _QUERY_CACHE[cache_key]
            if time.time() - cached_time < QUERY_CACHE_TTL_SECONDS:
                return cached_citations

        collection = get_knowledge_collection()

        # Build Chroma metadata filter condition
        where_filter = {}
        filter_conditions = []
        if category and category.lower() != "all":
            filter_conditions.append({"category": category})
        if file_type and file_type.lower() != "all":
            filter_conditions.append({"file_type": file_type.upper()})
        if source_type and source_type.lower() != "all":
            filter_conditions.append({"source_type": source_type})
        if doc_id:
            filter_conditions.append({"doc_id": doc_id})

        if len(filter_conditions) == 1:
            where_filter = filter_conditions[0]
        elif len(filter_conditions) > 1:
            where_filter = {"$and": filter_conditions}

        try:
            if _RETRIEVER_EMBEDDER is None:
                from backend.rag.embeddings import FinGuardEmbeddingFunction
                _RETRIEVER_EMBEDDER = FinGuardEmbeddingFunction()
            query_emb = _RETRIEVER_EMBEDDER.embed_documents([query])

            query_kwargs: Dict[str, Any] = {
                "query_embeddings": query_emb,
                "n_results": max(top_k * 2, 8),  # Fetch candidate buffer for deduplication & thresholding
                "include": ["documents", "metadatas", "distances"]
            }
            if where_filter:
                query_kwargs["where"] = where_filter

            results = collection.query(**query_kwargs)

        except Exception as e:
            logger.error(f"Chroma query execution error: {e}")
            return []

        if not results or not results.get("documents") or len(results["documents"]) == 0:
            return []

        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [0.5] * len(docs)

        citations: List[Dict[str, Any]] = []
        seen_snippets = set()

        for doc_text, meta, dist in zip(docs, metas, distances):
            # Normalize distance to cosine similarity (0.0 to 1.0)
            similarity = round(max(0.0, 1.0 - (dist / 2.0)), 3)

            # Apply relevance threshold
            if similarity < min_relevance_score:
                continue

            # Deduplication fingerprint (first 80 chars normalized)
            snippet_fp = "".join(doc_text.lower().split())[:80]
            if snippet_fp in seen_snippets:
                continue
            seen_snippets.add(snippet_fp)

            file_type_val = meta.get("file_type", "MD")
            page_num = meta.get("page_number")
            section_val = meta.get("section", "General")
            source_file = meta.get("source_file", "")

            # Precise source citation tag
            if file_type_val == "PDF" and page_num:
                citation_location = f"{source_file} (Page {page_num})"
            elif file_type_val == "MD" and section_val:
                citation_location = f"{source_file} [{section_val}]"
            else:
                citation_location = f"{source_file} - {section_val}"

            citations.append({
                "document_id": meta.get("doc_id", "DOC-UNKNOWN"),
                "document_title": meta.get("document_title", "Regulatory Guidance"),
                "category": meta.get("category", "regulations"),
                "source_type": meta.get("source_type", "official_regulation"),
                "file_type": file_type_val,
                "source_file": source_file,
                "page_number": int(page_num) if page_num is not None else None,
                "section": section_val,
                "citation_location": citation_location,
                "excerpt": doc_text[:400].strip() + ("..." if len(doc_text) > 400 else ""),
                "full_text": doc_text,
                "relevance_score": similarity
            })

            if len(citations) >= top_k:
                break

        duration = (time.time() - start_time) * 1000.0
        record_custom_span(
            name="rag_retrieval_query",
            duration_ms=duration,
            attributes={"query": query[:60], "results_count": len(citations), "top_k": top_k}
        )
        # Populate cache
        _QUERY_CACHE[cache_key] = (time.time(), citations)
        return citations

    @classmethod
    def answer_question_grounded(
        cls,
        query: str,
        top_k: int = 4,
        category: Optional[str] = None,
        min_relevance_score: float = 0.40
    ) -> RetrievalResponse:
        """
        Retrieves evidence and synthesizes a verifiable, strictly source-grounded response.
        If evidence is insufficient, returns an explicit insufficient-evidence response.
        """
        citations_data = cls.search_policies(
            query=query,
            top_k=top_k,
            category=category,
            min_relevance_score=min_relevance_score
        )

        citations = [SourceCitation(**c) for c in citations_data]

        # Case 1: Insufficient Evidence
        if not citations:
            return RetrievalResponse(
                query=query,
                has_evidence=False,
                results_count=0,
                citations=[],
                synthesis=(
                    "Insufficient Evidence: No indexed regulatory policy, AML guideline, or fraud documentation "
                    "in the FinGuard Knowledge Base meets the required relevance threshold for this inquiry. "
                    "To prevent hallucination, an authoritative answer cannot be generated without supporting source documents."
                )
            )

        # Case 2: Grounded Answer Synthesis
        context_blocks = []
        for idx, c in enumerate(citations):
            source_info = f"Source {idx+1}: {c.document_title} ({c.source_file}"
            if c.file_type == "PDF" and c.page_number:
                source_info += f", Page {c.page_number}"
            elif c.section:
                source_info += f", Section: {c.section}"
            source_info += f") [Relevance: {c.relevance_score:.2f}, Type: {c.source_type}]"
            
            context_blocks.append(f"--- {source_info} ---\n{c.full_text}")

        context_str = "\n\n".join(context_blocks)

        system_prompt = (
            "You are FinGuard Knowledge Intelligence Engine, an authoritative financial crime compliance analyst.\n"
            "Strict Instructions:\n"
            "1. Answer the query relying exclusively on the provided retrieved source excerpts.\n"
            "2. Format your response cleanly using GitHub-flavored Markdown with clear section headings (###), structured bullet points (- ), bold key terms (**), and blockquotes (>) for citations.\n"
            "3. For every factual claim, cite the exact source document, filename, and page number or section (e.g. '[fattdata.pdf, Page 14]' or '[anti_money_laundering_guide.md, Section 2]').\n"
            "4. Clearly distinguish official regulatory standards (such as FATF Recommendations or RBI Master Directions) from sample internal policies or research papers.\n"
            "5. If the retrieved sources do not provide sufficient facts to answer the question completely, explicitly identify what information is missing. Never fabricate facts, dates, or regulations.\n"
            "6. Never invent sources or URLs."
        )

        user_prompt = (
            f"Question: {query}\n\n"
            f"Retrieved Source Evidence:\n{context_str}\n\n"
            "Provide an executive, verifiable synthesis with precise source citations:"
        )

        llm_res = llm_client.generate_completion(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=700)
        synthesis = llm_res.get("content", "").strip()

        if not synthesis:
            # Deterministic fallback synthesis based on top citation
            top = citations[0]
            loc = f"Page {top.page_number}" if top.page_number else top.section
            synthesis = (
                f"According to verified guidance in **{top.document_title}** ({top.source_file}, {loc}):\n\n"
                f"> \"{top.excerpt}\"\n\n"
                f"Compliance analysts should cross-verify this standard against {top.category} protocols."
            )

        return RetrievalResponse(
            query=query,
            has_evidence=True,
            results_count=len(citations),
            citations=citations,
            synthesis=synthesis
        )
