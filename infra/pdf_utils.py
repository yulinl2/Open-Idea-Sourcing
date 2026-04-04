"""Paper text extraction — PDF, arxiv HTML, and local cache.

Resolution priority for arxiv papers:
  1. Local cache: data/pdfs/<id>.pdf or data/pdfs/<id>.txt
  2. arxiv HTML (ar5iv.labs.arxiv.org) — preserves LaTeX math
  3. PDF download + extraction (pymupdf → pdfminer fallback)

For non-arxiv sources, falls back to direct PDF extraction.
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
    """Extract text from a paper source (PDF, URL, or arxiv ID).

    Resolution order:
      1. Local text cache: data/pdfs/<id>.txt
      2. Local PDF cache: data/pdfs/<id>.pdf
      3. arxiv HTML (ar5iv) — preserves LaTeX math notation
      4. PDF download + extraction
    Returns '' on failure.
    """
    arxiv_id = _extract_arxiv_id(str(source)) if isinstance(source, str) else None

    # 1. Check local text cache (pre-extracted, highest quality)
    if arxiv_id:
        txt_cache = _PDF_CACHE / f"{arxiv_id}.txt"
        if txt_cache.exists():
            return txt_cache.read_text(encoding="utf-8")[:max_chars]

    # 2. Check local PDF cache
    if arxiv_id:
        pdf_cache = _PDF_CACHE / f"{arxiv_id}.pdf"
        if pdf_cache.exists():
            text = _extract_text(pdf_cache, max_chars)
            if text:
                return text

    # 3. Try arxiv HTML (ar5iv) for arxiv papers — much cleaner than PDF
    if arxiv_id:
        text = _fetch_arxiv_html(arxiv_id, max_chars)
        if text:
            # Cache for future use
            try:
                _PDF_CACHE.mkdir(parents=True, exist_ok=True)
                (_PDF_CACHE / f"{arxiv_id}.txt").write_text(
                    text, encoding="utf-8")
            except OSError:
                pass
            return text

    # 4. Download PDF and extract
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


def _fetch_arxiv_html(arxiv_id: str, max_chars: int) -> str:
    """Fetch paper text from ar5iv HTML rendering.

    ar5iv renders arxiv papers as HTML with LaTeX math preserved in
    <math> tags or \\(...\\) notation, which is much cleaner than PDF
    extraction for technical content.
    """
    try:
        url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "Open-Idea-Sourcing/agent"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        return _html_to_text(html, max_chars)
    except Exception:
        return ""


def _html_to_text(html: str, max_chars: int) -> str:
    """Convert ar5iv HTML to readable text preserving math notation."""
    # Remove script, style, nav, header, footer
    html = re.sub(r"<(script|style|nav|header|footer)[^>]*>.*?</\1>",
                  "", html, flags=re.DOTALL | re.IGNORECASE)
    # Convert <math> alttext attributes to inline LaTeX
    html = re.sub(r'<math[^>]*alttext="([^"]*)"[^>]*>.*?</math>',
                  r" $\1$ ", html, flags=re.DOTALL)
    # Convert remaining math tags
    html = re.sub(r"<math[^>]*>(.*?)</math>", r" $\1$ ", html, flags=re.DOTALL)
    # Paragraphs and line breaks
    html = re.sub(r"<br\s*/?>", "\n", html)
    html = re.sub(r"</p>", "\n\n", html)
    html = re.sub(r"<h[1-6][^>]*>", "\n\n## ", html)
    html = re.sub(r"</h[1-6]>", "\n\n", html)
    # Remove all remaining tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    # Decode HTML entities
    html = html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    html = html.replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    return html.strip()[:max_chars]


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
