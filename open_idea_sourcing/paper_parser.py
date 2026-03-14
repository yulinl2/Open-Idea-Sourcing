"""Parse academic papers from PDF or plain-text sources.

Extracts the title, abstract, and body sections so that downstream
evaluators can work with structured content rather than raw bytes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PaperSection:
    """A single named section inside a paper (e.g. 'Introduction')."""

    title: str
    content: str

    def __repr__(self) -> str:
        return f"PaperSection(title={self.title!r}, chars={len(self.content)})"


@dataclass
class ParsedPaper:
    """All structured content extracted from an academic paper."""

    title: str
    abstract: str
    full_text: str
    sections: list[PaperSection] = field(default_factory=list)

    def key_content(self, max_chars: int = 6000) -> str:
        """Return the most informative slice of the paper for LLM prompts.

        Combines the title, abstract, and the beginning of the body so
        that the result fits within typical context-window limits.
        """
        parts: list[str] = []
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.abstract:
            parts.append(f"Abstract: {self.abstract}")
        body = self.full_text.strip()
        # Compute budget from the actual prefix length so separator accounting
        # is always accurate regardless of how many parts are present.
        prefix = "\n\n".join(parts)
        budget = max_chars - len(prefix) - (2 if prefix and body else 0)
        if budget > 0 and body:
            parts.append(body[:budget])
        return "\n\n".join(parts)[:max_chars]


class PaperParser:
    """Parse academic papers from PDF files or plain text."""

    # Section headings we recognise (case-insensitive)
    _SECTION_RE = re.compile(
        r"(?m)^(?:\d+[\.\s]+)?([A-Z][A-Za-z &/\-]{2,50})\s*$"
    )

    # Abstract delimiters — stops at a blank line followed by a digit
    # (numbered section) or a known section heading.
    _ABSTRACT_RE = re.compile(
        r"(?m)^abstract[:\s]*\n(.*?)(?=\n\n\s*\d|\n\n\s*(?:keywords?|introduction|background|method)|\Z)",
        re.DOTALL | re.IGNORECASE,
    )

    def parse_file(self, path: str | Path) -> ParsedPaper:
        """Auto-detect file type and parse accordingly."""
        p = Path(path)
        if p.suffix.lower() == ".pdf":
            return self.parse_pdf(str(p))
        return self.parse_text(p.read_text(encoding="utf-8", errors="replace"))

    def parse_pdf(self, pdf_path: str) -> ParsedPaper:
        """Extract text from a PDF and return a :class:`ParsedPaper`."""
        try:
            import pdfplumber  # optional at import time
        except ImportError as exc:
            raise ImportError(
                "pdfplumber is required for PDF parsing. "
                "Install it with: pip install pdfplumber"
            ) from exc

        with pdfplumber.open(pdf_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return self.parse_text("\n".join(pages))

    def parse_text(self, text: str) -> ParsedPaper:
        """Parse a paper from a plain-text string."""
        text = self._normalise(text)
        title = self._extract_title(text)
        abstract = self._extract_abstract(text)
        sections = self._extract_sections(text)
        return ParsedPaper(
            title=title,
            abstract=abstract,
            full_text=text,
            sections=sections,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(text: str) -> str:
        text = re.sub(r"\r\n?", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _extract_title(text: str) -> str:
        for line in text.splitlines():
            line = line.strip()
            if line:
                return line
        return ""

    def _extract_abstract(self, text: str) -> str:
        m = self._ABSTRACT_RE.search(text)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()[:2000]
        return ""

    def _extract_sections(self, text: str) -> list[PaperSection]:
        matches = list(self._SECTION_RE.finditer(text))
        sections: list[PaperSection] = []
        for i, m in enumerate(matches):
            title = m.group(1).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            if len(content) > 50:
                sections.append(PaperSection(title=title, content=content))
        return sections
