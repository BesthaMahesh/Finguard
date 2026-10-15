import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from backend.rag.document_types import DocumentMetadataModel

logger = logging.getLogger(__name__)

MANIFEST_DIR = "./knowledge_base/manifests"
MANIFEST_FILE = os.path.join(MANIFEST_DIR, "manifest.json")

class ManifestManager:
    """
    Tracks document-level ingestion manifests, content hashes, and processing states.
    Ensures safe, idempotent, traceable RAG operations.
    """

    def __init__(self, manifest_path: str = MANIFEST_FILE):
        self.manifest_path = manifest_path
        self._manifest_data: Dict[str, Any] = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading manifest at {self.manifest_path}: {e}. Creating new manifest.")
        return {
            "version": "1.0",
            "last_updated": None,
            "total_documents": 0,
            "total_chunks": 0,
            "documents": {}
        }

    def save(self):
        os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
        self._manifest_data["last_updated"] = datetime.utcnow().isoformat()
        self._manifest_data["total_documents"] = len(self._manifest_data["documents"])
        self._manifest_data["total_chunks"] = sum(
            d.get("chunk_count", 0) for d in self._manifest_data["documents"].values() if d.get("status") == "INDEXED"
        )
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self._manifest_data, f, indent=2)

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self._manifest_data["documents"].get(doc_id)

    def get_all_documents(self) -> Dict[str, Any]:
        return self._manifest_data["documents"]

    def is_document_unchanged(self, doc_id: str, current_content_hash: str) -> bool:
        """
        Returns True if the document has already been successfully indexed with the identical hash.
        """
        existing = self.get_document(doc_id)
        if not existing:
            return False
        return existing.get("content_hash") == current_content_hash and existing.get("status") == "INDEXED"

    def record_document_status(
        self,
        doc_id: str,
        metadata: DocumentMetadataModel,
        status: str = "INDEXED",
        error_message: Optional[str] = None
    ):
        doc_dict = metadata.model_dump()
        doc_dict["status"] = status
        doc_dict["error_message"] = error_message
        doc_dict["ingested_at"] = datetime.utcnow().isoformat()
        self._manifest_data["documents"][doc_id] = doc_dict
        self.save()

    def remove_document(self, doc_id: str) -> bool:
        if doc_id in self._manifest_data["documents"]:
            del self._manifest_data["documents"][doc_id]
            self.save()
            return True
        return False

    def get_summary_statistics(self) -> Dict[str, Any]:
        docs = list(self._manifest_data["documents"].values())
        return {
            "total_discovered": len(docs),
            "total_indexed": sum(1 for d in docs if d.get("status") == "INDEXED"),
            "total_skipped": sum(1 for d in docs if d.get("status") == "SKIPPED"),
            "total_failed": sum(1 for d in docs if d.get("status") == "FAILED"),
            "total_chunks": self._manifest_data.get("total_chunks", 0),
            "last_updated": self._manifest_data.get("last_updated"),
            "categories": list(set(d.get("category", "") for d in docs if d.get("category"))),
            "file_types": list(set(d.get("file_type", "") for d in docs if d.get("file_type")))
        }
