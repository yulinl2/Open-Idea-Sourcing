"""Find a random non-cited reference from the broader related field.

Searches Semantic Scholar for papers related to the target paper's topic,
then excludes all known cited paper IDs to find a field-relevant but
non-cited reference.
"""

from __future__ import annotations

import json
import random
import sys
import urllib.parse

from .reference_collector import CitedPaper, _http_get, _parse_s2_paper

_S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = "title,abstract,year,authors,externalIds,url"


def _generate_field_queries(title: str, abstract: str) -> list[str]:
    """Generate broad field queries from paper title and abstract.

    Extracts key noun phrases and domain terms to search for papers
    in the same field but not necessarily the exact same topic.
    """
    queries = []

    # Use title words (minus common stopwords) as a broad query
    stopwords = {
        "a", "an", "the", "of", "in", "on", "for", "to", "and", "or",
        "is", "are", "was", "were", "with", "from", "by", "at", "as",
        "that", "this", "which", "into", "using", "via", "based",
    }
    title_words = [w for w in title.lower().split() if w not in stopwords and len(w) > 2]

    # Take first 3-4 meaningful words from title for a broad query
    if len(title_words) >= 3:
        queries.append(" ".join(title_words[:4]))

    # Take different subsets for variety
    if len(title_words) >= 5:
        queries.append(" ".join(title_words[2:6]))

    # Extract key terms from abstract
    if abstract:
        abstract_words = [
            w for w in abstract.lower().split()
            if w not in stopwords and len(w) > 3
        ]
        if len(abstract_words) >= 4:
            # Sample from the first few sentences (domain-relevant terms)
            queries.append(" ".join(abstract_words[:5]))

    if not queries:
        queries = [title[:80]]

    return queries[:3]


def find_random_non_cited_reference(
    title: str,
    abstract: str,
    cited_ids: set[str],
    *,
    max_search_results: int = 50,
    target_year: int | None = None,
) -> CitedPaper | None:
    """Find a random paper from the broader field that is NOT cited.

    Parameters
    ----------
    title:
        Target paper title (for generating search queries).
    abstract:
        Target paper abstract.
    cited_ids:
        Set of Semantic Scholar paper IDs to exclude.
    max_search_results:
        How many results to fetch per query.
    target_year:
        If provided, prefer papers from around this year (±3 years).

    Returns
    -------
    CitedPaper or None
        A random non-cited paper from the field, or None if none found.
    """
    queries = _generate_field_queries(title, abstract)
    candidates: dict[str, CitedPaper] = {}

    for query in queries:
        encoded = urllib.parse.quote(query)
        year_filter = ""
        if target_year:
            year_filter = f"&year={target_year - 3}-{target_year + 1}"

        url = (
            f"{_S2_SEARCH}?query={encoded}&limit={max_search_results}"
            f"&fields={_FIELDS}{year_filter}"
        )

        try:
            data = _http_get(url)
        except Exception as exc:
            print(
                f"  [random_ref] search failed for '{query}': {exc}",
                file=sys.stderr,
            )
            continue

        for raw in data.get("data") or []:
            paper = _parse_s2_paper(raw)
            if paper and paper.paper_id and paper.paper_id not in cited_ids:
                candidates[paper.paper_id] = paper

    if not candidates:
        print("  [random_ref] no non-cited candidates found", file=sys.stderr)
        return None

    # Pick one randomly
    chosen = random.choice(list(candidates.values()))
    print(
        f"  [random_ref] selected: '{chosen.title[:60]}...' "
        f"(from {len(candidates)} candidates)",
        file=sys.stderr,
    )
    return chosen
