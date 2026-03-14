"""Tests for open_idea_sourcing.similarity_search."""

import pytest

from open_idea_sourcing.reference_store import ReferencePaper, ReferenceStore
from open_idea_sourcing.similarity_search import SimilarityResult, SimilaritySearch


def _populate_store() -> ReferenceStore:
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
            id="bert2019",
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            abstract=(
                "We introduce BERT, a language representation model pre-trained "
                "on unlabelled text using masked language modelling."
            ),
            year=2019,
        )
    )
    store.add(
        ReferencePaper(
            id="resnet2016",
            title="Deep Residual Learning for Image Recognition",
            abstract=(
                "We present a residual learning framework to ease the training "
                "of deep neural networks for image classification."
            ),
            year=2016,
        )
    )
    return store


class TestSimilaritySearch:
    def setup_method(self):
        self.store = _populate_store()
        self.searcher = SimilaritySearch(self.store)

    def test_search_returns_list_of_results(self):
        results = self.searcher.search("attention mechanism transformer")
        assert isinstance(results, list)
        assert all(isinstance(r, SimilarityResult) for r in results)

    def test_search_top_k_limits_results(self):
        results = self.searcher.search("neural network", top_k=2)
        assert len(results) <= 2

    def test_scores_are_between_zero_and_one(self):
        results = self.searcher.search("attention transformer language model")
        for r in results:
            assert 0.0 <= r.score <= 1.0

    def test_results_sorted_descending_by_score(self):
        results = self.searcher.search("attention transformer")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_relevant_paper_surfaces_for_attention_query(self):
        results = self.searcher.search(
            "self-attention mechanism dispensing recurrence"
        )
        top_ids = [r.paper.id for r in results[:2]]
        assert "att2017" in top_ids

    def test_threshold_filters_low_scores(self):
        results = self.searcher.search("quantum physics", threshold=0.9)
        # Nothing should match unrelated content at high threshold
        assert len(results) == 0

    def test_empty_store_returns_empty_list(self):
        searcher = SimilaritySearch(ReferenceStore())
        results = searcher.search("anything")
        assert results == []

    def test_rebuild_index_reflects_new_papers(self):
        extra = ReferencePaper(
            id="gpt2020",
            title="Language Models are Few-Shot Learners",
            abstract="GPT-3 is a large-scale language model with in-context learning.",
            year=2020,
        )
        self.store.add(extra)
        self.searcher.rebuild_index()
        results = self.searcher.search("language model few-shot in-context")
        ids = [r.paper.id for r in results]
        assert "gpt2020" in ids

    def test_search_rebuilds_index_automatically(self):
        """search() should work even if rebuild_index was never called."""
        searcher = SimilaritySearch(self.store)
        results = searcher.search("deep residual image classification")
        assert len(results) > 0

    def test_similarity_result_repr(self):
        store = _populate_store()
        searcher = SimilaritySearch(store)
        results = searcher.search("transformer")
        assert "score=" in repr(results[0])
        assert "title=" in repr(results[0])
