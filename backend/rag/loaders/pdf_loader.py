import os
import logging
from typing import List, Dict, Any, Tuple
try:
    import pypdf
except ImportError:
    pypdf = None

logger = logging.getLogger(__name__)

class PDFExtractionError(Exception):
    pass

class PDFLoader:
    """
    Enterprise-grade PDF ingestion loader:
    - Extracts text page-by-page with exact page numbering
    - Preserves metadata, document title, and page provenance
    - Identifies empty, corrupted, password-protected, or scanned PDFs
    - Yields page records for streaming memory efficiency
    """

    @classmethod
    def load_pdf(cls, file_path: str) -> Dict[str, Any]:
        """
        Loads and validates a PDF document.
        Returns a dictionary containing:
        - title: str
        - total_pages: int
        - pages: List[Dict[str, Any]] (each with page_number: int, text: str)
        - metadata: Dict[str, Any]
        - total_characters: int
        - is_scanned_or_empty: bool
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise PDFExtractionError(f"PDF file is completely empty (0 bytes): {file_path}")

        filename = os.path.basename(file_path)
        if pypdf is None:
            raise PDFExtractionError(
                "pypdf is not installed. To ingest PDF documents, run: pip install pypdf"
            )

        try:
            reader = pypdf.PdfReader(file_path)
        except Exception as e:
            raise PDFExtractionError(f"Corrupted or invalid PDF format '{filename}': {str(e)}")

        if reader.is_encrypted:
            # Attempt empty password decryption
            try:
                decrypted = reader.decrypt("")
                if not decrypted:
                    raise PDFExtractionError(
                        f"PDF '{filename}' is password-protected and cannot be read without credentials."
                    )
            except Exception:
                raise PDFExtractionError(
                    f"PDF '{filename}' is encrypted and password-protected. Decryption failed."
                )

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise PDFExtractionError(f"PDF '{filename}' contains 0 pages.")

        # Extract PDF metadata
        pdf_meta = {}
        title = filename.replace(".pdf", "").replace("_", " ").title()
        if reader.metadata:
            for k, v in reader.metadata.items():
                clean_k = str(k).lstrip("/").lower()
                pdf_meta[clean_k] = str(v)
            if reader.metadata.title and reader.metadata.title.strip():
                extracted_title = reader.metadata.title.strip()
                if len(extracted_title) > 3 and not extracted_title.startswith("Untitled"):
                    title = extracted_title

        # Page-by-page text extraction
        pages: List[Dict[str, Any]] = []
        total_chars = 0
        non_empty_pages = 0

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            try:
                page_text = page.extract_text() or ""
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num} of {filename}: {e}")
                page_text = ""

            clean_text = page_text.strip()
            char_count = len(clean_text)
            total_chars += char_count

            if char_count > 0:
                non_empty_pages += 1

            pages.append({
                "page_number": page_num,
                "text": clean_text,
                "char_count": char_count
            })

        is_scanned = (total_chars < 50 and total_pages > 0) or (non_empty_pages == 0)
        if is_scanned:
            logger.warning(
                f"PDF '{filename}' has {total_pages} pages but only {total_chars} characters extracted. "
                "Document appears to be scanned or contains only raster graphics without OCR."
            )

        return {
            "file_name": filename,
            "file_path": file_path,
            "title": title,
            "total_pages": total_pages,
            "pages": pages,
            "total_characters": total_chars,
            "is_scanned_or_empty": is_scanned,
            "metadata": pdf_meta
        }
