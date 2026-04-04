"""Collect all cited references from a target paper via Semantic Scholar API.

Handles pagination for papers with 100+ references. Returns structured
metadata including arXiv IDs for downstream PDF fetching.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

_S2_BASE = "https://api.semanticscholar.org/graph/v1/paper"
_FIELDS = "title,abstract,year,authors,externalIds,url"
_REF_FIELDS = ",".join(f"citedPaper.{f}" for f in _FIELDS.split(","))
_PAGE_SIZE = 500  # S2 max per request for /references
_MAX_REFS = 2000  # safety ceiling
_TIMEOUT = 20
_MAX_RETRIES = 4
_RETRY_BASE = 2.0
_RETRYABLE_CODES = frozenset({429, 500, 503})

_USER_AGENT = "geo-perplexity/0.1.0 (academic-perplexity-analysis)"


@dataclass
class CitedPaper:
    """Metadata for a single cited reference."""

    paper_id: str
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    arxiv_id: str = ""
    url: str = ""
    full_text: str = ""  # populated later by text extractor
    content_source: str = ""  # "abstract", "tldr", "full_text_llm", "full_text_raw"

    @property
    def has_content(self) -> bool:
        return bool(self.full_text or self.abstract)

    @property
    def best_text(self) -> str:
        return self.full_text if self.full_text else self.abstract


def _http_get(url: str) -> dict:
    """GET with retries and exponential backoff."""
    headers = {"User-Agent": _USER_AGENT}
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code in _RETRYABLE_CODES and attempt < _MAX_RETRIES:
                delay = _RETRY_BASE * (2 ** (attempt - 1))
                print(
                    f"  [ref_collector] HTTP {exc.code}, retry {attempt}/{_MAX_RETRIES} "
                    f"in {delay:.0f}s",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BASE * (2 ** (attempt - 1))
                print(
                    f"  [ref_collector] network error ({exc}), retry {attempt}/{_MAX_RETRIES} "
                    f"in {delay:.0f}s",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue
            raise


def extract_arxiv_id(url_or_id: str) -> str:
    """Extract arXiv ID from a URL or return the ID if already bare."""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", url_or_id)
    if m:
        return m.group(1)
    m = re.match(r"^(\d{4}\.\d{4,5}(?:v\d+)?)$", url_or_id.strip())
    if m:
        return m.group(1)
    return ""


def _parse_s2_paper(raw: dict) -> Optional[CitedPaper]:
    """Parse a Semantic Scholar paper object into CitedPaper."""
    if not raw or not raw.get("title"):
        return None

    paper_id = raw.get("paperId", "")
    ext_ids = raw.get("externalIds") or {}
    arxiv_id = ext_ids.get("ArXiv", "")

    authors = []
    for a in raw.get("authors") or []:
        name = a.get("name", "")
        if name:
            authors.append(name)

    abstract = raw.get("abstract") or ""
    return CitedPaper(
        paper_id=paper_id,
        title=raw.get("title", ""),
        abstract=abstract,
        authors=authors,
        year=raw.get("year"),
        arxiv_id=arxiv_id,
        url=raw.get("url") or "",
        content_source="abstract" if abstract else "",
    )


def fetch_all_citations(
    arxiv_id: str = "",
    title: str = "",
) -> list[CitedPaper]:
    """Fetch ALL papers cited by the target paper, with pagination.

    Parameters
    ----------
    arxiv_id:
        arXiv ID of the target paper. Preferred lookup method.
    title:
        Paper title for fallback lookup if no arXiv ID.

    Returns
    -------
    list[CitedPaper]
        All cited papers found. May be 100+ entries.
    """
    s2_id = ""
    if arxiv_id:
        s2_id = f"arXiv:{arxiv_id}"
    elif title:
        s2_id = _lookup_by_title(title)

    if not s2_id:
        print("  [ref_collector] could not resolve paper ID", file=sys.stderr)
        return []

    results: dict[str, CitedPaper] = {}
    offset = 0

    while offset < _MAX_REFS:
        url = (
            f"{_S2_BASE}/{urllib.parse.quote(s2_id, safe=':')}/references"
            f"?fields={_REF_FIELDS}&offset={offset}&limit={_PAGE_SIZE}"
        )
        try:
            data = _http_get(url)
        except Exception as exc:
            print(
                f"  [ref_collector] failed to fetch references at offset {offset}: {exc}",
                file=sys.stderr,
            )
            break

        items = data.get("data") or []
        if not items:
            break

        for item in items:
            cited = item.get("citedPaper")
            if not cited:
                continue
            paper = _parse_s2_paper(cited)
            if paper and paper.paper_id and paper.paper_id not in results:
                results[paper.paper_id] = paper

        # Check if there are more pages
        next_offset = data.get("next")
        if next_offset is None or len(items) < _PAGE_SIZE:
            break
        offset = next_offset

    papers = list(results.values())
    print(
        f"  [ref_collector] fetched {len(papers)} cited references",
        file=sys.stderr,
    )

    # Back-fill abstracts from TLDR for papers that lack one
    _backfill_tldr(papers)

    return papers


def _backfill_tldr(papers: list[CitedPaper]) -> None:
    """Fetch TLDR summaries for papers missing abstracts."""
    missing = [p for p in papers if not p.abstract and p.paper_id]
    if not missing:
        return

    # Batch lookup via S2 /paper/batch endpoint (up to 500 per call)
    batch_url = f"{_S2_BASE}/batch"
    ids = [p.paper_id for p in missing]

    for chunk_start in range(0, len(ids), 500):
        chunk_ids = ids[chunk_start : chunk_start + 500]
        payload = json.dumps({"ids": chunk_ids}).encode()
        req = urllib.request.Request(
            f"{batch_url}?fields=paperId,tldr",
            data=payload,
            headers={
                "User-Agent": _USER_AGENT,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                results = json.loads(resp.read().decode())
        except Exception as exc:
            print(f"  [ref_collector] TLDR batch lookup failed: {exc}", file=sys.stderr)
            continue

        id_to_tldr = {}
        for item in results:
            if item and item.get("tldr"):
                tldr_text = item["tldr"].get("text", "")
                if tldr_text:
                    id_to_tldr[item["paperId"]] = tldr_text

        filled = 0
        for p in missing:
            if p.paper_id in id_to_tldr:
                p.abstract = id_to_tldr[p.paper_id]
                p.content_source = "tldr"
                filled += 1

        print(
            f"  [ref_collector] TLDR backfill: {filled}/{len(chunk_ids)} papers got summaries",
            file=sys.stderr,
        )


def _lookup_by_title(title: str) -> str:
    """Look up a paper's S2 ID by title search."""
    query = urllib.parse.quote(title[:200])
    url = f"{_S2_BASE}/search?query={query}&limit=1&fields=paperId"
    try:
        data = _http_get(url)
        papers = data.get("data") or []
        if papers:
            return papers[0].get("paperId", "")
    except Exception as exc:
        print(f"  [ref_collector] title lookup failed: {exc}", file=sys.stderr)
    return ""
