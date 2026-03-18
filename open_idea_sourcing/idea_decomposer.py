"""Iterative idea decomposition and source search.

Given a parsed paper, this module:

1. Uses an LLM to decompose the paper into its key constituent ideas.
2. For each idea, performs a TF-IDF similarity search against a
   :class:`~open_idea_sourcing.reference_store.ReferenceStore`.
3. Aggregates and deduplicates results, returning a ranked list of
   :class:`~open_idea_sourcing.similarity_search.SimilarityResult` objects
   (one entry per reference paper, scored by its highest match across all
   ideas).

This iterative approach surfaces more relevant references than a single
whole-paper query, because distinct ideas within a paper may match
different reference papers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from .paper_parser import ParsedPaper
from .similarity_search import SimilarityResult, SimilaritySearch


# Type alias for the LLM callable (same convention as novelty_evaluator.py)
LLMCallable = Callable[[str], str]


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_DECOMPOSE_PROMPT = """You are an expert research analyst.

TASK: Identify the key *independent* ideas or contributions in the submitted
paper. Each idea should be a self-contained concept, method, or claim that
could be searched for in the literature independently.

SUBMITTED PAPER:
{paper_content}

INSTRUCTIONS:
- List between 2 and 5 ideas, ordered from most important to least important.
- Each idea should be expressed as a short, precise phrase (5–20 words).
- Prefix each idea with a number and a period, e.g.:
    1. <idea one>
    2. <idea two>
- Do not include any other text — output only the numbered list.
"""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DecomposedIdea:
    """A single extracted idea and the reference papers found for it.

    Attributes
    ----------
    text:
        The idea text as returned by the LLM, e.g.
        ``"Dynamic attention masking to reduce quadratic complexity"``.
    results:
        Similarity-search results for this idea, sorted by score descending.
    """

    text: str
    results: list[SimilarityResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------


class IdeaDecomposer:
    """Decompose a paper into ideas and search for source papers for each.

    Parameters
    ----------
    llm:
        Callable that receives a prompt string and returns the LLM response.
    top_k_per_idea:
        Maximum number of similar papers to retrieve per idea.
    similarity_threshold:
        Minimum cosine-similarity score to include a result.
    """

    def __init__(
        self,
        llm: LLMCallable,
        top_k_per_idea: int = 5,
        similarity_threshold: float = 0.0,
    ) -> None:
        self._llm = llm
        self._top_k = top_k_per_idea
        self._threshold = similarity_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decompose(self, paper: ParsedPaper) -> list[str]:
        """Ask the LLM to list the key ideas in *paper*.

        Returns
        -------
        list[str]
            Ordered list of idea strings (at least one, even if the LLM
            response is malformed).
        """
        prompt = _DECOMPOSE_PROMPT.format(paper_content=paper.key_content())
        response = self._llm(prompt)
        return _parse_ideas(response, fallback=paper.title or paper.abstract[:200])

    def search_per_idea(
        self,
        ideas: list[str],
        searcher: SimilaritySearch,
    ) -> list[DecomposedIdea]:
        """Run a separate similarity search for each idea.

        Parameters
        ----------
        ideas:
            List of idea strings (e.g. from :meth:`decompose`).
        searcher:
            A :class:`~open_idea_sourcing.similarity_search.SimilaritySearch`
            instance backed by the reference store.

        Returns
        -------
        list[DecomposedIdea]
            One :class:`DecomposedIdea` per idea, each with its own ranked
            list of similar reference papers.
        """
        decomposed: list[DecomposedIdea] = []
        for idea_text in ideas:
            results = searcher.search(
                idea_text,
                top_k=self._top_k,
                threshold=self._threshold,
            )
            decomposed.append(DecomposedIdea(text=idea_text, results=results))
        return decomposed

    def merge_results(
        self, decomposed: list[DecomposedIdea]
    ) -> list[SimilarityResult]:
        """Merge per-idea results into a single deduplicated ranked list.

        When the same reference paper appears for multiple ideas, the
        highest similarity score across all ideas is kept.

        Parameters
        ----------
        decomposed:
            Output of :meth:`search_per_idea`.

        Returns
        -------
        list[SimilarityResult]
            Deduplicated results sorted by score descending.
        """
        best: dict[str, SimilarityResult] = {}
        for idea in decomposed:
            for result in idea.results:
                pid = result.paper.id
                if pid not in best or result.score > best[pid].score:
                    best[pid] = result
        return sorted(best.values(), key=lambda r: r.score, reverse=True)

    def run(
        self,
        paper: ParsedPaper,
        searcher: SimilaritySearch,
    ) -> tuple[list[str], list[DecomposedIdea], list[SimilarityResult]]:
        """Full pipeline: decompose → per-idea search → merge.

        Parameters
        ----------
        paper:
            Parsed paper to analyse.
        searcher:
            Similarity-search instance backed by the reference store.

        Returns
        -------
        tuple[list[str], list[DecomposedIdea], list[SimilarityResult]]
            ``(ideas, decomposed, merged)`` where:

            * *ideas* — raw idea strings extracted from the paper.
            * *decomposed* — per-idea search results.
            * *merged* — deduplicated, score-sorted list of all reference
              papers found across all ideas.
        """
        ideas = self.decompose(paper)
        decomposed = self.search_per_idea(ideas, searcher)
        merged = self.merge_results(decomposed)
        return ideas, decomposed, merged


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------


def _parse_ideas(text: str, fallback: str = "") -> list[str]:
    """Extract numbered ideas from the LLM response.

    Each line that starts with an optional number followed by a period
    (e.g. ``"1. "`` or ``"2) "``) is treated as one idea.  If no numbered
    items are found, non-empty lines are used instead.  If the text is
    empty the *fallback* string is returned as a single idea.
    """
    lines = text.strip().splitlines()
    # Try to extract numbered list items: "1. text", "1) text"
    numbered = re.compile(r"^\s*\d+[.)]\s+(.+)")
    ideas: list[str] = []
    for line in lines:
        m = numbered.match(line)
        if m:
            ideas.append(m.group(1).strip())
    if ideas:
        return ideas

    # Fall back to all non-empty lines
    ideas = [line.strip() for line in lines if line.strip()]
    if ideas:
        return ideas

    # Last resort: use the fallback
    return [fallback] if fallback else ["(unknown idea)"]
