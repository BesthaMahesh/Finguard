import re
import logging
from typing import List, Dict, Any, Optional
from backend.rag.document_types import DocumentChunk

logger = logging.getLogger(__name__)

class DocumentChunker:
    """
    Intelligent document chunker:
    - Preserves PDF page numbers
    - Preserves Markdown heading hierarchy and section context
    - Paragraph and sentence boundary aware
    - Configurable chunk size and overlap
    """

    def __init__(self, target_chunk_size: int = 1000, chunk_overlap: int = 150):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text_clean(self, text: str) -> List[str]:
        """
        Splits long text blocks while respecting paragraph and sentence boundaries.
        """
        text = text.strip()
        if not text:
            return []
        if len(text) <= self.target_chunk_size:
            return [text]

        # Split by double newlines first (paragraphs)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        current_chunk = ""

        for p in paragraphs:
            if len(p) > self.target_chunk_size:
                # If paragraph itself is larger than chunk size, split by sentences
                sentences = re.split(r"(?<=[.!?])\s+", p)
                for s in sentences:
                    s = s.strip()
                    if not s:
                        continue
                    if len(current_chunk) + len(s) + 1 <= self.target_chunk_size:
                        current_chunk = f"{current_chunk} {s}".strip() if current_chunk else s
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = s
            else:
                if len(current_chunk) + len(p) + 2 <= self.target_chunk_size:
                    current_chunk = f"{current_chunk}\n\n{p}".strip() if current_chunk else p
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = p

        if current_chunk:
            chunks.append(current_chunk)

        # Add overlap if needed
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped_chunks = [chunks[0]]
            for i in range(1, len(chunks)):
                prev = chunks[i - 1]
                curr = chunks[i]
                overlap_text = prev[-self.chunk_overlap:].strip()
                if overlap_text and not curr.startswith(overlap_text):
                    overlapped_chunks.append(f"...{overlap_text}\n{curr}")
                else:
                    overlapped_chunks.append(curr)
            return overlapped_chunks

        return chunks

    def chunk_pdf_pages(
        self,
        doc_id: str,
        title: str,
        filename: str,
        category: str,
        source_type: str,
        pages: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Creates chunks from PDF pages, strictly preserving page numbers.
        """
        chunks: List[DocumentChunk] = []
        chunk_idx = 0

        for p in pages:
            page_num = p["page_number"]
            page_text = p["text"].strip()
            if not page_text or len(page_text) < 15:
                continue

            sub_chunks = self.split_text_clean(page_text)
            for sub_i, sc in enumerate(sub_chunks):
                chunk_id = f"{doc_id}-p{page_num}-c{sub_i + 1}"
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    document_title=title,
                    section=f"Page {page_num}",
                    page_number=page_num,
                    file_type="PDF",
                    source_file=filename,
                    source_type=source_type,
                    category=category,
                    text=sc,
                    chunk_index=chunk_idx
                ))
                chunk_idx += 1

        return chunks

    def chunk_markdown_sections(
        self,
        doc_id: str,
        title: str,
        filename: str,
        category: str,
        source_type: str,
        sections: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Creates chunks from Markdown sections, preserving section heading context.
        """
        chunks: List[DocumentChunk] = []
        chunk_idx = 0

        for s_idx, sec in enumerate(sections):
            heading = sec["heading"]
            content = sec["content"].strip()
            if not content or len(content) < 10:
                continue

            sub_chunks = self.split_text_clean(content)
            for sub_i, sc in enumerate(sub_chunks):
                chunk_id = f"{doc_id}-s{s_idx + 1}-c{sub_i + 1}"
                
                # Contextually prefix section header if not present in chunk
                formatted_text = sc
                if heading != "Overview" and not sc.startswith("#"):
                    formatted_text = f"[{heading}]\n{sc}"

                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    document_title=title,
                    section=heading,
                    page_number=1,  # Markdown single-document baseline
                    file_type="MD",
                    source_file=filename,
                    source_type=source_type,
                    category=category,
                    text=formatted_text,
                    chunk_index=chunk_idx
                ))
                chunk_idx += 1

        return chunks

    def chunk_raw_text(
        self,
        doc_id: str,
        title: str,
        filename: str,
        file_type: str,
        category: str,
        source_type: str,
        raw_text: str
    ) -> List[DocumentChunk]:
        """
        Fallback chunker for Plain Text, HTML, CSV, DOCX.
        """
        chunks: List[DocumentChunk] = []
        sub_chunks = self.split_text_clean(raw_text)
        for i, sc in enumerate(sub_chunks):
            chunk_id = f"{doc_id}-c{i + 1}"
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                document_title=title,
                section="General Guidance",
                page_number=1,
                file_type=file_type,
                source_file=filename,
                source_type=source_type,
                category=category,
                text=sc,
                chunk_index=i
            ))
        return chunks
