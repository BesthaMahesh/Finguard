import os
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf": "PDF",
    ".md": "MD",
    ".markdown": "MD",
    ".txt": "TXT",
    ".docx": "DOCX",
    ".html": "HTML",
    ".htm": "HTML",
    ".csv": "CSV"
}

def calculate_file_hash(file_path: str) -> str:
    """
    Computes cryptographic SHA-256 hash of file contents for provenance and idempotency.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def infer_category_and_source_type(file_path: str, base_dir: str = "knowledge_base") -> Tuple[str, str]:
    """
    Infers document category and official vs internal vs research classification
    based on relative folder location and filename semantics.
    """
    rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/").lower()
    parts = rel_path.split("/")
    filename = os.path.basename(file_path).lower()

    # Check immediate parent folder
    if len(parts) > 1:
        parent = parts[0]
        if "regulation" in parent:
            return "regulations", "official_regulation"
        elif "aml" in parent or "kyc" in parent:
            return "aml_kyc", "official_regulation"
        elif "fraud" in parent:
            return "fraud_patterns", "sample_internal_policy"
        elif "internal" in parent or "policy" in parent:
            return "internal_policies", "sample_internal_policy"
        elif "research" in parent:
            return "research", "research"
        elif "dataset" in parent:
            return "dataset_documentation", "dataset_documentation"

    # Semantic filename heuristics for root or un-categorized files
    if any(k in filename for k in ["fatf", "fatt", "rbi", "fincen", "statute", "act", "circular", "master"]):
        return "regulations", "official_regulation"
    elif any(k in filename for k in ["kyc", "aml", "cdd", "edd", "due_diligence"]):
        return "aml_kyc", "official_regulation"
    elif any(k in filename for k in ["fraud", "typology", "mule", "ato", "liquidation"]):
        return "fraud_patterns", "sample_internal_policy"
    elif any(k in filename for k in ["ftfe", "paper", "study", "ownership"]):
        return "research", "research"
    elif any(k in filename for k in ["dataset", "paysim"]):
        return "dataset_documentation", "dataset_documentation"

    return "general_compliance", "sample_internal_policy"

def discover_documents(
    scan_dirs: List[str] = ["./knowledge_base", "./backend/rag/knowledge_base"]
) -> List[Dict[str, Any]]:
    """
    Recursively scans target directories for all supported document formats.
    Returns list of discovered document descriptors with metadata and content hashes.
    """
    discovered: List[Dict[str, Any]] = []
    seen_hashes: set = set()
    seen_paths: set = set()

    for directory in scan_dirs:
        if not os.path.exists(directory):
            continue

        for root, dirs, files in os.walk(directory):
            # Skip hidden, cache, or manifests directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "manifests" and d != "__pycache__"]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue

                full_path = os.path.abspath(os.path.join(root, file))
                norm_path = os.path.normpath(full_path)
                if norm_path in seen_paths:
                    continue
                seen_paths.add(norm_path)

                # Skip raw CSVs that are excessively large (> 25MB) as they are dataset records, not docs
                file_size = os.path.getsize(full_path)
                if ext == ".csv" and file_size > 25 * 1024 * 1024:
                    logger.info(f"Skipping raw large CSV file {file} ({file_size} bytes) from knowledge indexing.")
                    continue

                try:
                    content_hash = calculate_file_hash(full_path)
                except Exception as e:
                    logger.error(f"Cannot compute hash for {full_path}: {e}")
                    continue

                # Check duplicate content within this discovery pass
                is_duplicate = content_hash in seen_hashes
                seen_hashes.add(content_hash)

                file_type = SUPPORTED_EXTENSIONS[ext]
                category, source_type = infer_category_and_source_type(full_path, base_dir=directory)

                # Generate stable document ID
                clean_name = os.path.splitext(file)[0].lower().replace(" ", "-").replace("_", "-")
                doc_id = f"doc-{clean_name}"

                discovered.append({
                    "doc_id": doc_id,
                    "file_name": file,
                    "file_path": full_path,
                    "relative_path": os.path.relpath(full_path, os.getcwd()).replace("\\", "/"),
                    "file_type": file_type,
                    "file_size": file_size,
                    "content_hash": content_hash,
                    "category": category,
                    "source_type": source_type,
                    "is_duplicate": is_duplicate
                })

    logger.info(f"Discovered {len(discovered)} valid knowledge documents across directories: {scan_dirs}")
    return discovered
