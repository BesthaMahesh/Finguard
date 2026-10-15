import logging
from typing import List, Dict, Any, Optional
from backend.rag.ingestion_pipeline import KnowledgeIngestionPipeline

logger = logging.getLogger(__name__)

def ingest_all_knowledge_docs(docs_dir: str = "./knowledge_base", force_reindex: bool = False) -> int:
    """
    Unified entry point for knowledge ingestion:
    Supports incremental hashing, PDF page extraction, Markdown front matter,
    safe de-duplication, and manifest tracking.
    """
    pipeline = KnowledgeIngestionPipeline(target_dirs=[docs_dir, "./backend/rag/knowledge_base"])
    res = pipeline.run_incremental_ingestion(force_reindex=force_reindex)
    return res.get("total_chunks_indexed", 0)
