"""
infra/search_tools.py

LAST-RESORT FALLBACK — use only when the model's native web_search tool is
unavailable or when structured S2 metadata (canonical paper IDs, citation
counts, author lists) is specifically needed.

For general literature discovery, prefer the model's built-in web_search tool
and let the agent decide its own search strategy.

Thin clients for Semantic Scholar and arXiv.

These are pure I/O functions — no LLM calls, no agent logic.
They return structured dicts that agent tracks can process as needed.

Semantic Scholar API docs: https://api.semanticscholar.org/api-docs/
arXiv API docs: https://arxiv.org/help/api/user-manual
"""

from __future__ import annotations

import time
import urllib.parse
import urllib.request
import json
from typing import Any


# ---------------------------------------------------------------------------
# Semantic Scholar
# ---------------------------------------------------------------------------

S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_PAPER_URL = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
S2_CITATIONS_URL = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"

S2_FIELDS = "paperId,title,year,authors,abstract,publicationDate,externalIds"
S2_RATE_LIMIT_DELAY = 1.0          # seconds between requests (unauthenticated tier)
S2_RATE_LIMIT_RETRY_MULTIPLIER = 3  # backoff multiplier on 429 retry


def _s2_get(url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    """Make a GET request to the Semantic Scholar API and return parsed JSON.

    Raises urllib.error.HTTPError directly so callers can inspect the status code
    (e.g. to retry on 429 rate-limit responses).
    """
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError:
        raise  # re-raise so callers can check exc.code (e.g. 429)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Semantic Scholar network error for {url}: {exc.reason}") from exc


def search_semantic_scholar(
    query: str,
    limit: int = 10,
    fields: str = S2_FIELDS,
    retry_on_429: bool = True,
) -> list[dict[str, Any]]:
    """
    Search Semantic Scholar by keyword query.

    Returns a list of paper dicts, each with at least:
      paperId, title, year, authors, abstract, externalIds
    """
    params = {"query": query, "limit": str(limit), "fields": fields}
    try:
        data = _s2_get(S2_SEARCH_URL, params)
        return data.get("data", [])
    except urllib.error.HTTPError as exc:
        if exc.code == 429 and retry_on_429:
            time.sleep(S2_RATE_LIMIT_DELAY * S2_RATE_LIMIT_RETRY_MULTIPLIER)
            data = _s2_get(S2_SEARCH_URL, params)
            return data.get("data", [])
        raise RuntimeError(
            f"Semantic Scholar API error {exc.code} for search '{query}': {exc.reason}"
        ) from exc


def fetch_s2_citations(
    paper_id: str,
    limit: int = 50,
    fields: str = S2_FIELDS,
) -> list[dict[str, Any]]:
    """
    Fetch the papers that cite the given Semantic Scholar paper_id.

    paper_id may be an S2 paperId, arXiv ID (e.g. "2006.06138"),
    or DOI prefixed with "DOI:".

    Returns a list of citing paper dicts.
    """
    url = S2_CITATIONS_URL.format(paper_id=urllib.parse.quote(paper_id, safe=""))
    params = {"limit": str(limit), "fields": fields}
    data = _s2_get(url, params)
    return [entry.get("citingPaper", {}) for entry in data.get("data", [])]


def fetch_s2_paper(paper_id: str, fields: str = S2_FIELDS) -> dict[str, Any]:
    """
    Fetch metadata for a single paper by Semantic Scholar paperId or arXiv ID.
    """
    url = S2_PAPER_URL.format(paper_id=urllib.parse.quote(paper_id, safe=""))
    params = {"fields": fields}
    return _s2_get(url, params)


# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------

ARXIV_SEARCH_URL = "https://export.arxiv.org/api/query"


def search_arxiv(
    query: str,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """
    Search arXiv using the public API.

    Returns a list of paper dicts with keys:
      arxiv_id, title, summary (abstract), authors, published
    """
    params = {
        "search_query": query,
        "max_results": str(max_results),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = ARXIV_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/atom+xml"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml = resp.read().decode("utf-8")
    return _parse_arxiv_atom(xml)


def _parse_arxiv_atom(xml: str) -> list[dict[str, Any]]:
    """Parse arXiv Atom feed XML into a list of paper dicts."""
    import xml.etree.ElementTree as ET

    NS = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(xml)
    papers = []
    for entry in root.findall("atom:entry", NS):
        id_text = (entry.findtext("atom:id", "", NS) or "").strip()
        arxiv_id = id_text.split("/abs/")[-1].split("v")[0] if "/abs/" in id_text else id_text
        title_el = entry.find("atom:title", NS)
        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""
        summary_el = entry.find("atom:summary", NS)
        summary = (summary_el.text or "").strip() if summary_el is not None else ""
        published_el = entry.find("atom:published", NS)
        published = (published_el.text or "").strip() if published_el is not None else ""
        authors = [
            (a.findtext("atom:name", "", NS) or "").strip()
            for a in entry.findall("atom:author", NS)
        ]
        papers.append(
            {
                "arxiv_id": arxiv_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "published": published,
            }
        )
    return papers
