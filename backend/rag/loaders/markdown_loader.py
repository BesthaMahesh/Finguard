import os
import re
import logging
from typing import List, Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)

class MarkdownExtractionError(Exception):
    pass

class MarkdownLoader:
    """
    Dedicated Markdown loader:
    - Parses YAML frontmatter if present
    - Preserves heading hierarchy (#, ##, ###)
    - Preserves tables, lists, and code blocks
    - Splits content keeping headings with their associated sections
    """

    @classmethod
    def load_markdown(cls, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise MarkdownExtractionError(f"Markdown file is completely empty (0 bytes): {file_path}")

        filename = os.path.basename(file_path)

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_content = f.read()

        clean_content = raw_content.strip()
        if not clean_content:
            raise MarkdownExtractionError(f"Markdown file contains no readable text: {file_path}")

        # Parse YAML frontmatter if present (between --- and ---)
        frontmatter = {}
        body_content = clean_content

        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", clean_content, re.DOTALL)
        if frontmatter_match:
            fm_text = frontmatter_match.group(1)
            body_content = frontmatter_match.group(2).strip()
            try:
                parsed_fm = yaml.safe_load(fm_text)
                if isinstance(parsed_fm, dict):
                    frontmatter = parsed_fm
            except Exception as e:
                logger.warning(f"Failed to parse YAML frontmatter in {filename}: {e}")

        # Determine title
        title = frontmatter.get("title")
        if not title:
            # Look for top-level header # Title
            h1_match = re.search(r"^#\s+(.+)$", body_content, re.MULTILINE)
            if h1_match:
                title = h1_match.group(1).strip()
            else:
                title = filename.replace(".markdown", "").replace(".md", "").replace("_", " ").title()

        # Extract Document ID if explicitly stated
        doc_id = frontmatter.get("document_id") or frontmatter.get("doc_id")
        if not doc_id:
            doc_id_match = re.search(r"Document ID:\s*([A-Za-z0-9\-]+)", body_content)
            if doc_id_match:
                doc_id = doc_id_match.group(1).strip()
            else:
                doc_id = filename.replace(".markdown", "").replace(".md", "").lower()

        # Parse sections based on markdown headers (## or #)
        sections = cls._extract_sections(body_content)

        return {
            "file_name": filename,
            "file_path": file_path,
            "doc_id": doc_id,
            "title": title,
            "frontmatter": frontmatter,
            "sections": sections,
            "raw_content": body_content,
            "total_characters": len(body_content)
        }

    @classmethod
    def _extract_sections(cls, markdown_text: str) -> List[Dict[str, Any]]:
        """
        Splits markdown into logical sections while keeping headers with content.
        """
        lines = markdown_text.splitlines()
        sections: List[Dict[str, Any]] = []
        
        current_header = "Overview"
        current_level = 1
        current_lines: List[str] = []

        header_regex = re.compile(r"^(#{1,4})\s+(.+)$")

        for line in lines:
            match = header_regex.match(line)
            if match:
                # If we have accumulated lines, commit current section
                if current_lines:
                    text = "\n".join(current_lines).strip()
                    if text:
                        sections.append({
                            "heading": current_header,
                            "level": current_level,
                            "content": text
                        })
                    current_lines = []

                current_level = len(match.group(1))
                current_header = match.group(2).strip()
                current_lines.append(line)
            else:
                current_lines.append(line)

        # Commit final section
        if current_lines:
            text = "\n".join(current_lines).strip()
            if text:
                sections.append({
                    "heading": current_header,
                    "level": current_level,
                    "content": text
                })

        # Fallback if no headers were found
        if not sections and markdown_text.strip():
            sections.append({
                "heading": "General Guidance",
                "level": 1,
                "content": markdown_text.strip()
            })

        return sections
