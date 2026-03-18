"""Tests for open_idea_sourcing.idea_decomposer."""

import pytest

from open_idea_sourcing.idea_decomposer import (
    DecomposedIdea,
    IdeaDecomposer,
    _parse_ideas,
)
from open_idea_sourcing.paper_parser import ParsedPaper
from open_idea_sourcing.reference_store import ReferencePaper, ReferenceStore
from open_idea_sourcing.similarity_search import SimilarityResult, SimilaritySearch


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

SAMPLE_PAPER = ParsedPaper(
    title="Efficient Sparse Transformers with Dynamic Masking",
    abstract=(
        "We propose sparse attention with dynamic masking to reduce the "
        "quadratic complexity of self-attention in large transformer models."
    ),
    full_text=(
        "Efficient Sparse Transformers with Dynamic Masking\n\n"
        "Abstract\n"
        "We propose sparse attention with dynamic masking to reduce the "
        "quadratic complexity of self-attention in large transformer models.\n\n"
        "Introduction\n"
        "The standard attention mechanism scales quadratically. "
        "We address this with sparsity and learnable masks."
    ),
)


def _populated_store() -> ReferenceStore:
    store = ReferenceStore()
    store.add(
        ReferencePaper(
            id="att2017",
            title="Attention Is All You Need",
            abstract=(
                "We propose the Transformer, a novel architecture based solely "
                "on attention mechanisms, dispensing with recurrence entirely."
            ),
            year=2017,
        )
    )
    store.add(
        ReferencePaper(
            id="sparse2019",
            title="Generating Long Sequences with Sparse Transformers",
            abstract=(
                "We introduce sparse factorizations of the attention matrix "
                "that reduce the complexity to O(n sqrt(n))."
            ),
            year=2019,
        )
    )
    store.add(
        ReferencePaper(
            id="bert2019",
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            abstract=(
                "We introduce BERT, a language representation model "
                "pre-trained on unlabelled text using masked language modelling."
            ),
            year=2019,
        )
    )
    return store


def _make_canned_llm(ideas_response: str):
    """Return an LLM stub that always returns *ideas_response*."""

    def llm(_prompt: str) -> str:
        return ideas_response

    return llm


# ---------------------------------------------------------------------------
# _parse_ideas unit tests
# ---------------------------------------------------------------------------


class TestParseIdeas:
    def test_numbered_list(self):
        text = "1. Sparse attention mechanism\n2. Dynamic masking"
        ideas = _parse_ideas(text)
        assert ideas == ["Sparse attention mechanism", "Dynamic masking"]

    def test_numbered_list_with_parens(self):
        text = "1) Sparse attention\n2) Dynamic masking\n3) Linear complexity"
        ideas = _parse_ideas(text)
        assert len(ideas) == 3
        assert ideas[0] == "Sparse attention"

    def test_fallback_to_plain_lines(self):
        text = "Sparse attention\nDynamic masking"
        ideas = _parse_ideas(text)
        assert ideas == ["Sparse attention", "Dynamic masking"]

    def test_empty_text_uses_fallback(self):
        ideas = _parse_ideas("", fallback="my fallback")
        assert ideas == ["my fallback"]

    def test_empty_text_no_fallback(self):
        ideas = _parse_ideas("")
        assert ideas == ["(unknown idea)"]

    def test_strips_surrounding_whitespace(self):
        text = "  1. Idea with spaces   \n  2.   Another idea  "
        ideas = _parse_ideas(text)
        assert ideas[0] == "Idea with spaces"
        assert ideas[1] == "Another idea"

    def test_ignores_blank_lines(self):
        text = "\n\n1. First idea\n\n2. Second idea\n\n"
        ideas = _parse_ideas(text)
        assert ideas == ["First idea", "Second idea"]


# ---------------------------------------------------------------------------
# IdeaDecomposer.decompose
# ---------------------------------------------------------------------------


class TestDecompose:
    def test_returns_list_of_strings(self):
        llm = _make_canned_llm(
            "1. Sparse attention to reduce complexity\n2. Learnable dynamic masks"
        )
        decomposer = IdeaDecomposer(llm=llm)
        ideas = decomposer.decompose(SAMPLE_PAPER)
        assert isinstance(ideas, list)
        assert len(ideas) == 2
        assert all(isinstance(i, str) for i in ideas)

    def test_malformed_response_falls_back(self):
        """An unstructured LLM response should still produce at least one idea."""
        llm = _make_canned_llm("This is just an unstructured response without numbering")
        decomposer = IdeaDecomposer(llm=llm)
        ideas = decomposer.decompose(SAMPLE_PAPER)
        assert len(ideas) >= 1

    def test_empty_response_falls_back_to_title(self):
        llm = _make_canned_llm("")
        decomposer = IdeaDecomposer(llm=llm)
        ideas = decomposer.decompose(SAMPLE_PAPER)
        assert len(ideas) == 1
        assert SAMPLE_PAPER.title in ideas[0]


# ---------------------------------------------------------------------------
# IdeaDecomposer.search_per_idea
# ---------------------------------------------------------------------------


class TestSearchPerIdea:
    def setup_method(self):
        store = _populated_store()
        self.searcher = SimilaritySearch(store)

    def test_returns_one_entry_per_idea(self):
        llm = _make_canned_llm("1. sparse attention\n2. dynamic masking")
        decomposer = IdeaDecomposer(llm=llm, top_k_per_idea=3)
        ideas = ["sparse attention transformer", "dynamic masking training"]
        decomposed = decomposer.search_per_idea(ideas, self.searcher)
        assert len(decomposed) == 2
        assert all(isinstance(d, DecomposedIdea) for d in decomposed)

    def test_results_are_similarity_results(self):
        decomposer = IdeaDecomposer(llm=_make_canned_llm(""), top_k_per_idea=3)
        decomposed = decomposer.search_per_idea(
            ["attention mechanism"], self.searcher
        )
        for d in decomposed:
            for r in d.results:
                assert isinstance(r, SimilarityResult)

    def test_empty_store_yields_empty_results(self):
        empty_searcher = SimilaritySearch(ReferenceStore())
        decomposer = IdeaDecomposer(llm=_make_canned_llm(""), top_k_per_idea=3)
        decomposed = decomposer.search_per_idea(["any idea"], empty_searcher)
        assert len(decomposed) == 1
        assert decomposed[0].results == []

    def test_empty_ideas_list(self):
        decomposer = IdeaDecomposer(llm=_make_canned_llm(""), top_k_per_idea=3)
        decomposed = decomposer.search_per_idea([], self.searcher)
        assert decomposed == []


# ---------------------------------------------------------------------------
# IdeaDecomposer.merge_results
# ---------------------------------------------------------------------------


class TestMergeResults:
    def _make_result(self, paper_id: str, score: float) -> SimilarityResult:
        paper = ReferencePaper(id=paper_id, title=paper_id, abstract="")
        return SimilarityResult(paper=paper, score=score)

    def test_deduplicates_same_paper_id(self):
        r1 = self._make_result("att2017", 0.8)
        r2 = self._make_result("att2017", 0.6)  # same paper, lower score
        d1 = DecomposedIdea(text="idea 1", results=[r1])
        d2 = DecomposedIdea(text="idea 2", results=[r2])
        decomposer = IdeaDecomposer(llm=_make_canned_llm(""))
        merged = decomposer.merge_results([d1, d2])
        assert len(merged) == 1
        assert merged[0].score == 0.8  # keeps the higher score

    def test_keeps_max_score(self):
        r1 = self._make_result("bert2019", 0.3)
        r2 = self._make_result("bert2019", 0.9)
        d1 = DecomposedIdea(text="idea 1", results=[r1])
        d2 = DecomposedIdea(text="idea 2", results=[r2])
        decomposer = IdeaDecomposer(llm=_make_canned_llm(""))
        merged = decomposer.merge_results([d1, d2])
        assert merged[0].score == 0.9

    def test_sorted_by_score_descending(self):
        results = [
            self._make_result("a", 0.4),
            self._make_result("b", 0.9),
            self._make_result("c", 0.1),
        ]
        d = DecomposedIdea(text="idea", results=results)
        decomposer = IdeaDecomposer(llm=_make_canned_llm(""))
        merged = decomposer.merge_results([d])
        scores = [r.score for r in merged]
        assert scores == sorted(scores, reverse=True)

    def test_empty_input(self):
        decomposer = IdeaDecomposer(llm=_make_canned_llm(""))
        merged = decomposer.merge_results([])
        assert merged == []

    def test_distinct_papers_from_multiple_ideas(self):
        r1 = self._make_result("att2017", 0.7)
        r2 = self._make_result("sparse2019", 0.5)
        d1 = DecomposedIdea(text="idea 1", results=[r1])
        d2 = DecomposedIdea(text="idea 2", results=[r2])
        decomposer = IdeaDecomposer(llm=_make_canned_llm(""))
        merged = decomposer.merge_results([d1, d2])
        ids = {r.paper.id for r in merged}
        assert ids == {"att2017", "sparse2019"}


# ---------------------------------------------------------------------------
# IdeaDecomposer.run (integration)
# ---------------------------------------------------------------------------


class TestRun:
    def setup_method(self):
        store = _populated_store()
        self.searcher = SimilaritySearch(store)

    def test_run_returns_three_tuple(self):
        llm = _make_canned_llm(
            "1. Sparse attention transformer\n"
            "2. Dynamic masking for efficiency"
        )
        decomposer = IdeaDecomposer(llm=llm, top_k_per_idea=3)
        ideas, decomposed, merged = decomposer.run(SAMPLE_PAPER, self.searcher)
        assert isinstance(ideas, list)
        assert isinstance(decomposed, list)
        assert isinstance(merged, list)

    def test_run_ideas_match_decomposed(self):
        llm = _make_canned_llm(
            "1. Sparse attention\n2. Dynamic masking\n3. Linear complexity"
        )
        decomposer = IdeaDecomposer(llm=llm, top_k_per_idea=2)
        ideas, decomposed, _ = decomposer.run(SAMPLE_PAPER, self.searcher)
        assert len(ideas) == len(decomposed)
        for idea_text, d in zip(ideas, decomposed):
            assert d.text == idea_text

    def test_merged_results_are_deduplicated(self):
        """The same paper should not appear twice in the merged list."""
        llm = _make_canned_llm(
            "1. attention mechanism transformer\n"
            "2. attention masking transformer"
        )
        decomposer = IdeaDecomposer(llm=llm, top_k_per_idea=5)
        _, _, merged = decomposer.run(SAMPLE_PAPER, self.searcher)
        paper_ids = [r.paper.id for r in merged]
        assert len(paper_ids) == len(set(paper_ids)), "Duplicate paper IDs in merged results"

    def test_run_with_empty_store(self):
        llm = _make_canned_llm("1. some idea")
        decomposer = IdeaDecomposer(llm=llm, top_k_per_idea=3)
        ideas, decomposed, merged = decomposer.run(
            SAMPLE_PAPER, SimilaritySearch(ReferenceStore())
        )
        assert len(ideas) >= 1
        assert merged == []

    def test_top_k_respected(self):
        """Merged results should not exceed store size (and top_k acts per idea)."""
        llm = _make_canned_llm("1. transformer attention\n2. masking")
        decomposer = IdeaDecomposer(llm=llm, top_k_per_idea=1)
        _, _, merged = decomposer.run(SAMPLE_PAPER, self.searcher)
        # At most 1 result per idea × 2 ideas = at most 2 unique papers
        assert len(merged) <= 2

    def test_threshold_filters_low_scores(self):
        llm = _make_canned_llm("1. completely unrelated topic xyz abc")
        decomposer = IdeaDecomposer(
            llm=llm, top_k_per_idea=5, similarity_threshold=0.99
        )
        _, _, merged = decomposer.run(SAMPLE_PAPER, self.searcher)
        for r in merged:
            assert r.score >= 0.99
