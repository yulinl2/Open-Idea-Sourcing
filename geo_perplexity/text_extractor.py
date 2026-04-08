"""SOTA full-text extraction from academic PDFs.

Uses **pymupdf4llm** (PyMuPDF markdown backend) as the primary extractor —
it handles multi-column layouts, tables, math symbols, and embedded fonts
far more accurately than pdfplumber.  Falls back to **pdfminer.six** for
layout-based extraction when pymupdf4llm output is poor.

An optional LLM cleaning pass (GPT-4o) refines the pymupdf4llm markdown
into plain academic prose — removing figure captions, page-break artifacts,
table markup, and the references section — while preserving all substantive
text.

Fallback chain:  pymupdf4llm + LLM clean → pymupdf4llm raw → pdfminer → abstract.
"""

from __future__ import annotations

import hashlib
import json
import re
import signal
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

from .reference_collector import CitedPaper

# ── Cache config ──────────────────────────────────────────────────────
_CACHE_DIR = Path(".cache/pdf_text_v2")
_BATCH_SIZE = 5
_BATCH_DELAY = 1.5
_DOWNLOAD_TIMEOUT = 30
_MAX_RETRIES = 3

# ── Extraction limits ────────────────────────────────────────────────
_MAX_FULL_TEXT_CHARS = 120_000   # generous cap for very long papers
_MIN_USEFUL_LENGTH = 300        # below this, extraction is considered failed
_EXTRACT_TIMEOUT = 120          # seconds — abort pymupdf4llm if it takes too long


# ── LLM cleaning prompt ─────────────────────────────────────────────

_CLEAN_SYSTEM = """\
You are an expert academic-text cleaner.  You receive markdown extracted \
from a PDF of an academic paper.  Your job is to return the paper's \
substantive prose — clean, readable, paragraph-structured plain text.

Rules:
1. KEEP all sections from Abstract through Conclusion/Discussion \
   (inclusive).  Keep appendices if they contain methodological detail.
2. REMOVE: the references / bibliography section, figure/table captions, \
   page numbers, header/footer repetitions, and markdown table markup.
3. PRESERVE: all equations written inline, theorem/lemma statements, \
   algorithm descriptions, and mathematical notation.
4. CLEAN UP: fix broken words from column-break hyphenation, collapse \
   excessive whitespace, and join lines that were split mid-sentence.
5. Output ONLY the cleaned text — no commentary, no markdown fences.
6. Preserve section headings as simple lines (e.g. "1 Introduction")."""

_CLEAN_USER = """\
Clean the following extracted markdown ({n_chars} chars) from an academic \
paper.  Return only the cleaned body text.

--- EXTRACTED MARKDOWN ---
{md_text}
--- END ---"""


# ── Cache helpers ────────────────────────────────────────────────────

def _ensure_cache_dir() -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(identifier: str) -> str:
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


def _load_cached(identifier: str) -> str | None:
    _ensure_cache_dir()
    path = _CACHE_DIR / f"{_cache_key(identifier)}.json"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def _save_cache(identifier: str, text: str) -> None:
    _ensure_cache_dir()
    path = _CACHE_DIR / f"{_cache_key(identifier)}.json"
    path.write_text(text, encoding="utf-8")


# ── PDF download ─────────────────────────────────────────────────────

def download_arxiv_pdf(arxiv_id: str) -> str | None:
    """Download an arXiv PDF and return its local file path."""
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    tmp_dir = Path(tempfile.gettempdir()) / "geo_perplexity_pdfs"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / f"{arxiv_id.replace('/', '_')}.pdf"

    if dest.exists() and dest.stat().st_size > 1000:
        return str(dest)

    headers = {"User-Agent": "geo-perplexity/0.2.0 (academic research)"}
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT) as resp:
                data = resp.read()
                if not data[:5].startswith(b"%PDF"):
                    print(
                        f"  [v2-extractor] arXiv:{arxiv_id}: not a PDF "
                        f"({len(data)} bytes)",
                        file=sys.stderr,
                    )
                    return None
                dest.write_bytes(data)
            return str(dest)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            if attempt < _MAX_RETRIES:
                time.sleep(2 ** attempt)
                continue
            print(f"  [v2-extractor] download failed arXiv:{arxiv_id}: {exc}",
                  file=sys.stderr)
            return None


# ── Primary: pymupdf4llm ────────────────────────────────────────────

class _ExtractionTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise _ExtractionTimeout("extraction timed out")


def extract_text_pymupdf4llm(pdf_path: str) -> str:
    """Extract markdown text from a PDF using pymupdf4llm (PyMuPDF).

    This is the SOTA approach — handles multi-column academic layouts,
    embedded math, tables, and produces clean markdown output.
    Uses SIGALRM timeout to prevent hangs on very large PDFs.
    """
    try:
        import pymupdf4llm
    except ImportError:
        print("  [v2-extractor] pymupdf4llm not installed", file=sys.stderr)
        return ""
    try:
        # Set alarm-based timeout
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(_EXTRACT_TIMEOUT)
        try:
            md = pymupdf4llm.to_markdown(pdf_path)
        finally:
            signal.alarm(0)  # cancel alarm
            signal.signal(signal.SIGALRM, old_handler)

        if not md or len(md.strip()) < _MIN_USEFUL_LENGTH:
            return ""
        return md[:_MAX_FULL_TEXT_CHARS]
    except _ExtractionTimeout:
        print(f"  [v2-extractor] pymupdf4llm timed out ({_EXTRACT_TIMEOUT}s) "
              f"for {pdf_path}", file=sys.stderr)
        return ""
    except Exception as exc:
        print(f"  [v2-extractor] pymupdf4llm error: {exc}", file=sys.stderr)
        return ""


# ── Fallback: pdfminer.six ──────────────────────────────────────────

def extract_text_pdfminer(pdf_path: str) -> str:
    """Extract text using pdfminer.six layout analysis.

    Good at preserving reading order in multi-column PDFs.
    """
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        print("  [v2-extractor] pdfminer.six not installed", file=sys.stderr)
        return ""
    try:
        text = extract_text(pdf_path)
        if not text or len(text.strip()) < _MIN_USEFUL_LENGTH:
            return ""
        return text[:_MAX_FULL_TEXT_CHARS]
    except Exception as exc:
        print(f"  [v2-extractor] pdfminer error: {exc}", file=sys.stderr)
        return ""


# ── Text cleaning ────────────────────────────────────────────────────

def _strip_references_section(text: str) -> str:
    """Remove the References / Bibliography section from the end of the text."""
    # Look for common reference-section headings
    patterns = [
        # Markdown headings
        r'\n#{1,3}\s*\*{0,2}References\*{0,2}\s*\n',
        r'\n#{1,3}\s*\*{0,2}Bibliography\*{0,2}\s*\n',
        r'\n#{1,3}\s*\*{0,2}Works Cited\*{0,2}\s*\n',
        # Numbered section headings
        r'\n\d+\.?\s+References\s*\n',
        r'\n\d+\.?\s+Bibliography\s*\n',
        # Plain headings (bold or uppercase)
        r'\n\*{2}References\*{2}\s*\n',
        r'\nREFERENCES\s*\n',
        r'\nBIBLIOGRAPHY\s*\n',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            # Keep everything before the references heading
            before = text[:m.start()]
            # Sanity: don't strip more than 60% of the text
            if len(before) > len(text) * 0.3:
                return before.rstrip()
    return text


def _strip_markdown_artifacts(text: str) -> str:
    """Remove markdown formatting artifacts while preserving content."""
    # Remove pymupdf4llm figure placeholders: **==> picture [...] <==**
    text = re.sub(
        r'\*{0,2}=+>\s*picture\s*\[[^\]]*\]\s*intentionally omitted\s*<?=+\*{0,2}',
        '', text,
    )
    # Remove pymupdf4llm picture-text blocks: ----- Start/End of picture text -----
    text = re.sub(r'-{3,}\s*(?:Start|End) of picture text\s*-{3,}', '', text)
    # Remove image references: ![...](...)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    # Remove bold/italic markers but keep the text
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    # Remove markdown links: [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    # Remove horizontal rules
    text = re.sub(r'\n-{3,}\n', '\n', text)
    text = re.sub(r'\n\*{3,}\n', '\n', text)
    # Clean up heading markers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove only real HTML tags (short, with known tag names) — NOT math < > symbols
    text = re.sub(r'<(?:br|hr|/?\w{1,10})(?:\s[^>]{0,50})?/?>', '', text)
    # Remove standalone page numbers (isolated 1-3 digit numbers between blank lines)
    text = re.sub(r'\n\n\d{1,3}\s*\n\n', '\n\n', text)
    # Collapse runs of blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _strip_running_headers(text: str, title: str) -> str:
    """Remove repeated page headers (page number + paper title on each page)."""
    if not title or len(title) < 10:
        return text
    # Escape title for regex and allow minor variations
    esc = re.escape(title[:60])
    # Match: page number line, blank line, title line
    text = re.sub(
        r'^\d{1,3}\s*\n\n' + esc + r'\s*\n',
        '\n', text, flags=re.MULTILINE,
    )
    # Also match: "N Author Name" style headers (e.g. "4 Lihua Lei and Emmanuel J. Candès")
    text = re.sub(r'^\d{1,3}\s+_[A-Z][a-z]+.*?_\s*$', '', text, flags=re.MULTILINE)
    return text


def _extract_abstract_from_md(md_text: str) -> str:
    """Try to extract the abstract from markdown text."""
    # Pattern 1: "Abstract"/"Summary" heading (possibly bold) followed by text
    # until next section heading.  The abstract text may start on the same line
    # (e.g. "**Summary** . Evaluating...") or on the next line.
    m = re.search(
        r'(?:^|\n)(?:#{1,3}\s*)?(?:\*{0,2})?(?:Abstract|ABSTRACT|Summary)(?:\*{0,2})?'
        r'[:\.\s]*\n?(.*?)(?=\n#{1,3}\s|\n\d+[\.\s]+[A-Z]|\n\*{2}\d+[\.\s])',
        md_text, re.DOTALL | re.IGNORECASE,
    )
    if m:
        abstract = re.sub(r'\s+', ' ', m.group(1)).strip()
        if len(abstract) > 50:
            return abstract[:3000]

    # Fallback: look for "Abstract." or "Summary:" inline with text following
    m = re.search(
        r'(?:Abstract|Summary)[:\.\s]+(.{50,3000}?)(?:\n\n\n|\n#{1,3}\s|\n\d+[\.\s]+[A-Z])',
        md_text, re.DOTALL | re.IGNORECASE,
    )
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip()[:3000]

    return ""


def _extract_title_from_md(md_text: str) -> str:
    """Extract the paper title from the first heading or prominent line."""
    # Look for first markdown heading
    m = re.search(r'^#{1,3}\s+\*{0,2}(.+?)\*{0,2}\s*$', md_text, re.MULTILINE)
    if m:
        title = m.group(1).strip()
        if 10 < len(title) < 300:
            return title

    # Fallback: first substantial line
    for line in md_text.splitlines()[:15]:
        line = line.strip().strip('#').strip('*').strip()
        if len(line) > 10 and not any(
            kw in line.lower()
            for kw in ['abstract', 'arxiv', 'http', 'university', 'department']
        ):
            return line[:300]

    return ""


def clean_extracted_text(
    md_text: str,
    *,
    llm_clean: Optional[Callable[[str, str], str]] = None,
    title: str = "",
) -> str:
    """Clean extracted markdown into plain academic prose.

    If llm_clean is provided, uses the LLM for high-quality cleaning.
    Otherwise does rule-based cleaning.

    Args:
        llm_clean: callable(system_prompt, user_prompt) -> str.
            Should return plain text (not JSON).
    """
    # Always strip references first
    text = _strip_references_section(md_text)

    if llm_clean and len(text) > _MIN_USEFUL_LENGTH:
        # Use LLM for deep cleaning — send in chunks if very long
        # LLM context is limited, so send up to ~60K chars
        chunk_to_clean = text[:60000]
        user_msg = _CLEAN_USER.format(
            n_chars=len(chunk_to_clean), md_text=chunk_to_clean,
        )
        try:
            resp = llm_clean(_CLEAN_SYSTEM, user_msg)
            cleaned = resp.strip()
            # Basic validation: LLM output should be substantial
            if len(cleaned) > len(chunk_to_clean) * 0.15:
                # If original was longer than what we sent to LLM, append rest
                if len(text) > 60000:
                    remainder = _strip_markdown_artifacts(text[55000:])
                    cleaned = cleaned + "\n\n" + remainder
                return cleaned[:_MAX_FULL_TEXT_CHARS]
        except Exception as exc:
            print(f"  [v2-extractor] LLM cleaning failed: {exc}", file=sys.stderr)

    # Rule-based fallback cleaning
    text = _strip_markdown_artifacts(text)
    if title:
        text = _strip_running_headers(text, title)
    return text[:_MAX_FULL_TEXT_CHARS]


# ── Main extraction pipeline ────────────────────────────────────────

def extract_full_text(
    pdf_path: str,
    *,
    llm_json: Optional[Callable[[str, str], str]] = None,
    use_llm_cleaning: bool = True,
) -> dict[str, Any]:
    """Extract full text from a PDF using the SOTA pipeline.

    Args:
        llm_json: callable(system_prompt, user_prompt) -> str.
            Used for LLM-based text cleaning.  Despite the name, this
            callable should return plain text (not JSON) for the cleaning
            pass.  The name is kept for backward compatibility with callers.
        use_llm_cleaning: if True and llm_json is provided, apply LLM
            cleaning to the extracted markdown.

    Returns a dict with:
        - full_text: cleaned body text
        - raw_md: raw pymupdf4llm markdown (for audit)
        - title: extracted title
        - abstract: extracted abstract
        - extraction_method: which extractor succeeded
        - raw_md_length: character count of raw markdown
    """
    result: dict[str, Any] = {
        "full_text": "",
        "raw_md": "",
        "title": "",
        "abstract": "",
        "extraction_method": "none",
        "raw_md_length": 0,
    }

    # ── Try pymupdf4llm first (SOTA) ──
    raw_md = extract_text_pymupdf4llm(pdf_path)
    if raw_md and len(raw_md) >= _MIN_USEFUL_LENGTH:
        result["raw_md"] = raw_md
        result["raw_md_length"] = len(raw_md)
        result["title"] = _extract_title_from_md(raw_md)
        result["abstract"] = _extract_abstract_from_md(raw_md)

        lj = llm_json if (use_llm_cleaning and llm_json) else None
        result["full_text"] = clean_extracted_text(
            raw_md, llm_clean=lj, title=result["title"],
        )
        result["extraction_method"] = "pymupdf4llm+llm" if lj else "pymupdf4llm"
        return result

    # ── Fallback: pdfminer.six ──
    print("  [v2-extractor] pymupdf4llm failed, trying pdfminer.six",
          file=sys.stderr)
    raw_pdfminer = extract_text_pdfminer(pdf_path)
    if raw_pdfminer and len(raw_pdfminer) >= _MIN_USEFUL_LENGTH:
        result["raw_md"] = raw_pdfminer
        result["raw_md_length"] = len(raw_pdfminer)
        result["extraction_method"] = "pdfminer"

        # Try basic title/abstract extraction from plain text
        for line in raw_pdfminer.splitlines()[:10]:
            line = line.strip()
            if len(line) > 10 and not any(
                kw in line.lower()
                for kw in ['abstract', 'arxiv', 'http']
            ):
                result["title"] = line[:300]
                break

        m = re.search(
            r'(?i)abstract[:\s]*\n(.+?)(?=\n\n|\nintroduction|\n1[\.\s])',
            raw_pdfminer, re.DOTALL,
        )
        if m:
            result["abstract"] = re.sub(r'\s+', ' ', m.group(1)).strip()[:3000]

        result["full_text"] = _strip_references_section(raw_pdfminer)
        return result

    print("  [v2-extractor] all extraction methods failed", file=sys.stderr)
    return result


# ── Batch extraction for cited papers ────────────────────────────────

def batch_extract_full_text(
    papers: list[CitedPaper],
    llm_json: Callable[[str, str], str],
    *,
    batch_size: int = _BATCH_SIZE,
    batch_delay: float = _BATCH_DELAY,
) -> list[CitedPaper]:
    """Download and extract full text for cited papers.

    Uses pymupdf4llm (no LLM cleaning) for references to save cost.
    Falls back to pdfminer.six, then abstract.
    """
    total = len(papers)
    stats = {"pymupdf4llm": 0, "pdfminer": 0, "abstract_only": 0, "skipped": 0}

    for batch_start in range(0, total, batch_size):
        batch = papers[batch_start : batch_start + batch_size]

        for paper in batch:
            cache_id = paper.arxiv_id or paper.paper_id
            cached = _load_cached(cache_id)
            if cached:
                paper.full_text = cached
                paper.content_source = "full_text_pymupdf4llm"
                stats["pymupdf4llm"] += 1
                continue

            if not paper.arxiv_id:
                if paper.abstract:
                    paper.full_text = paper.abstract
                    _save_cache(cache_id, paper.abstract)
                    stats["abstract_only"] += 1
                else:
                    stats["skipped"] += 1
                continue

            # Download PDF
            pdf_path = download_arxiv_pdf(paper.arxiv_id)
            if not pdf_path:
                if paper.abstract:
                    paper.full_text = paper.abstract
                    _save_cache(cache_id, paper.abstract)
                    stats["abstract_only"] += 1
                else:
                    stats["skipped"] += 1
                continue

            # Try pymupdf4llm (no LLM cleaning for references — too costly)
            extraction = extract_full_text(
                pdf_path, llm_json=None, use_llm_cleaning=False,
            )
            full_text = extraction["full_text"]

            if full_text and len(full_text) >= _MIN_USEFUL_LENGTH:
                paper.full_text = full_text
                _save_cache(cache_id, full_text)
                method = extraction["extraction_method"]
                paper.content_source = f"full_text_{method}"
                stats[method.split("+")[0]] = stats.get(method.split("+")[0], 0) + 1
            elif paper.abstract:
                paper.full_text = paper.abstract
                _save_cache(cache_id, paper.abstract)
                paper.content_source = "abstract"
                stats["abstract_only"] += 1
            else:
                stats["skipped"] += 1

        done = min(batch_start + batch_size, total)
        print(
            f"  [v2-extractor] {done}/{total} processed "
            f"(pymupdf4llm={stats['pymupdf4llm']}, pdfminer={stats['pdfminer']}, "
            f"abstract={stats['abstract_only']}, skip={stats['skipped']})",
            file=sys.stderr,
        )

        if batch_start + batch_size < total:
            time.sleep(batch_delay)

    print(f"  [v2-extractor] done: {stats}", file=sys.stderr)
    return papers
