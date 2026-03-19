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

Search strategy
---------------
When an arXiv ID is supplied the search proceeds in two phases:

1. **References endpoint** — ``GET /paper/arXiv:{id}/references`` retrieves
   the papers that the submitted paper itself cites.  These are the most
   directly relevant works for a novelty evaluation and do not depend on
   title-extraction quality.
2. **Keyword fallback** — if the references list is sparse (or no arXiv ID
   is available), a keyword query built from the paper title is issued
   against the ``/paper/search`` endpoint.  When that is also sparse,
   a second query derived from the opening of the abstract is tried.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from typing import Any

from .reference_store import ReferencePaper

_SEMANTIC_SCHOLAR_PAPER_URL = (
    "https://api.semanticscholar.org/graph/v1/paper"
)
_SEMANTIC_SCHOLAR_SEARCH_URL = (
    "https://api.semanticscholar.org/graph/v1/paper/search"
)
_FIELDS = "title,abstract,year,authors,externalIds,url"
# For the /references endpoint each field must be prefixed with "citedPaper."
_REFERENCE_FIELDS = ",".join(f"citedPaper.{f}" for f in _FIELDS.split(","))
_DEFAULT_LIMIT = 10
_DEFAULT_TIMEOUT = 15  # seconds

_USER_AGENT = (
    "open-idea-sourcing/1.0 (academic novelty evaluator; "
    "https://github.com/yulinl2/Open-Idea-Sourcing)"
)


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

    def search(
        self, title: str, abstract: str = "", arxiv_id: str = ""
    ) -> list[ReferencePaper]:
        """Return papers related to the submitted paper.

        Strategy
        --------
        Both queries run in parallel and their results are merged:

        1. **arXiv references** (when *arxiv_id* is given): fetch the paper's
           reference list from Semantic Scholar's ``/paper/arXiv:{id}/references``
           endpoint.  These are the papers the authors cited — depth signal for
           detecting duplicates and near-equivalent prior work.
        2. **Keyword search** (always): query ``/paper/search`` with the paper
           title for broader field discovery — finds topically related work that
           the authors may not have cited.  Semantic Scholar's semantic matching
           works well with short topic-level queries ("Conformal Inference",
           "diffusion models"), surfacing subtly equivalent work across the field.
        3. **Abstract fallback** (when both above are sparse): an additional
           keyword query derived from the opening of *abstract* for higher recall.

        All network and parsing errors are swallowed; on failure the method
        returns whatever partial results have been collected so far.

        Parameters
        ----------
        title:
            Title of the paper being evaluated.
        abstract:
            Abstract text used as a third-pass fallback query.  May be empty.
        arxiv_id:
            arXiv identifier (e.g. ``"2006.06138"``).  When supplied,
            the references endpoint runs in addition to keyword search.

        Returns
        -------
        list[ReferencePaper]
            Deduplicated list of reference papers (references first,
            then keyword matches), capped at *max_results*.
        """
        results: dict[str, ReferencePaper] = {}

        # Phase 1: paper-specific references (depth — papers the authors cited).
        if arxiv_id:
            for paper in self._fetch_references(f"arXiv:{arxiv_id}"):
                results[paper.id] = paper

        # Phase 2: keyword search (breadth — broader field / topic discovery).
        # Runs always, not just as a fallback, because it finds related work the
        # authors may not have cited (subtly equivalent work, parallel efforts).
        if title:
            for paper in self._query(title):
                results.setdefault(paper.id, paper)

        # Phase 3: abstract fallback when both above are sparse.
        if len(results) < max(1, self._max_results // 2) and abstract:
            fallback_query = _extract_query_from_abstract(abstract)
            if fallback_query:
                for paper in self._query(fallback_query):
                        results.setdefault(paper.id, paper)

        return list(results.values())[: self._max_results]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_references(self, semantic_paper_id: str) -> list[ReferencePaper]:
        """Return references of a paper using Semantic Scholar's references endpoint.

        Parameters
        ----------
        semantic_paper_id:
            Semantic Scholar paper identifier.  Use ``"arXiv:XXXX.XXXXX"`` for
            arXiv papers.  Other formats (e.g. bare S2 paper hash) also work.
        """
        paper_id_encoded = urllib.parse.quote(semantic_paper_id, safe="")
        params = urllib.parse.urlencode(
            {
                "fields": _REFERENCE_FIELDS,
                "limit": self._max_results,
            }
        )
        url = f"{_SEMANTIC_SCHOLAR_PAPER_URL}/{paper_id_encoded}/references?{params}"
        req = urllib.request.Request(
            url, headers={"User-Agent": _USER_AGENT}
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                raw = resp.read()
        except Exception as exc:
            print(
                f"  [online_search] references request failed: {exc}",
                file=sys.stderr,
            )
            return []
        try:
            data: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            return []

        papers: list[ReferencePaper] = []
        for item in data.get("data", []):
            cited = item.get("citedPaper") or {}
            paper = _parse_semantic_scholar_item(cited)
            if paper is not None:
                papers.append(paper)
        return papers

    def _query(self, query: str) -> list[ReferencePaper]:
        """Send one keyword query to Semantic Scholar; return parsed papers."""
        params = urllib.parse.urlencode(
            {
                "query": query,
                "fields": _FIELDS,
                "limit": self._max_results,
            }
        )
        url = f"{_SEMANTIC_SCHOLAR_SEARCH_URL}?{params}"
        req = urllib.request.Request(
            url, headers={"User-Agent": _USER_AGENT}
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
