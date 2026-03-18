"""Online academic reference search via the Semantic Scholar public API.

Queries the `Semantic Scholar Graph API
<https://api.semanticscholar.org/graph/v1/paper/search>`_ to discover
papers related to a submitted paper.  The results are returned as
:class:`~.reference_store.ReferencePaper` objects so they can be fed
directly into the existing :class:`~.similarity_search.SimilaritySearch`
pipeline.

No API key is required for basic usage.  The public endpoint permits
approximately 100 unauthenticated requests per 5 minutes, which is more
than sufficient for interactive use.  All network errors are caught and
cause an empty list to be returned so that the broader evaluation pipeline
degrades gracefully when the internet is unavailable.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from .reference_store import ReferencePaper

_SEMANTIC_SCHOLAR_SEARCH_URL = (
    "https://api.semanticscholar.org/graph/v1/paper/search"
)
_FIELDS = "title,abstract,year,authors,externalIds,url"
_DEFAULT_LIMIT = 10
_DEFAULT_TIMEOUT = 15  # seconds


class OnlineReferenceSearch:
    """Fetch related papers from the Semantic Scholar public API.

    Parameters
    ----------
    max_results:
        Maximum number of papers to retrieve per search call.  The
        actual number returned may be lower if the API returns fewer
        matches or if network errors occur.
    timeout:
        HTTP request timeout in seconds.  Requests that exceed this
        duration are silently abandoned and an empty result set is
        returned.
    """

    def __init__(
        self,
        max_results: int = _DEFAULT_LIMIT,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        self._max_results = max_results
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, title: str, abstract: str = "") -> list[ReferencePaper]:
        """Search Semantic Scholar for papers related to *title*.

        Strategy
        --------
        1. Query with the paper title (high precision).
        2. If fewer than ``max_results // 2`` papers are returned, also
           query with the opening terms of *abstract* (higher recall) and
           merge any new results.

        All network and parsing errors are swallowed; on failure the
        method returns whatever partial results have been collected so far
        (possibly an empty list).

        Parameters
        ----------
        title:
            Title of the paper being evaluated.
        abstract:
            Abstract text used as a fallback query when the title search
            returns few results.  May be empty.

        Returns
        -------
        list[ReferencePaper]
            Deduplicated list of reference papers ordered by the API's
            relevance ranking.
        """
        results: dict[str, ReferencePaper] = {}

        for paper in self._query(title):
            results[paper.id] = paper

        # Fallback: augment with abstract-based query when primary is sparse.
        if len(results) < max(1, self._max_results // 2) and abstract:
            fallback_query = _extract_query_from_abstract(abstract)
            if fallback_query:
                for paper in self._query(fallback_query):
                    results.setdefault(paper.id, paper)

        return list(results.values())[: self._max_results]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _query(self, query: str) -> list[ReferencePaper]:
        """Send one query to Semantic Scholar; return parsed papers."""
        params = urllib.parse.urlencode(
            {
                "query": query,
                "fields": _FIELDS,
                "limit": self._max_results,
            }
        )
        url = f"{_SEMANTIC_SCHOLAR_SEARCH_URL}?{params}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "open-idea-sourcing/1.0 (academic novelty evaluator; "
                    "https://github.com/yulinl2/Open-Idea-Sourcing)"
                ),
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                raw = resp.read()
        except Exception:
            return []
        try:
            data: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            return []

        papers: list[ReferencePaper] = []
        for item in data.get("data", []):
            paper = _parse_semantic_scholar_item(item)
            if paper is not None:
                papers.append(paper)
        return papers


# ---------------------------------------------------------------------------
# Module-level helpers (also exported for testing)
# ---------------------------------------------------------------------------


def _extract_query_from_abstract(abstract: str, max_words: int = 15) -> str:
    """Return a short query string derived from the opening of *abstract*.

    Takes up to *max_words* words from the start of *abstract* so that
    the Semantic Scholar search stays focused and does not time out.
    """
    words = abstract.split()
    return " ".join(words[:max_words])


def _parse_semantic_scholar_item(item: dict[str, Any]) -> ReferencePaper | None:
    """Convert one Semantic Scholar ``data`` entry to a :class:`ReferencePaper`.

    Returns *None* when essential fields (``paperId`` or ``title``) are
    missing so that the caller can simply skip the item.
    """
    paper_id: str | None = item.get("paperId")
    title: str = (item.get("title") or "").strip()
    if not paper_id or not title:
        return None

    abstract: str = (item.get("abstract") or "").strip()
    year_raw = item.get("year")
    year: int | None = int(year_raw) if isinstance(year_raw, int) else None

    authors: list[str] = [
        a.get("name", "")
        for a in (item.get("authors") or [])
        if a.get("name")
    ]

    external_ids: dict[str, str] = item.get("externalIds") or {}
    arxiv_id: str = external_ids.get("ArXiv", "")
    url: str = item.get("url") or (
        f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
    )

    return ReferencePaper(
        id=paper_id,
        title=title,
        abstract=abstract,
        authors=authors,
        year=year,
        url=url,
    )
