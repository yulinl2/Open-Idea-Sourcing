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
import time as _time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from . import __version__
from .reference_store import ReferencePaper

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
_MAX_RETRIES = 4
_RETRY_BASE_DELAY = 2.0  # seconds; doubles on each attempt
_RETRY_429_MIN_DELAY = 60.0  # minimum wait after a 429 (rate-limit) response
_RETRYABLE_HTTP_CODES = frozenset({429, 500, 503})
# Maximum number of cited references to fetch per paper from the /references
# endpoint.  The paper-cited reference list should not be capped at top_k * 2
# (which is the keyword-search max_results); a paper may have 100+ references.
_MAX_CITED_REFS_LIMIT = 500
# Maximum results per keyword-search request to the S2 /paper/search endpoint.
# The S2 API accepts up to 100 per page.  Fetching the full page gives the
# caller a richer pool before deduplication across multiple queries.
_MAX_KEYWORD_SEARCH_LIMIT = 100

_USER_AGENT = (
    f"open-idea-sourcing/{__version__} (academic novelty evaluator; "
    "https://github.com/yulinl2/Open-Idea-Sourcing)"
)


def generate_search_queries(
    paper_content: str,
    llm: LLMCallable,
    *,
    max_queries: int = 6,
    decomposition: object = None,
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

    Returns
    -------
    list[str]
        List of short query strings.  Returns an empty list on any error
        (LLM failure, malformed response, etc.) so that callers can fall
        back to title-based search gracefully.
    """
    decomp_hint = ""
    if decomposition is not None:
        from .novelty_evaluator import _format_decomp_context
        decomp_hint = "\n\nIDEA DECOMPOSITION:\n" + _format_decomp_context(decomposition)
    prompt = _QUERY_GENERATION_PROMPT.format(
        content=paper_content + decomp_hint
    )
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
    min_year:
        Earliest publication year to include (inclusive).  Papers older
        than this year are filtered out both via the API ``year`` parameter
        and client-side.
    max_year:
        Latest publication year to include (inclusive).  Papers published
        after this year are filtered out, which prevents works that are
        contemporaneous with or newer than the submitted paper from being
        included in the prior-art pool.  Pass the submitted paper's own
        publication year to enforce this cutoff automatically.
    """

    def __init__(
        self,
        max_results: int = _DEFAULT_LIMIT,
        timeout: int = _DEFAULT_TIMEOUT,
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> None:
        self._max_results = max_results
        self._timeout = timeout
        self._min_year = min_year
        self._max_year = max_year
        self._last_errors: list[str] = []
        self._last_query_counts: dict[str, int] = {}

    @property
    def last_errors(self) -> list[str]:
        """HTTP or parse errors collected during the most recent :meth:`search` call.

        Each entry is a short human-readable string (e.g.
        ``"references: HTTP 429 Too Many Requests"``).  The list is cleared at
        the start of every :meth:`search` call.  Callers can inspect this to
        surface rate-limit or network problems in the pipeline job log.
        """
        return list(self._last_errors)

    @property
    def last_query_counts(self) -> dict[str, int]:
        """Per-query raw hit counts from the most recent :meth:`search` call.

        Maps each query string to the number of papers returned by Semantic
        Scholar for that query *before* deduplication across queries.  Useful
        for pipeline audit — a count of zero indicates the query was too
        specific or returned no results.  Cleared at the start of every
        :meth:`search` call.
        """
        return dict(self._last_query_counts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_citations(
        self,
        title: str = "",
        arxiv_id: str = "",
    ) -> list[ReferencePaper]:
        """Fetch papers cited by the submitted paper (Phase 1 — depth signal).

        For arXiv papers, uses the dedicated ``/paper/arXiv:{id}/references``
        endpoint.  For non-arXiv papers, falls back to a Semantic Scholar
        title lookup to find the S2 paper ID so the references endpoint can
        still be called.  Returns an empty list when neither identifier can be
        resolved.

        Parameters
        ----------
        title:
            Title of the paper (used for non-arXiv title-lookup fallback).
        arxiv_id:
            arXiv identifier (e.g. ``"2006.06138"``).  When supplied, the arXiv
            endpoint is used directly without a title lookup.

        Returns
        -------
        list[ReferencePaper]
            All papers found in the reference list of the submitted paper.
            Not capped at *max_results* — callers receive the full citation list.
        """
        self._last_errors = []
        results: dict[str, ReferencePaper] = {}
        if arxiv_id:
            for paper in self._fetch_references(f"arXiv:{arxiv_id}"):
                results[paper.id] = paper
        elif title:
            s2_id = self._lookup_paper_id_by_title(title)
            if s2_id:
                for paper in self._fetch_references(s2_id):
                    results[paper.id] = paper
        return list(results.values())

    def search(
        self,
        title: str,
        abstract: str = "",
        queries: list[str] | None = None,
    ) -> list[ReferencePaper]:
        """Return papers related to the submitted paper via keyword search.

        Performs conceptual/keyword search only (Phase 2 + Phase 3).  To also
        load papers cited by the submitted paper, call :meth:`fetch_citations`
        separately so each group can be stored with its own provenance tag.

        Strategy
        --------
        1. **Conceptual keyword search** (breadth): when LLM-generated *queries*
           are provided, each query is issued independently against
           ``/paper/search``; results are merged.  This surfaces work that is
           conceptually equivalent to the submitted paper even when the wording
           differs.  When *queries* is *None* or empty, the raw *title* is used
           as a single fallback query.
        2. **Abstract fallback** (when above is sparse): an additional keyword
           query derived from the opening of *abstract*.

        All network and parsing errors are swallowed; on failure the method
        returns whatever partial results have been collected so far.

        Parameters
        ----------
        title:
            Title of the paper being evaluated (used as fallback query when
            *queries* is empty).
        abstract:
            Abstract text used as a last-resort fallback query.  May be empty.
        queries:
            LLM-generated conceptual queries (from :func:`generate_search_queries`).
            When provided these replace the title-based keyword search.

        Returns
        -------
        list[ReferencePaper]
            Deduplicated list of keyword-matched papers (all unique hits across
            all queries, without an artificial cap).
        """
        results: dict[str, ReferencePaper] = {}
        self._last_errors = []
        self._last_query_counts = {}

        # Phase 2: conceptual keyword search (breadth).
        # Use LLM-generated queries when available; fall back to the raw title.
        search_queries = queries if queries else ([title] if title else [])
        for q in search_queries:
            hits = self._query(q)
            self._last_query_counts[q] = len(hits)
            for paper in hits:
                results.setdefault(paper.id, paper)

        # Phase 3: abstract fallback when keyword search is sparse.
        if len(results) < max(1, self._max_results // 2) and abstract:
            fallback_query = _extract_query_from_abstract(abstract)
            if fallback_query:
                hits = self._query(fallback_query)
                self._last_query_counts[fallback_query] = len(hits)
                for paper in hits:
                    results.setdefault(paper.id, paper)

        return list(results.values())

    def lookup_domain_refs(
        self, domain_refs: list,  # list[DomainReference]
    ) -> list:  # list[ReferencePaper]
        """Look up domain reference papers by title via Semantic Scholar.

        For each domain reference identified by the LLM, issues a title-based
        search to Semantic Scholar to resolve it to a concrete paper with
        abstract and year.  Papers that cannot be found are silently skipped.

        Parameters
        ----------
        domain_refs:
            DomainReference objects from the LLM domain-reference finder.

        Returns
        -------
        list[ReferencePaper]
            Resolved reference papers.  May be shorter than *domain_refs*
            if some titles could not be matched.
        """
        results: list = []
        seen_ids: set[str] = set()
        for ref in domain_refs:
            if not ref.title:
                continue
            try:
                params = urllib.parse.urlencode({
                    "query": ref.title,
                    "fields": _FIELDS,
                    "limit": 1,
                })
                url = f"{_SEMANTIC_SCHOLAR_SEARCH_URL}?{params}"
                raw = self._http_get(url, label=f"domain-ref-lookup:{ref.title[:40]}")
                if raw is None:
                    continue
                data = json.loads(raw)
                items = data.get("data", [])
                if not items:
                    continue
                paper = _parse_semantic_scholar_item(items[0])
                if paper is not None and paper.id not in seen_ids:
                    seen_ids.add(paper.id)
                    results.append(paper)
            except Exception:
                continue
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _http_get(self, url: str, label: str) -> bytes | None:
        """GET *url* with exponential-backoff retry on transient HTTP errors.

        For HTTP 429 (rate-limit) responses the ``Retry-After`` response header
        is honoured when present; otherwise a minimum wait of
        ``_RETRY_429_MIN_DELAY`` seconds is used so that Semantic Scholar's
        per-minute quota has time to reset before the next attempt.

        Parameters
        ----------
        url:
            Fully-formed URL to fetch.
        label:
            Short description used in error messages (e.g. ``"references"``).

        Returns
        -------
        bytes | None
            Raw response body, or *None* if all attempts failed.
        """
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                    return resp.read()
            except urllib.error.HTTPError as exc:
                if exc.code in _RETRYABLE_HTTP_CODES and attempt < _MAX_RETRIES:
                    if exc.code == 429:
                        # Honour the Retry-After header when Semantic Scholar
                        # provides it; fall back to the configured minimum.
                        retry_after_raw = (exc.headers or {}).get("Retry-After", "")
                        try:
                            delay = max(float(retry_after_raw), _RETRY_429_MIN_DELAY)
                        except (TypeError, ValueError):
                            delay = _RETRY_429_MIN_DELAY
                    else:
                        delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    print(
                        f"  [online_search] {label}: HTTP {exc.code}, "
                        f"retrying in {delay:.0f}s (attempt {attempt}/{_MAX_RETRIES})…",
                        file=sys.stderr,
                    )
                    _time.sleep(delay)
                else:
                    err_msg = f"{label}: HTTP {exc.code} {exc.reason}"
                    self._last_errors.append(err_msg)
                    print(
                        f"  [online_search] {label}: HTTP {exc.code} {exc.reason}",
                        file=sys.stderr,
                    )
                    return None
            except Exception as exc:
                err_msg = f"{label}: {exc}"
                self._last_errors.append(err_msg)
                print(f"  [online_search] {label}: {exc}", file=sys.stderr)
                return None
        return None  # all retries exhausted

    def _lookup_paper_id_by_title(self, title: str) -> str | None:
        """Look up a Semantic Scholar paper ID by title search.

        Returns the first result's ``paperId`` or *None* on failure.  Used
        to find non-arXiv papers so that the ``/references`` depth-signal
        endpoint can still be called.
        """
        params = urllib.parse.urlencode({
            "query": title,
            "fields": "paperId,title",
            "limit": 3,
        })
        url = f"{_SEMANTIC_SCHOLAR_SEARCH_URL}?{params}"
        raw = self._http_get(url, label="title-lookup")
        if raw is None:
            return None
        try:
            data: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            return None
        items = data.get("data", [])
        if not items:
            return None
        return items[0].get("paperId") or None

    def lookup_paper_year(
        self,
        arxiv_id: str = "",
        title: str = "",
    ) -> int | None:
        """Look up the publication year of the submitted paper from Semantic Scholar.

        Used to establish an upper temporal bound so that papers published
        after the submission date are excluded from the prior-art pool.
        Tries the arXiv ID first (most reliable); falls back to a title
        search when no arXiv ID is available.  When both S2 lookups fail
        (e.g. due to rate-limiting) the year is derived from the arXiv ID's
        ``YYMM`` prefix as a last resort, so the temporal filter can still
        be applied.

        Parameters
        ----------
        arxiv_id:
            arXiv identifier (e.g. ``"2006.06138"``).
        title:
            Paper title, used as a fallback when *arxiv_id* is empty.

        Returns
        -------
        int | None
            Publication year, or *None* if the lookup fails.
        """
        if arxiv_id:
            paper_id_encoded = urllib.parse.quote(f"arXiv:{arxiv_id}", safe=":")
            url = f"{_SEMANTIC_SCHOLAR_PAPER_URL}/{paper_id_encoded}?fields=year"
            raw = self._http_get(url, label="paper-year-lookup")
            if raw is not None:
                try:
                    data: dict[str, Any] = json.loads(raw)
                    year_raw = data.get("year")
                    if isinstance(year_raw, int):
                        return year_raw
                except json.JSONDecodeError:
                    pass
        if title:
            s2_id = self._lookup_paper_id_by_title(title)
            if s2_id:
                url = f"{_SEMANTIC_SCHOLAR_PAPER_URL}/{s2_id}?fields=year"
                raw = self._http_get(url, label="paper-year-lookup-title")
                if raw is not None:
                    try:
                        data = json.loads(raw)
                        year_raw = data.get("year")
                        if isinstance(year_raw, int):
                            return year_raw
                    except json.JSONDecodeError:
                        pass
        # Last resort: derive the year from the arXiv ID's YYMM prefix.
        # New-style IDs (YYMM.NNNNN, introduced in April 2007) encode the
        # submission year and month.  IDs submitted from 2007 onwards have a
        # two-digit year ≤ 99; we assume 20YY for YY ≤ 99 (no arXiv IDs
        # predate 2007 in new-style format, and 2099 is far enough away that
        # this heuristic is safe for the foreseeable future).
        if arxiv_id:
            year_from_id = _year_from_arxiv_id(arxiv_id)
            if year_from_id is not None:
                return year_from_id
        return None

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
                # Use a dedicated large limit here: the paper's own reference list
                # should not be capped at the keyword-search max_results value.
                "limit": _MAX_CITED_REFS_LIMIT,
            }
        )
        url = f"{_SEMANTIC_SCHOLAR_PAPER_URL}/{paper_id_encoded}/references?{params}"
        raw = self._http_get(url, label=f"references({semantic_paper_id})")
        if raw is None:
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
        if self._min_year is not None:
            papers = [
                p for p in papers
                if p.year is None or p.year >= self._min_year
            ]
        if self._max_year is not None:
            papers = [
                p for p in papers
                if p.year is None or p.year <= self._max_year
            ]
        return papers

    def _query(self, query: str) -> list[ReferencePaper]:
        """Send one keyword query to Semantic Scholar; return parsed papers."""
        query_params: dict[str, str | int] = {
            "query": query,
            "fields": _FIELDS,
            "limit": _MAX_KEYWORD_SEARCH_LIMIT,
        }
        if self._min_year is not None or self._max_year is not None:
            min_part = str(self._min_year) if self._min_year is not None else ""
            max_part = str(self._max_year) if self._max_year is not None else ""
            query_params["year"] = f"{min_part}-{max_part}"
        params = urllib.parse.urlencode(query_params)
        url = f"{_SEMANTIC_SCHOLAR_SEARCH_URL}?{params}"
        raw = self._http_get(url, label=f"query('{query[:40]}')")
        if raw is None:
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
        # Apply client-side year filtering as a safeguard: the server-side
        # ``year`` parameter is not always honoured (e.g. when S2 rate-limits
        # the request and the year lookup failed, leaving max_year=None).
        # Papers with year=None pass through so that undated papers are not
        # silently dropped — the same convention as _fetch_references.
        if self._min_year is not None:
            papers = [p for p in papers if p.year is None or p.year >= self._min_year]
        if self._max_year is not None:
            papers = [p for p in papers if p.year is None or p.year <= self._max_year]
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


def _year_from_arxiv_id(arxiv_id: str) -> int | None:
    """Derive a publication year from a new-style arXiv ID (``YYMM.NNNNN``).

    New-style arXiv IDs were introduced in April 2007 and encode the
    submission year and month as a four-digit prefix ``YYMM``.  Returns the
    four-digit year (e.g. ``2020`` for ID ``"2006.06138"``) or *None* when
    the ID does not match the expected pattern.
    """
    m = re.match(r'^(\d{2})\d{2}\.\d+', arxiv_id)
    if m:
        yy = int(m.group(1))
        return 2000 + yy
    return None


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
