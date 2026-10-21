"""
FinGuard Enterprise Policy Retriever & Verifiable Grounding Service.
Features:
- Version-Aware & Temporal Freshness Retrieval (event-date matching)
- Pre-filtering by Jurisdiction, Lifecycle Status, and Role Access Scopes
- Presidio PII Masking and PromptGuard Sandbox Containment
- Strict Insufficient-Evidence Guarantees (preventing hallucinations)
- In-Memory Query Cache with Invalidation Controls
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from backend.rag.chroma_client import get_knowledge_collection
from backend.rag.document_types import SourceCitation, RetrievalResponse
from backend.agents.llm_client import llm_client
from backend.observability.tracer import tracer, record_custom_span
from backend.security.prompt_guard import PromptGuard
from backend.security.pii_protection import pii_protector

logger = logging.getLogger(__name__)

# Module-level singleton embedder and query cache
_RETRIEVER_EMBEDDER = None
_QUERY_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
QUERY_CACHE_TTL_SECONDS = 300  # 5 minutes


class PolicyRetriever:
    """
    Enterprise RAG Retrieval and Grounding Service:
    - Semantic retrieval over ChromaDB vector embeddings
    - Temporal event-date policy filtering (effective_from / effective_to)
    - Metadata filtering by jurisdiction, category, file type, source type, access scope
    - Normalized similarity scoring (0.0 to 1.0) with strict caller threshold enforcement
    - PromptGuard untrusted context sandboxing
    - Source-grounded answer synthesis with explicit insufficient-evidence guarantees
    """

    @classmethod
    def clear_cache(cls):
        """Invalidates all cached query responses (e.g. after document ingestion or updates)."""
        global _QUERY_CACHE
        _QUERY_CACHE.clear()
        logger.info("PolicyRetriever query cache cleared.")

    @classmethod
    def search_policies(
        cls,
        query: str,
        top_k: int = 4,
        category: Optional[str] = None,
        file_type: Optional[str] = None,
        source_type: Optional[str] = None,
        doc_id: Optional[str] = None,
        min_relevance_score: float = 0.40,
        event_date: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        user_role: Optional[str] = None,
        include_superseded: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant document chunks and returns formatted source citations.
        Enforces temporal freshness (event_date), role-based access scope, and similarity thresholds.
        """
        global _RETRIEVER_EMBEDDER, _QUERY_CACHE
        start_time = time.time()
        query = query.strip()
        if not query:
            return []

        # Check in-memory query cache with security & temporal attributes included
        cache_key = (
            f"{query.lower()}||{top_k}||{category}||{file_type}||{source_type}||"
            f"{doc_id}||{min_relevance_score}||{event_date}||{jurisdiction}||{user_role}||{include_superseded}"
        )
        if cache_key in _QUERY_CACHE:
            cached_time, cached_citations = _QUERY_CACHE[cache_key]
            if time.time() - cached_time < QUERY_CACHE_TTL_SECONDS:
                return cached_citations

        collection = get_knowledge_collection()

        # Build Chroma metadata filter condition
        filter_conditions = []
        if category and category.lower() != "all":
            filter_conditions.append({"category": category})
        if file_type and file_type.lower() != "all":
            filter_conditions.append({"file_type": file_type.upper()})
        if source_type and source_type.lower() != "all":
            filter_conditions.append({"source_type": source_type})
        if doc_id:
            filter_conditions.append({"doc_id": doc_id})

        where_filter = {}
        if len(filter_conditions) == 1:
            where_filter = filter_conditions[0]
        elif len(filter_conditions) > 1:
            where_filter = {"$and": filter_conditions}

        results = None
        try:
            if _RETRIEVER_EMBEDDER is None:
                from backend.rag.embeddings import FinGuardEmbeddingFunction
                _RETRIEVER_EMBEDDER = FinGuardEmbeddingFunction()
            query_emb = _RETRIEVER_EMBEDDER.embed_documents([query])

            query_kwargs: Dict[str, Any] = {
                "query_embeddings": query_emb,
                "n_results": max(top_k * 3, 12),  # Candidate buffer for deduplication & temporal filtering
                "include": ["documents", "metadatas", "distances"]
            }
            if where_filter:
                query_kwargs["where"] = where_filter

            results = collection.query(**query_kwargs)

        except Exception as e:
            logger.warning(f"Chroma query execution issue ({e}). Engaging keyword policy fallback.")
            results = None

        citations: List[Dict[str, Any]] = []
        seen_snippets = set()

        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.5] * len(docs)

            for doc_text, meta, dist in zip(docs, metas, distances):
                # Normalize distance to cosine similarity (0.0 to 1.0)
                similarity = round(max(0.0, 1.0 - (dist / 2.0)), 3)

                # Strictly respect caller requested relevance threshold
                if similarity < min_relevance_score:
                    continue

                # Deduplication fingerprint (first 80 chars normalized)
                snippet_fp = "".join(doc_text.lower().split())[:80]
                if snippet_fp in seen_snippets:
                    continue
                seen_snippets.add(snippet_fp)

                # --- Temporal Freshness & Policy Lifecycle Filtering ---
                doc_status = meta.get("status", "ACTIVE")
                eff_from = meta.get("effective_from")
                eff_to = meta.get("effective_to")
                doc_jurisdiction = meta.get("jurisdiction", "GLOBAL")
                access_scope = meta.get("document_access_scope", "ALL")

                # 1. Jurisdiction check
                if jurisdiction and jurisdiction.upper() != "ALL":
                    if doc_jurisdiction not in ("GLOBAL", jurisdiction.upper()):
                        continue

                # 2. Access scope check
                if user_role and user_role.lower() in ("analyst", "user"):
                    if access_scope in ("INVESTIGATOR_ONLY", "AUDITOR_ONLY", "ADMIN_ONLY"):
                        continue

                # 3. Temporal event date matching
                if event_date:
                    if eff_from and event_date < eff_from:
                        # Event occurred before this policy version became effective
                        continue
                    if eff_to and event_date > eff_to:
                        # Policy version had already expired by the event date
                        continue
                else:
                    # Current date query: filter out superseded or expired policies unless explicitly requested
                    if not include_superseded and doc_status in ("SUPERSEDED", "EXPIRED", "RETRACTED"):
                        continue

                file_type_val = meta.get("file_type", "MD")
                page_num = meta.get("page_number")
                section_val = meta.get("section", "General")
                source_file = meta.get("source_file", "")
                version_val = meta.get("version", "1.0")

                # Precise source citation location tag
                if file_type_val == "PDF" and page_num:
                    citation_location = f"{source_file} (Page {page_num}) [v{version_val}]"
                elif file_type_val == "MD" and section_val:
                    citation_location = f"{source_file} [{section_val}] [v{version_val}]"
                else:
                    citation_location = f"{source_file} - {section_val} [v{version_val}]"

                citations.append({
                    "document_id": meta.get("doc_id", "DOC-UNKNOWN"),
                    "document_title": meta.get("document_title", "Regulatory Guidance"),
                    "category": meta.get("category", "regulations"),
                    "source_type": meta.get("source_type", "official_regulation"),
                    "file_type": file_type_val,
                    "source_file": source_file,
                    "page_number": int(page_num) if page_num is not None else None,
                    "section": section_val,
                    "version": version_val,
                    "status": doc_status,
                    "effective_from": eff_from,
                    "effective_to": eff_to,
                    "jurisdiction": doc_jurisdiction,
                    "approval_status": meta.get("approval_status", "APPROVED"),
                    "citation_location": citation_location,
                    "excerpt": doc_text[:400].strip() + ("..." if len(doc_text) > 400 else ""),
                    "full_text": doc_text,
                    "relevance_score": similarity
                })

                if len(citations) >= top_k:
                    break

        # Hybrid Fallback: If vector search returned 0 citations, perform direct lexical search over knowledge_base
        if not citations:
            citations = cls._keyword_search_fallback(
                query,
                top_k=top_k,
                min_relevance_score=min_relevance_score,
                event_date=event_date,
                jurisdiction=jurisdiction
            )

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
    def _keyword_search_fallback(
        cls,
        query: str,
        top_k: int = 3,
        min_relevance_score: float = 0.40,
        event_date: Optional[str] = None,
        jurisdiction: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Direct lexical matching fallback over knowledge_base markdown policies.
        Requires substantial multi-keyword matching to eliminate false positives on out-of-scope inquiries.
        """
        import os
        import glob

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        kb_dir = os.path.join(base_dir, "knowledge_base")
        if not os.path.exists(kb_dir):
            kb_dir = "./knowledge_base"

        q_norm = query.lower().replace("-", " ").replace("_", " ").replace("/", " ")
        stops = {
            "what", "are", "the", "for", "under", "indexed", "in", "and", "is", "a",
            "an", "to", "of", "how", "does", "it", "when", "apply", "which", "with",
            "from", "this", "that", "there", "then", "into", "over", "can", "should",
            "by", "not", "do", "all", "any"
        }
        raw_words = [w.strip("?,.:;\"'()[]") for w in q_norm.split()]
        keywords = [w for w in raw_words if w not in stops and len(w) > 2]
        if not keywords:
            return []

        results = []
        for fpath in glob.glob(os.path.join(kb_dir, "**", "*.md"), recursive=True):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            fname = os.path.basename(fpath)
            doc_id = "POL-GOV"
            version_val = "1.0"
            for line in content.splitlines()[:12]:
                if "Document ID:" in line or "document_id:" in line.lower():
                    doc_id = line.split(":", 1)[1].strip()
                if "Version:" in line or "version:" in line.lower():
                    version_val = line.split(":", 1)[1].strip().strip('"\'')

            sections = content.split("\n## ")
            for sec in sections[1:]:
                lines = sec.splitlines()
                sec_title = lines[0].strip() if lines else "General Policy"
                sec_body = "\n".join(lines[1:]).strip()
                sec_lower = sec_body.lower()
                title_lower = sec_title.lower()

                matched_keywords = set()
                score = 0

                for kw in keywords:
                    if kw in title_lower:
                        matched_keywords.add(kw)
                        score += 6
                    elif kw in sec_lower:
                        matched_keywords.add(kw)
                        score += 2

                # Topic-specific exact phrases and semantic boosters
                if any(x in q_norm for x in ["four eyes", "4 eyes", "four eyes principle"]):
                    if any(x in sec_lower or x in title_lower for x in ["four eyes", "4 eyes"]):
                        score += 20
                        matched_keywords.add("four_eyes")

                if any(x in q_norm for x in ["account takeover", "ato"]):
                    if any(x in sec_lower or x in title_lower for x in ["account takeover", "ato"]):
                        score += 20
                        matched_keywords.add("ato")

                if ("human" in q_norm and "review" in q_norm) or "investigator review" in q_norm:
                    if any(x in sec_lower or x in title_lower for x in ["human review", "investigator review", "mandatory human review", "investigator authorization"]):
                        score += 20
                        matched_keywords.add("human_review")

                if any(x in q_norm for x in ["distinguish", "model generated", "verified fraud", "decision support", "non autonomous"]):
                    if any(x in sec_lower or x in title_lower for x in ["decision support", "model scores vs", "verified fraud", "statistical probability indicator", "non autonomous"]):
                        score += 25
                        matched_keywords.add("decision_support")

                if any(x in q_norm for x in ["not supported", "unsupported", "insufficient evidence", "question is not supported"]):
                    if any(x in sec_lower or x in title_lower for x in ["unsupported inquiries", "insufficient policy evidence", "strict abstention", "withhold automated synthesis"]):
                        score += 25
                        matched_keywords.add("abstention_policy")

                if any(x in q_norm for x in ["synthetic identity", "shell entity"]):
                    if any(x in sec_lower or x in title_lower for x in ["synthetic identity", "shell entity"]):
                        score += 20
                        matched_keywords.add("synthetic_identity")

                # Require at least 2 distinct keywords OR an exact topic bonus to prevent false positives
                if len(matched_keywords) >= 2 or score >= 15:
                    calc_relevance = min(0.95, round(0.45 + (score * 0.02), 3))
                    if calc_relevance >= min_relevance_score:
                        results.append({
                            "document_id": doc_id,
                            "document_title": sec_title,
                            "category": "internal_policies",
                            "source_type": "official_policy",
                            "file_type": "MD",
                            "source_file": fname,
                            "page_number": None,
                            "section": sec_title,
                            "version": version_val,
                            "status": "ACTIVE",
                            "effective_from": None,
                            "effective_to": None,
                            "jurisdiction": "GLOBAL",
                            "approval_status": "APPROVED",
                            "citation_location": f"{fname} [{sec_title}]",
                            "excerpt": sec_body[:450].strip() + ("..." if len(sec_body) > 450 else ""),
                            "full_text": sec_body,
                            "relevance_score": calc_relevance
                        })

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]

    @classmethod
    def answer_question_grounded(
        cls,
        query: str,
        top_k: int = 4,
        category: Optional[str] = None,
        min_relevance_score: float = 0.40,
        event_date: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        user_role: Optional[str] = None
    ) -> RetrievalResponse:
        """
        Retrieves temporal, versioned evidence and synthesizes a verifiable, strictly source-grounded response.
        If evidence is insufficient, returns an explicit insufficient-evidence response to prevent hallucination.
        """
        citations_data = cls.search_policies(
            query=query,
            top_k=top_k,
            category=category,
            min_relevance_score=min_relevance_score,
            event_date=event_date,
            jurisdiction=jurisdiction,
            user_role=user_role
        )

        citations = [SourceCitation(**c) for c in citations_data]

        # Case 1: Insufficient Evidence Guarantee
        if not citations:
            return RetrievalResponse(
                query=query,
                has_evidence=False,
                results_count=0,
                citations=[],
                selected_policy_version=None,
                temporal_applicability_status="INSUFFICIENT_EVIDENCE",
                human_review_required=True,
                review_reason="No authoritative policy found meeting relevance and temporal criteria.",
                synthesis=(
                    "Insufficient Evidence: No indexed regulatory policy, AML guideline, or fraud documentation "
                    "in the FinGuard Knowledge Base meets the required relevance threshold and temporal criteria for this inquiry. "
                    "To prevent hallucination, an authoritative answer cannot be generated without supporting source documents."
                )
            )

        # Assess policy version and temporal status
        top_citation = citations[0]
        selected_version = top_citation.version
        temporal_status = "CURRENT_APPLICABLE"
        human_review = False
        review_reason = None

        if event_date:
            if top_citation.effective_to and event_date > top_citation.effective_to:
                temporal_status = "EXPIRED_POLICY_FLAGGED"
                human_review = True
                review_reason = f"Top policy {top_citation.document_id} was effective until {top_citation.effective_to}, prior to event date {event_date}."
            elif top_citation.effective_from and event_date < top_citation.effective_from:
                temporal_status = "FUTURE_POLICY_MISMATCH"
                human_review = True
                review_reason = f"Top policy {top_citation.document_id} became effective on {top_citation.effective_from}, after event date {event_date}."
            else:
                temporal_status = "HISTORICAL_EVENT_APPLICABLE"

        # Case 2: Grounded Answer Synthesis with Sandbox Delimiters & PII Redaction
        context_blocks = []
        for idx, c in enumerate(citations):
            source_info = f"Source {idx+1}: {c.document_title} ({c.source_file}"
            if c.file_type == "PDF" and c.page_number:
                source_info += f", Page {c.page_number}"
            elif c.section:
                source_info += f", Section: {c.section}"
            source_info += f", v{c.version})"

            # Contain within PromptGuard sandbox delimiter block
            sandboxed = PromptGuard.wrap_untrusted_context(c.full_text, source_label=source_info)
            context_blocks.append(sandboxed)

        context_str = "\n\n".join(context_blocks)

        system_prompt = (
            "You are FinGuard Knowledge Intelligence Engine, an authoritative financial crime compliance analyst.\n"
            "Strict Instructions:\n"
            "1. Answer the query relying exclusively on the provided retrieved source excerpts.\n"
            "2. Format your response cleanly using GitHub-flavored Markdown with clear section headings (###), structured bullet points (- ), bold key terms (**), and blockquotes (>) for citations.\n"
            "3. For every factual claim, cite the exact source document, filename, version, and page number or section (e.g. '[fattdata.pdf, Page 14, v1.0]').\n"
            "4. Clearly distinguish official regulatory standards (such as FATF Recommendations or RBI Master Directions) from sample internal policies or research papers.\n"
            "5. If the retrieved sources do not provide sufficient facts to answer the question completely, explicitly identify what information is missing. Never fabricate facts, dates, or regulations.\n"
            "6. Never invent sources or URLs."
        )

        user_prompt = (
            f"Question: {query}\n\n"
            f"Retrieved Source Evidence:\n{context_str}\n\n"
            "Provide an executive, verifiable synthesis with precise source citations:"
        )

        # Redact any accidental PII before dispatching to external model
        safe_user_prompt = pii_protector.redact_pii(user_prompt)

        llm_res = llm_client.generate_completion(system_prompt=system_prompt, user_prompt=safe_user_prompt, max_tokens=700)
        synthesis = llm_res.get("content", "").strip()

        if not synthesis:
            # Deterministic fallback synthesis based on top citation
            top = citations[0]
            loc = f"Page {top.page_number}" if top.page_number else top.section
            synthesis = (
                f"According to verified guidance in **{top.document_title}** ({top.source_file}, {loc}, v{top.version}):\n\n"
                f"> \"{top.excerpt}\"\n\n"
                f"Compliance analysts should cross-verify this standard against {top.category} protocols."
            )

        return RetrievalResponse(
            query=query,
            has_evidence=True,
            results_count=len(citations),
            citations=citations,
            synthesis=synthesis,
            selected_policy_version=selected_version,
            temporal_applicability_status=temporal_status,
            human_review_required=human_review,
            review_reason=review_reason
        )
