import os
import re
import csv
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TextLoader:
    """
    Handles Plain Text (.txt), HTML (.html, .htm), CSV (.csv), and Word (.docx).
    """

    @classmethod
    def load_plain_text(cls, file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
        filename = os.path.basename(file_path)
        first_line = content.splitlines()[0] if content else filename
        title = first_line[:80].strip("# ").strip() or filename
        return {
            "file_name": filename,
            "file_path": file_path,
            "title": title,
            "content": content,
            "total_characters": len(content)
        }

    @classmethod
    def load_html(cls, file_path: str) -> Dict[str, Any]:
        from bs4 import BeautifulSoup
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else os.path.basename(file_path)
        text = soup.get_text(separator="\n\n").strip()
        return {
            "file_name": os.path.basename(file_path),
            "file_path": file_path,
            "title": title,
            "content": text,
            "total_characters": len(text)
        }

    @classmethod
    def load_csv(cls, file_path: str) -> Dict[str, Any]:
        """
        Extracts tabular schema, summary columns, and sample records from CSV.
        """
        filename = os.path.basename(file_path)
        rows = []
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i < 50:  # Sample up to 50 rows for schema summary
                    rows.append(row)
                else:
                    break

        if not rows:
            return {
                "file_name": filename,
                "file_path": file_path,
                "title": filename,
                "content": f"Empty CSV dataset: {filename}",
                "total_characters": 0
            }

        headers = rows[0]
        summary_md = [
            f"# Dataset Summary: {filename}",
            f"**Total Sampled Columns:** {len(headers)}",
            f"**Columns:** {', '.join(headers)}",
            "\n### Sample Rows:\n"
        ]
        for row in rows[1:6]:
            summary_md.append("- " + " | ".join(row))

        content = "\n".join(summary_md)
        return {
            "file_name": filename,
            "file_path": file_path,
            "title": f"Dataset: {filename}",
            "content": content,
            "total_characters": len(content)
        }

    @classmethod
    def load_docx(cls, file_path: str) -> Dict[str, Any]:
        try:
            import docx
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = "\n\n".join(paragraphs)
            title = paragraphs[0][:80] if paragraphs else os.path.basename(file_path)
            return {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "title": title,
                "content": content,
                "total_characters": len(content)
            }
        except ImportError:
            raise RuntimeError(
                "python-docx is not installed. To ingest .docx documents, run: pip install python-docx"
            )
