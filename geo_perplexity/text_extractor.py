"""Batched full-text extraction from PDFs using LLMs as parser.

Downloads arXiv PDFs and extracts structured text via an LLM, falling
back to pdfplumber for raw extraction. Processes papers in configurable
batches to respect rate limits.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from .reference_collector import CitedPaper

_CACHE_DIR = Path(".cache/pdf_text")
_BATCH_SIZE = 5  # papers per batch
_BATCH_DELAY = 2.0  # seconds between batches
_DOWNLOAD_TIMEOUT = 30
_MAX_RETRIES = 3

# LLM prompt for structured paper extraction
_PARSE_PROMPT = """\
Extract the following fields from this academic paper text. Return ONLY
the fields below, no extra commentary.

TITLE: <paper title>
AUTHORS: <comma-separated author names, or "Unknown">
ABSTRACT: <full abstract text>
FULL_TEXT: <the complete body text of the paper, preserving section structure>

If a field cannot be determined, write "Not found".

---
Paper text (first 12000 characters):
{raw_text}
"""


def _ensure_cache_dir() -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(identifier: str) -> str:
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


def _load_cached(identifier: str) -> str | None:
    _ensure_cache_dir()
    path = _CACHE_DIR / f"{_cache_key(identifier)}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def _save_cache(identifier: str, text: str) -> None:
    _ensure_cache_dir()
    path = _CACHE_DIR / f"{_cache_key(identifier)}.txt"
    path.write_text(text, encoding="utf-8")


def download_arxiv_pdf(arxiv_id: str) -> str | None:
    """Download an arXiv PDF and return its file path, or None on failure."""
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    tmp_dir = Path(tempfile.gettempdir()) / "geo_perplexity_pdfs"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / f"{arxiv_id.replace('/', '_')}.pdf"

    if dest.exists():
        return str(dest)

    headers = {"User-Agent": "geo-perplexity/0.1.0"}
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT) as resp:
                dest.write_bytes(resp.read())
            return str(dest)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < _MAX_RETRIES:
                time.sleep(2 ** attempt)
                continue
            print(
                f"  [text_extractor] failed to download arXiv:{arxiv_id}: {exc}",
                file=sys.stderr,
            )
            return None


def extract_text_pdfplumber(pdf_path: str) -> str:
    """Extract raw text from a PDF using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        return ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages)
    except Exception as exc:
        print(f"  [text_extractor] pdfplumber failed: {exc}", file=sys.stderr)
        return ""


def extract_text_llm(raw_text: str, llm: Callable[[str], str]) -> str:
    """Use an LLM to extract structured full text from raw paper text."""
    snippet = raw_text[:12000]
    prompt = _PARSE_PROMPT.format(raw_text=snippet)

    try:
        response = llm(prompt)
    except Exception as exc:
        print(f"  [text_extractor] LLM extraction failed: {exc}", file=sys.stderr)
        return raw_text[:8000]  # fallback to raw text

    # Extract FULL_TEXT field from response
    import re
    m = re.search(r"FULL_TEXT:\s*(.+)", response, re.DOTALL)
    if m:
        text = m.group(1).strip()
        if text.lower() not in ("not found", "none", ""):
            return text

    # If extraction failed, return the raw text truncated
    return raw_text[:8000]


def batch_extract_full_text(
    papers: list[CitedPaper],
    llm: Callable[[str], str],
    *,
    batch_size: int = _BATCH_SIZE,
    batch_delay: float = _BATCH_DELAY,
) -> list[CitedPaper]:
    """Download and extract full text for a list of cited papers.

    Papers with arXiv IDs get PDF download + LLM extraction.
    Papers without arXiv IDs keep their Semantic Scholar abstract.
    Results are cached to disk.

    Parameters
    ----------
    papers:
        List of CitedPaper objects to process.
    llm:
        Callable that accepts a prompt string and returns LLM response.
    batch_size:
        Number of papers to process per batch.
    batch_delay:
        Seconds to wait between batches (rate limiting).

    Returns
    -------
    list[CitedPaper]
        Same papers with full_text populated where possible.
    """
    total = len(papers)
    extracted = 0
    skipped = 0

    for batch_start in range(0, total, batch_size):
        batch = papers[batch_start : batch_start + batch_size]

        for paper in batch:
            # Check cache first
            cache_id = paper.arxiv_id or paper.paper_id
            cached = _load_cached(cache_id)
            if cached:
                paper.full_text = cached
                extracted += 1
                continue

            if not paper.arxiv_id:
                # No arXiv ID — use abstract as full text
                if paper.abstract:
                    paper.full_text = paper.abstract
                    _save_cache(cache_id, paper.abstract)
                    extracted += 1
                else:
                    skipped += 1
                continue

            # Download PDF and extract
            pdf_path = download_arxiv_pdf(paper.arxiv_id)
            if not pdf_path:
                if paper.abstract:
                    paper.full_text = paper.abstract
                    _save_cache(cache_id, paper.abstract)
                skipped += 1
                continue

            raw_text = extract_text_pdfplumber(pdf_path)
            if not raw_text:
                if paper.abstract:
                    paper.full_text = paper.abstract
                    _save_cache(cache_id, paper.abstract)
                skipped += 1
                continue

            # LLM-enhanced extraction
            full_text = extract_text_llm(raw_text, llm)
            paper.full_text = full_text
            _save_cache(cache_id, full_text)
            extracted += 1

        # Progress report
        done = min(batch_start + batch_size, total)
        print(
            f"  [text_extractor] progress: {done}/{total} papers processed",
            file=sys.stderr,
        )

        # Rate-limit delay between batches
        if batch_start + batch_size < total:
            time.sleep(batch_delay)

    print(
        f"  [text_extractor] done: {extracted} extracted, {skipped} skipped",
        file=sys.stderr,
    )
    return papers
