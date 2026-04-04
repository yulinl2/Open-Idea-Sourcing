"""PDF-to-text extraction. Pure I/O — no LLM calls."""

from __future__ import annotations

import io
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

_ALLOWED_SCHEMES = {"https"}


def extract_text_from_pdf(source: str | Path, max_chars: int = 200_000) -> str:
    """Extract text from a PDF file path or https URL. Returns '' on failure."""
    tmp_path: Path | None = None
    try:
        path = _resolve_source(source)
        tmp_path = path if (isinstance(source, str) and source.startswith("https://")) else None
        return _extract_with_pdfminer(path, max_chars)
    except Exception:
        return ""
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _resolve_source(source: str | Path) -> Path:
    if isinstance(source, Path):
        return source
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in _ALLOWED_SCHEMES:
        return _download_pdf(source)
    return Path(source)


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


def _extract_with_pdfminer(path: Path, max_chars: int) -> str:
    from pdfminer.high_level import extract_text_to_fp
    from pdfminer.layout import LAParams
    output = io.StringIO()
    with open(path, "rb") as fh:
        extract_text_to_fp(fh, output, laparams=LAParams(), output_type="text", codec="utf-8")
    return output.getvalue()[:max_chars]
