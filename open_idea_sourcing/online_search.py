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
When a set of LLM-generated conceptual queries is supplied the search
proceeds in two phases:

1. **References endpoint** — ``GET /paper/arXiv:{id}/references`` retrieves
   the papers that the submitted paper itself cites (when an arXiv ID is
   available).  These are the most directly relevant works for a novelty
   evaluation and do not depend on title-extraction quality.
2. **Conceptual keyword search** — each LLM-generated query is issued
   against the ``/paper/search`` endpoint.  Queries are derived from a
   conceptual digest of the paper (central problem, proposed strategy,
   alternative solutions) so that Semantic Scholar's semantic matching
   finds work that is *conceptually equivalent*, not merely keyword-similar.
   When no queries are supplied the raw title is used as a single fallback
   query.  When all of the above are sparse, an abstract-derived query
   is tried as a last resort.

The query-generation step is deliberately separated into
:func:`generate_search_queries` so that the search engine
(:class:`OnlineReferenceSearch`) and the query-generation logic can be
evolved or replaced independently.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from typing import Any, Callable, TYPE_CHECKING

from . import __version__
from .reference_store import ReferencePaper

if TYPE_CHECKING:
    from .novelty_evaluator import IdeaDecomposition

# Type alias for an LLM callable (matches novelty_evaluator.LLMCallable)
LLMCallable = Callable[[str], str]

# ---------------------------------------------------------------------------
# LLM-based query generation
# ---------------------------------------------------------------------------

_QUERY_GENERATION_PROMPT = """\
You are analyzing an academic paper to generate search queries for finding \
related work in Semantic Scholar.

Your task is to understand the paper at a **conceptual** level and generate \
queries that will surface papers solving the SAME PROBLEM, possibly under \
a different name, framing, or notation — not just papers that share keywords.

Based on the paper content below:
1. Identify the **central scientific or technical problem** being addressed.
2. Identify the **proposed approach or method**.
3. List **2–3 alternative approaches** that could solve the same problem.
4. Generate **4–6 short search queries** (2–6 words each) optimised for \
Semantic Scholar's semantic search.  Include queries for:
   - The core problem domain
   - The proposed method / technique
   - The alternative solution approaches

Respond with ONLY a valid JSON object in this exact format (no extra text):
{{
  "central_problem": "<one-sentence statement of the core problem>",
  "proposed_approach": "<one-sentence description of the paper's method>",
  "alternative_approaches": ["<approach 1>", "<approach 2>"],
  "queries": ["<query 1>", "<query 2>", "<query 3>", "<query 4>"]
}}

Paper content:
{content}
"""

_QUERY_GENERATION_PROMPT_WITH_DECOMP = """\
You are analyzing an academic paper to generate search queries for finding \
related work in Semantic Scholar.

A structured decomposition of the paper's core idea is provided below. \
Use it to generate queries that are conceptually precise — targeting the \
same problem space, methodology, and alternative approaches identified in \
the decomposition.

Your task is to generate **4–6 short search queries** (2–6 words each) \
optimised for Semantic Scholar's semantic search. Include queries for:
   - The core concept / central problem
   - The proposed approach derived from the decomposition
   - Alternative solution approaches to the same problem

Structured decomposition:
{decomposition_context}

Paper content:
{content}

Respond with ONLY a valid JSON object in this exact format (no extra text):
{{
  "central_problem": "<one-sentence statement of the core problem>",
  "proposed_approach": "<one-sentence description of the paper's method>",
  "alternative_approaches": ["<approach 1>", "<approach 2>"],
  "queries": ["<query 1>", "<query 2>", "<query 3>", "<query 4>"]
}}
"""

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
    f"open-idea-sourcing/{__version__} (academic novelty evaluator; "
    "https://github.com/yulinl2/Open-Idea-Sourcing)"
)


def _summarise_decomposition(decomposition: "IdeaDecomposition") -> str:
    """Compact text summary of a decomposition for query generation."""
    parts = []
    if decomposition.core_concept:
        parts.append(f"Core concept: {decomposition.core_concept}")
    if decomposition.sub_ideas:
        parts.append("Key components: " + "; ".join(decomposition.sub_ideas[:5]))
    return "\n".join(parts)


def generate_search_queries(
    paper_content: str,
    llm: LLMCallable,
    *,
    max_queries: int = 6,
    decomposition: "IdeaDecomposition | None" = None,
) -> list[str]:
    """Ask an LLM to generate conceptual search queries for a paper.

    The LLM is asked to identify the paper's central problem, proposed
    approach, and alternative solutions, then produce short queries
    optimised for Semantic Scholar's semantic search.  This surfaces
    work that is *conceptually equivalent* — same problem, different name
    or framing — rather than just keyword-similar papers.

    Parameters
    ----------
    paper_content:
        Textual content of the paper (e.g. ``paper.key_content()``).
    llm:
        Callable that accepts a prompt string and returns the LLM response.
    max_queries:
        Maximum number of queries to return (excess are silently dropped).
    decomposition:
        Optional pre-computed :class:`~.novelty_evaluator.IdeaDecomposition`
        from Stage 2.  When provided and has a ``core_concept``, the
        decomposition-aware prompt is used so that queries are derived from
        the structured concept tree rather than the raw paper text alone.
        Falls back to the standard prompt when *None* (backward compatible).

    Returns
    -------
    list[str]
        List of short query strings.  Returns an empty list on any error
        (LLM failure, malformed response, etc.) so that callers can fall
        back to title-based search gracefully.
    """
    if decomposition is not None and decomposition.core_concept:
        prompt = _QUERY_GENERATION_PROMPT_WITH_DECOMP.format(
            decomposition_context=_summarise_decomposition(decomposition),
            content=paper_content,
        )
    else:
        prompt = _QUERY_GENERATION_PROMPT.format(content=paper_content)
    try:
        response = llm(prompt)
    except Exception as exc:  # noqa: BLE001
        print(
            f"  [online_search] query generation failed: {exc}",
            file=sys.stderr,
        )
        return []

    raw = response.strip()

    # Strip possible ```json ... ``` fences that some models add.
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\n?```$", "", raw.strip())

    # Parse the JSON response.
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract a JSON object embedded in the response.
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return []
        try:
            data = json.loads(m.group())
        except json.JSONDecodeError:
            return []

    queries = data.get("queries") or []
    if not isinstance(queries, list):
        return []
    return [str(q).strip() for q in queries if str(q).strip()][:max_queries]


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
        self._last_errors: list[str] = []

    @property
    def last_errors(self) -> list[str]:
        """HTTP or parse errors collected during the most recent :meth:`search` call.

        Each entry is a short human-readable string (e.g.
        ``"references: HTTP 429 Too Many Requests"``).  The list is cleared at
        the start of every :meth:`search` call.  Callers can inspect this to
        surface rate-limit or network problems in the pipeline job log.
        """
        return list(self._last_errors)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        title: str,
        abstract: str = "",
        arxiv_id: str = "",
        queries: list[str] | None = None,
    ) -> list[ReferencePaper]:
        """Return papers related to the submitted paper.

        Strategy
        --------
        1. **arXiv references** (when *arxiv_id* is given): fetch the paper's
           reference list from Semantic Scholar's ``/paper/arXiv:{id}/references``
           endpoint.  These are the papers the authors cited — depth signal for
           detecting duplicates and near-equivalent prior work.
        2. **Conceptual keyword search** (breadth): when LLM-generated *queries*
           are provided, each query is issued independently against
           ``/paper/search``; results are merged.  This surfaces work that is
           conceptually equivalent to the submitted paper even when the wording
           differs.  When *queries* is *None* or empty, the raw *title* is used
           as a single fallback query.
        3. **Abstract fallback** (when both above are sparse): an additional
           keyword query derived from the opening of *abstract*.

        All network and parsing errors are swallowed; on failure the method
        returns whatever partial results have been collected so far.

        Parameters
        ----------
        title:
            Title of the paper being evaluated.
        abstract:
            Abstract text used as a last-resort fallback query.  May be empty.
        arxiv_id:
            arXiv identifier (e.g. ``"2006.06138"``).  When supplied,
            the references endpoint runs in addition to keyword queries.
        queries:
            LLM-generated conceptual queries (from :func:`generate_search_queries`).
            When provided these replace the title-based keyword search.

        Returns
        -------
        list[ReferencePaper]
            Deduplicated list of reference papers (references first,
            then keyword matches), capped at *max_results*.
        """
        results: dict[str, ReferencePaper] = {}
        self._last_errors = []

        # Phase 1: paper-specific references (depth — papers the authors cited).
        if arxiv_id:
            for paper in self._fetch_references(f"arXiv:{arxiv_id}"):
                results[paper.id] = paper

        # Phase 2: conceptual keyword search (breadth).
        # Use LLM-generated queries when available; fall back to the raw title.
        search_queries = queries if queries else ([title] if title else [])
        for q in search_queries:
            for paper in self._query(q):
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
        # RFC 3986 allows colons in URI path segments unencoded; Semantic
        # Scholar's paper-lookup endpoint expects the literal "arXiv:XXXX.XXXXX"
        # form in the path (e.g. /paper/arXiv:2006.06138/references).
        paper_id_encoded = urllib.parse.quote(semantic_paper_id, safe=":")
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
            err_msg = f"references: {exc}"
            self._last_errors.append(err_msg)
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
        except Exception as exc:
            self._last_errors.append(f"query '{query[:40]}': {exc}")
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
