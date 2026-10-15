import os
import sys
import argparse
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag.ingestion_pipeline import KnowledgeIngestionPipeline
from backend.rag.manifest import ManifestManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ingest_knowledge")

def main():
    parser = argparse.ArgumentParser(description="FinGuard Enterprise Knowledge Base Ingestion CLI")
    parser.add_argument("--dir", default="./knowledge_base", help="Target root directory to scan for documents")
    parser.add_argument("--reindex-all", action="store_true", help="Force re-indexing of all documents, ignoring hash cache")
    parser.add_argument("--doc-id", default=None, help="Re-index specific document by doc_id")
    parser.add_argument("--status", action="store_true", help="Print current knowledge base manifest statistics")
    args = parser.parse_args()

    if args.status:
        mgr = ManifestManager()
        stats = mgr.get_summary_statistics()
        print("\n=== FinGuard Knowledge Base Manifest Status ===")
        print(f"Total Discovered Documents: {stats['total_discovered']}")
        print(f"Total Successfully Indexed: {stats['total_indexed']}")
        print(f"Total Skipped (Unchanged):   {stats['total_skipped']}")
        print(f"Total Failed:               {stats['total_failed']}")
        print(f"Total Indexed Chunks:       {stats['total_chunks']}")
        print(f"Categories:                 {', '.join(stats['categories'])}")
        print(f"File Formats:               {', '.join(stats['file_types'])}")
        print(f"Last Ingestion Run:         {stats['last_updated']}\n")
        return

    pipeline = KnowledgeIngestionPipeline(target_dirs=[args.dir, "./backend/rag/knowledge_base"])

    if args.doc_id:
        logger.info(f"Re-indexing individual document: {args.doc_id}")
        res = pipeline.reindex_document(args.doc_id)
        logger.info(f"Document re-indexed: {res}")
        return

    logger.info(f"Starting FinGuard knowledge ingestion on '{args.dir}' (force_reindex={args.reindex_all})...")
    results = pipeline.run_incremental_ingestion(force_reindex=args.reindex_all)

    print("\n" + "=" * 50)
    print("FIN GUARD KNOWLEDGE INGESTION REPORT")
    print("=" * 50)
    print(f"Discovered:    {results['discovered']} documents")
    print(f"Processed:     {results['processed']} documents")
    print(f"Skipped:       {results['skipped']} documents")
    print(f"Failed:        {results['failed']} documents")
    print(f"Chunks Added:  {results['total_chunks_indexed']} vector chunks")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
