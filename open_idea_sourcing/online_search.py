"""Online reference search using the Semantic Scholar public API.

No API key is required.  Searches are rate-limited by the upstream service
(roughly 1 request/second on the free public tier).

Example usage::

    from open_idea_sourcing.online_search import OnlineReferenceSearch

    searcher = OnlineReferenceSearch()
    papers = searcher.search("attention mechanisms in transformers", max_results=5)
    for p in papers:
        print(p.title, p.url)
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from .reference_store import ReferencePaper

_SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
_DEFAULT_FIELDS = "title,abstract,year,authors,url,externalIds"
_USER_AGENT = (
    "open-idea-sourcing/1.0 (https://github.com/yulinl2/Open-Idea-Sourcing)"
)
_REQUEST_TIMEOUT = 15  # seconds


class OnlineReferenceSearch:
    """Search for academic papers using the Semantic Scholar public API.

    Parameters
    ----------
    rate_limit_delay:
        Minimum number of seconds to wait between successive API calls to
        stay within the public tier rate limit (default: 1.0 s).
    """

    def __init__(self, rate_limit_delay: float = 1.0) -> None:
        self._rate_limit_delay = rate_limit_delay
        self._last_request_time: float = 0.0

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[ReferencePaper]:
        """Search Semantic Scholar for papers matching *query*.

        Parameters
        ----------
        query:
            Free-form search query (e.g. ``"attention mechanisms transformers"``).
        max_results:
            Maximum number of papers to return.  Capped at 10 to stay within
            the recommended page size for the public API tier.

        Returns
        -------
        list[ReferencePaper]
            Papers found, in relevance order.  Returns an empty list when
            the API is unavailable or returns no usable results.
        """
        if not query.strip():
            return []

        max_results = max(1, min(max_results, 10))
        self._throttle()

        params = urllib.parse.urlencode({
            "query": query.strip(),
            "fields": _DEFAULT_FIELDS,
            "limit": max_results,
        })
        url = f"{_SEMANTIC_SCHOLAR_URL}?{params}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": _USER_AGENT},
        )

        try:
            with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            return []

        papers: list[ReferencePaper] = []
        for item in raw.get("data", []):
            paper = self._parse_paper(item)
            if paper is not None:
                papers.append(paper)
        return papers

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _throttle(self) -> None:
        """Sleep if needed to respect the configured rate limit."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.monotonic()

    @staticmethod
    def _parse_paper(item: dict) -> Optional[ReferencePaper]:
        """Convert a Semantic Scholar API result object to a :class:`ReferencePaper`."""
        paper_id = item.get("paperId") or (
            item.get("externalIds") or {}
        ).get("DOI", "")
        if not paper_id:
            return None

        title = (item.get("title") or "").strip()
        abstract = (item.get("abstract") or "").strip()
        year = item.get("year")
        authors = [
            a.get("name", "")
            for a in item.get("authors", [])
            if a.get("name")
        ]
        url = item.get("url") or ""
        if not url and item.get("paperId"):
            url = f"https://www.semanticscholar.org/paper/{item['paperId']}"

        return ReferencePaper(
            id=paper_id,
            title=title,
            abstract=abstract,
            authors=authors,
            year=int(year) if year else None,
            url=url,
        )
