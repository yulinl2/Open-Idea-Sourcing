"""
infra/pdf_utils.py

PDF-to-text extraction wrapper.

Pure I/O — no LLM calls, no agent logic. Accepts a file path or URL and returns
the extracted text as a string. Falls back gracefully when extraction fails,
including download failures.

Dependencies:
  - pdfminer.six (listed in requirements.txt)

For URL inputs, the PDF is downloaded to a temporary file before extraction.
Only https:// URLs are accepted to prevent SSRF.
"""

from __future__ import annotations

import io
import os
import tempfile
import urllib.request
import urllib.parse
from pathlib import Path

# Allowed URL schemes for PDF download (block http:// to reduce redirect risk)
_ALLOWED_SCHEMES = {"https"}


def extract_text_from_pdf(source: str | Path, max_chars: int = 200_000) -> str:
    """
    Extract text from a PDF file or URL.

    Args:
        source: A local file path (str or Path) or an https:// URL.
        max_chars: Maximum characters to return (avoids runaway memory on large PDFs).

    Returns:
        Extracted text as a string. Returns an empty string if extraction fails
        (including download failures, import errors, and corrupt PDFs).
    """
    tmp_path: Path | None = None
    try:
        path = _resolve_source(source)
        tmp_path = path if (isinstance(source, str) and source.startswith("https://")) else None
        return _extract_with_pdfminer(path, max_chars)
    except ImportError:
        # pdfminer.six not installed — return empty string so callers can
        # fall back to abstract-only mode
        return ""
    except Exception as exc:  # noqa: BLE001
        # Any failure (download error, corrupt PDF, etc.) — warn and return empty
        import warnings
        warnings.warn(f"PDF extraction failed for {source}: {exc}", RuntimeWarning, stacklevel=2)
        return ""
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _resolve_source(source: str | Path) -> Path:
    """Return a local Path, downloading the PDF if source is an https:// URL."""
    if isinstance(source, Path):
        return source
    if isinstance(source, str):
        parsed = urllib.parse.urlparse(source)
        if parsed.scheme in _ALLOWED_SCHEMES:
            return _download_pdf(source)
        if parsed.scheme:
            raise ValueError(
                f"Unsupported URL scheme '{parsed.scheme}': only https:// is allowed."
            )
    return Path(source)


def _download_pdf(url: str) -> Path:
    """Download a PDF from an https:// URL to a temporary file and return its path."""
    # Validate scheme once more inside the downloader (defence in depth)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Refusing to download from non-https URL: {url}")

    # Convert arXiv abstract URLs to PDF URLs
    url = _coerce_arxiv_pdf_url(url)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Open-Idea-Sourcing/infra (research tool)"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        data = resp.read()
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(data)
    tmp.close()
    return Path(tmp.name)


def _coerce_arxiv_pdf_url(url: str) -> str:
    """
    Convert an arXiv abstract URL to a PDF download URL.
    e.g. https://arxiv.org/abs/2006.06138 → https://arxiv.org/pdf/2006.06138
    """
    if "arxiv.org/abs/" in url:
        return url.replace("arxiv.org/abs/", "arxiv.org/pdf/")
    return url


def _extract_with_pdfminer(path: Path, max_chars: int) -> str:
    """Extract text using pdfminer.six."""
    from pdfminer.high_level import extract_text_to_fp
    from pdfminer.layout import LAParams

    output = io.StringIO()
    with open(path, "rb") as fh:
        extract_text_to_fp(fh, output, laparams=LAParams(), output_type="text", codec="utf-8")
    text = output.getvalue()
    return text[:max_chars]
