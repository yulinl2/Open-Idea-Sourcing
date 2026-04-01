"""Batched full-text extraction from PDFs using an agentic LLM parser.

Downloads arXiv PDFs and extracts structured text via a multi-turn LLM
conversation with tool-use-style structured outputs.  When the first
extraction pass is incomplete or low-confidence, the parser runs a
second "refinement" turn asking the model to fill gaps.

Falls back gracefully: LLM parse → pdfplumber raw text → abstract only.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from .reference_collector import CitedPaper

_CACHE_DIR = Path(".cache/pdf_text")
_BATCH_SIZE = 5
_BATCH_DELAY = 1.5
_DOWNLOAD_TIMEOUT = 30
_MAX_RETRIES = 3

# ── Agentic parser prompts ─────────────────────────────────────────────

_EXTRACT_SYSTEM = """\
You are an expert academic paper parser.  Given raw text extracted from a \
PDF, you produce clean, structured output.  You handle messy OCR, column \
layouts, header/footer noise, and reference-list boilerplate gracefully.

Return a JSON object with EXACTLY these keys:
{
  "title": "<paper title>",
  "authors": ["<author 1>", "<author 2>"],
  "abstract": "<full abstract text>",
  "sections": [
    {"heading": "<section heading>", "text": "<section body text>"}
  ],
  "full_text": "<complete body text, sections concatenated, cleaned>",
  "confidence": <0.0-1.0 float — your confidence in extraction quality>
}

Rules:
- Strip page numbers, headers/footers, and column-break artifacts.
- Preserve paragraph structure with blank lines.
- Do NOT include the reference/bibliography list in full_text.
- If a field is genuinely unrecoverable, use "" or [].
- Output ONLY valid JSON — no markdown fences, no commentary."""

_EXTRACT_USER = """\
Parse the following raw paper text (first {n_chars} characters).  \
Return the structured JSON.

--- RAW TEXT ---
{raw_text}
--- END ---"""

_REFINE_USER = """\
Your previous extraction had confidence {confidence:.2f}.  Here are \
additional pages of the paper that may help fill gaps.  Update and \
return the COMPLETE JSON structure (not just the changes).

--- ADDITIONAL TEXT (chars {start}-{end}) ---
{extra_text}
--- END ---"""


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


def download_arxiv_pdf(arxiv_id: str) -> str | None:
    """Download an arXiv PDF and return its local file path."""
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    tmp_dir = Path(tempfile.gettempdir()) / "geo_perplexity_pdfs"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / f"{arxiv_id.replace('/', '_')}.pdf"

    if dest.exists() and dest.stat().st_size > 1000:
        return str(dest)

    headers = {"User-Agent": "geo-perplexity/0.1.0 (academic research)"}
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT) as resp:
                data = resp.read()
                # Sanity check: PDFs start with %PDF
                if not data[:5].startswith(b"%PDF"):
                    print(
                        f"  [extractor] arXiv:{arxiv_id}: response is not a PDF "
                        f"({len(data)} bytes, starts with {data[:20]!r})",
                        file=sys.stderr,
                    )
                    return None
                dest.write_bytes(data)
            return str(dest)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            if attempt < _MAX_RETRIES:
                time.sleep(2 ** attempt)
                continue
            print(f"  [extractor] download failed arXiv:{arxiv_id}: {exc}", file=sys.stderr)
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
        text = "\n\n".join(p for p in pages if p.strip())
        return text
    except Exception as exc:
        print(f"  [extractor] pdfplumber error: {exc}", file=sys.stderr)
        return ""


def _parse_json_response(text: str) -> dict[str, Any] | None:
    """Robustly parse a JSON response, handling markdown fences etc."""
    text = text.strip()
    # Strip ```json ... ``` fences
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n?```$", "", text.strip())

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON object in the response
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return None


def extract_text_llm_agentic(
    raw_text: str,
    llm_json: Callable[[str, str], str],
) -> str:
    """Multi-turn agentic LLM extraction with refinement.

    Parameters
    ----------
    raw_text:
        Raw text from pdfplumber.
    llm_json:
        Callable(system_prompt, user_prompt) -> response_text.
        Should be configured for JSON output mode if the model supports it.

    Returns
    -------
    str
        Cleaned full text of the paper, or raw text fallback.
    """
    # Pass 1: initial extraction (first 15K chars)
    first_chunk = raw_text[:15000]
    user_msg = _EXTRACT_USER.format(n_chars=len(first_chunk), raw_text=first_chunk)

    try:
        resp1 = llm_json(_EXTRACT_SYSTEM, user_msg)
    except Exception as exc:
        print(f"  [extractor] LLM pass-1 failed: {exc}", file=sys.stderr)
        return _clean_raw_fallback(raw_text)

    parsed = _parse_json_response(resp1)
    if not parsed:
        print("  [extractor] LLM pass-1: could not parse JSON response", file=sys.stderr)
        return _clean_raw_fallback(raw_text)

    confidence = parsed.get("confidence", 0.0)
    full_text = parsed.get("full_text", "")

    # Pass 2: refinement if confidence is low and we have more text
    if confidence < 0.7 and len(raw_text) > 15000:
        extra = raw_text[12000:28000]  # overlapping window
        refine_msg = _REFINE_USER.format(
            confidence=confidence,
            start=12000,
            end=min(28000, len(raw_text)),
            extra_text=extra,
        )
        try:
            resp2 = llm_json(_EXTRACT_SYSTEM, refine_msg)
            parsed2 = _parse_json_response(resp2)
            if parsed2 and parsed2.get("full_text"):
                full_text = parsed2["full_text"]
                confidence = parsed2.get("confidence", confidence)
        except Exception as exc:
            print(f"  [extractor] LLM pass-2 refinement failed: {exc}", file=sys.stderr)

    if full_text and len(full_text) > 200:
        return full_text

    # Fall back to assembling from sections
    sections = parsed.get("sections", [])
    if sections:
        assembled = "\n\n".join(
            f"## {s.get('heading', '')}\n\n{s.get('text', '')}"
            for s in sections
            if s.get("text")
        )
        if len(assembled) > 200:
            return assembled

    return _clean_raw_fallback(raw_text)


def _clean_raw_fallback(raw_text: str) -> str:
    """Last-resort cleaning of raw PDF text."""
    # Remove obvious noise: page numbers, repeated headers
    lines = raw_text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip pure page numbers
        if re.match(r"^\d{1,3}$", stripped):
            continue
        # Skip very short lines that look like headers/footers
        if len(stripped) < 5 and not stripped.endswith("."):
            continue
        cleaned.append(line)
    text = "\n".join(cleaned)
    # Collapse excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:15000]  # cap at 15K chars


def batch_extract_full_text(
    papers: list[CitedPaper],
    llm_json: Callable[[str, str], str],
    *,
    batch_size: int = _BATCH_SIZE,
    batch_delay: float = _BATCH_DELAY,
) -> list[CitedPaper]:
    """Download and extract full text for cited papers.

    Parameters
    ----------
    papers:
        CitedPaper objects to process.
    llm_json:
        Callable(system_prompt, user_prompt) -> response.
    batch_size:
        Papers per batch before rate-limit pause.
    batch_delay:
        Seconds between batches.

    Returns
    -------
    list[CitedPaper]
        Same papers with full_text populated where possible.
    """
    total = len(papers)
    stats = {"extracted_llm": 0, "extracted_raw": 0, "abstract_only": 0, "skipped": 0}

    for batch_start in range(0, total, batch_size):
        batch = papers[batch_start : batch_start + batch_size]

        for paper in batch:
            cache_id = paper.arxiv_id or paper.paper_id
            cached = _load_cached(cache_id)
            if cached:
                paper.full_text = cached
                stats["extracted_llm"] += 1
                continue

            if not paper.arxiv_id:
                # No arXiv ID → use abstract
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

            # Raw extraction via pdfplumber
            raw_text = extract_text_pdfplumber(pdf_path)
            if not raw_text or len(raw_text) < 100:
                if paper.abstract:
                    paper.full_text = paper.abstract
                    _save_cache(cache_id, paper.abstract)
                    stats["abstract_only"] += 1
                else:
                    stats["skipped"] += 1
                continue

            # Agentic LLM extraction
            full_text = extract_text_llm_agentic(raw_text, llm_json)
            paper.full_text = full_text
            _save_cache(cache_id, full_text)

            if full_text == _clean_raw_fallback(raw_text):
                stats["extracted_raw"] += 1
            else:
                stats["extracted_llm"] += 1

        done = min(batch_start + batch_size, total)
        print(
            f"  [extractor] {done}/{total} processed "
            f"(llm={stats['extracted_llm']}, raw={stats['extracted_raw']}, "
            f"abstract={stats['abstract_only']}, skip={stats['skipped']})",
            file=sys.stderr,
        )

        if batch_start + batch_size < total:
            time.sleep(batch_delay)

    print(f"  [extractor] done: {stats}", file=sys.stderr)
    return papers
