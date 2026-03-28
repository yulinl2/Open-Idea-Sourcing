"""Parse academic papers from PDF or plain-text sources.

Extracts the title, abstract, and body sections so that downstream
evaluators can work with structured content rather than raw bytes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


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
    authors: list[str] = field(default_factory=list)

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
        authors = self._extract_authors(text, title)
        return ParsedPaper(
            title=title,
            abstract=abstract,
            full_text=text,
            sections=sections,
            authors=authors,
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

    # Keywords that signal we have left the title area.
    _NON_TITLE_RE = re.compile(
        r"(?i)\b(abstract|introduction|university|institute|department|"
        r"laboratory|school|faculty|college|email|@|\bphd\b|\bdr\b)\b"
    )

    @staticmethod
    def _extract_title(text: str) -> str:
        """Return the paper title, joining continuation lines when needed.

        Many PDF-extracted papers split the title across two or three short
        lines (e.g. "Conformal Inference" / "of Counterfactuals and …").
        We join consecutive non-empty lines that look like title continuation
        (start with a lowercase letter or a short common connector word) up
        to a maximum of three lines.
        """
        lines: list[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                if lines:
                    break  # blank line after the title area — stop
                continue

            # Stop if we hit something that clearly isn't title text.
            if PaperParser._NON_TITLE_RE.search(line):
                break

            if not lines:
                lines.append(line)
                continue

            # A continuation line typically starts with a lowercase letter or
            # a connector word ("of", "for", "via", "with", "and", "in", etc.)
            # or looks like a subtitle (starts with "—", ":", or a dash).
            first_char = line[0] if line else ""
            is_continuation = (
                first_char.islower()
                or first_char in ("-", "—", ":")
                or re.match(
                    r"(?i)^(of|for|via|with|and|in|on|a|an|the|to|from|by|at)\b",
                    line,
                )
            )
            if is_continuation and len(lines) < 3:
                lines.append(line)
            else:
                break

        return " ".join(lines) if lines else ""

    @staticmethod
    def _extract_authors(text: str, title: str) -> list[str]:
        """Heuristically extract author names from the paper header.

        Authors typically appear on the lines immediately after the title,
        before institutional affiliations and the abstract.  We identify
        them as lines that:

        * consist of 2–5 words each starting with a capital letter (or an
          initial like "J."), allowing accented characters
        * do not contain digits, email addresses, or institutional keywords
        * appear within the first 30 lines of the document
        """
        # A name token is a capitalised word (with optional accents / hyphens)
        # or a single letter followed by a period (initial, e.g. "J.").
        # We use a broad Latin-extended range rather than a long explicit list.
        _NAME_TOKEN = re.compile(
            r"^[\u0041-\u005A\u00C0-\u00D6\u00D8-\u00DE]"  # uppercase first char
            r"[\u0061-\u007A\u00C0-\u00FF'\-]+$"            # lowercase rest
            r"|^[A-Z]\.$"                                    # single initial
        )
        _STOP = re.compile(
            r"(?i)\b(university|institute|department|laboratory|school|"
            r"faculty|college|abstract|introduction|@|\.edu|\.com|\.org)\b"
        )
        # Maximum number of words in a person-name line (handles "van den Berg").
        _MAX_NAME_WORDS = 5

        title_lines = {ln.strip() for ln in title.split(" ")}
        candidates: list[str] = []
        title_consumed = False

        for raw_line in text.splitlines()[:30]:
            line = raw_line.strip()
            if not line:
                continue

            # Skip until we've passed the title.
            if not title_consumed:
                if line in title or title in line or any(tl in line for tl in title_lines if len(tl) > 3):
                    title_consumed = True
                continue

            # Skip institutional affiliation lines but keep scanning for more authors.
            if _STOP.search(line):
                continue

            # Stop at section headings / numbered sections.
            if re.match(r"^\d+[\.\)]\s", line):
                break

            # Check if this looks like a name line.
            words = line.split()
            if 2 <= len(words) <= _MAX_NAME_WORDS and all(_NAME_TOKEN.match(w) for w in words):
                # Reject overly long "names" — real names rarely exceed 60 chars.
                if len(line) <= 60:
                    candidates.append(line)
                    if len(candidates) >= 8:
                        break

        return candidates

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


class LLMPaperParser(PaperParser):
    """LLM-enhanced paper parser (Stage 1).

    Uses an LLM to extract structured fields (title, abstract, authors,
    sections) from raw paper text.  Never falls back to the regex-based
    parser — raises :class:`RuntimeError` after all retries are exhausted.

    Parameters
    ----------
    llm:
        Callable that receives a prompt string and returns the LLM response.
    """

    _PARSE_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "paper_parse.txt"
    _MAX_RETRIES = 3

    def __init__(self, llm: Callable[[str], str]) -> None:
        self._llm = llm
        self._prompt_template = self._PARSE_PROMPT_PATH.read_text(encoding="utf-8")

    def parse_text(self, text: str) -> ParsedPaper:
        """Use LLM to extract structured paper content.

        Retries up to 3 times on failure or empty output.  Never falls back
        to regex — the LLM is the only extraction path.

        Parameters
        ----------
        text:
            Raw paper text.

        Returns
        -------
        ParsedPaper
            Structured paper content.

        Raises
        ------
        RuntimeError
            When all retries are exhausted without extracting a usable title
            or abstract.
        """
        text = self._normalise(text)
        snippet = text[:8000]
        prompt = self._prompt_template.format(raw_text=snippet)
        last_exc: Exception | None = None
        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                response = self._llm(prompt)
                parsed = self._parse_llm_response(response, text)
                if parsed.title or parsed.abstract:
                    return parsed
            except Exception as exc:
                last_exc = exc
        raise RuntimeError(
            f"LLMPaperParser: failed to extract paper structure after "
            f"{self._MAX_RETRIES} attempts"
            + (f": {last_exc}" if last_exc else "")
        )

    def _parse_llm_response(self, response: str, full_text: str) -> ParsedPaper:
        """Parse the LLM-structured response into a :class:`ParsedPaper`."""

        def _extract_field(text: str, field: str, default: str = "") -> str:
            pattern = rf"(?mi)^{re.escape(field)}:\s*(.+?)(?=\n[A-Z]+:|$)"
            m = re.search(pattern, text, re.DOTALL)
            return m.group(1).strip() if m else default

        title = _extract_field(response, "TITLE")
        authors_raw = _extract_field(response, "AUTHORS")
        abstract = _extract_field(response, "ABSTRACT")

        authors: list[str] = []
        if authors_raw and authors_raw.lower() not in ("unknown", "none", "not found"):
            authors = [a.strip() for a in authors_raw.split(",") if a.strip()]

        sections: list[PaperSection] = []
        sections_match = re.search(
            r"(?mi)^SECTIONS:\s*\n(.*?)(?=\n[A-Z]+:|\Z)", response, re.DOTALL
        )
        if sections_match:
            section_text = sections_match.group(1).strip()
            for line in section_text.splitlines():
                line = line.strip()
                if not line or line.lower() == "none":
                    continue
                section_title = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
                if section_title:
                    sections.append(PaperSection(title=section_title, content=""))

        if abstract.lower() in ("not found", "none", ""):
            abstract = ""

        return ParsedPaper(
            title=title,
            abstract=abstract,
            full_text=full_text,
            sections=sections,
            authors=authors,
        )
