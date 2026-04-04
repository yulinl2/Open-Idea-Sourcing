"""PDF-to-text extraction. Pure I/O — no LLM calls.

Supports local files, URLs, and arxiv paper IDs (looks up local cache first).
Uses pymupdf (fitz) for extraction, falls back to pdfminer.six.
"""

from __future__ import annotations

import os
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

_ALLOWED_SCHEMES = {"https"}
_SCRIPT_DIR = Path(__file__).parent.parent
_PDF_CACHE = _SCRIPT_DIR / "data" / "pdfs"


def extract_text_from_pdf(source: str | Path, max_chars: int = 200_000) -> str:
    """Extract text from a PDF file path, https URL, or arxiv ID.

    Resolution order:
      1. If source is a local file path → use directly
      2. If source contains an arxiv ID → check data/pdfs/<id>.pdf cache
      3. If source is a URL → download to temp file
    Returns '' on failure.
    """
    tmp_path: Path | None = None
    try:
        path, tmp_path = _resolve_source(source)
        return _extract_text(path, max_chars)
    except Exception:
        return ""
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _resolve_source(source: str | Path) -> tuple[Path, Path | None]:
    """Resolve source to (pdf_path, tmp_path_or_None)."""
    if isinstance(source, Path):
        return source, None
    # Check local PDF cache by arxiv ID
    arxiv_id = _extract_arxiv_id(source)
    if arxiv_id:
        cached = _PDF_CACHE / f"{arxiv_id}.pdf"
        if cached.exists():
            return cached, None
    # Local file path
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return Path(source), None
    # URL download
    tmp = _download_pdf(source)
    return tmp, tmp


def _extract_arxiv_id(source: str) -> str | None:
    m = re.search(r"(\d{4}\.\d{4,5})", source)
    return m.group(1) if m else None


def _download_pdf(url: str) -> Path:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Refusing non-https URL: {url}")
    if "arxiv.org/abs/" in url:
        url = url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
    req = urllib.request.Request(url, headers={"User-Agent": "Open-Idea-Sourcing/agent"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(data)
    tmp.close()
    return Path(tmp.name)


def _extract_text(path: Path, max_chars: int) -> str:
    """Try pymupdf first, fall back to pdfminer."""
    text = _extract_with_pymupdf(path, max_chars)
    if text:
        return text
    return _extract_with_pdfminer(path, max_chars)


def _extract_with_pymupdf(path: Path, max_chars: int) -> str:
    try:
        import pymupdf
        doc = pymupdf.open(str(path))
        parts = []
        total = 0
        for page in doc:
            t = page.get_text()
            parts.append(t)
            total += len(t)
            if total >= max_chars:
                break
        return "".join(parts)[:max_chars]
    except Exception:
        return ""


def _extract_with_pdfminer(path: Path, max_chars: int) -> str:
    try:
        import io
        from pdfminer.high_level import extract_text_to_fp
        from pdfminer.layout import LAParams
        output = io.StringIO()
        with open(path, "rb") as fh:
            extract_text_to_fp(fh, output, laparams=LAParams(),
                               output_type="text", codec="utf-8")
        return output.getvalue()[:max_chars]
    except Exception:
        return ""
