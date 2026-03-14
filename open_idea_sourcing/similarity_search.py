"""Semantic similarity search over a :class:`ReferenceStore`.

Uses TF-IDF vectorisation (``scikit-learn``) and cosine similarity to
rank reference papers by their textual closeness to a query string.
No GPU or large model download required.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .reference_store import ReferencePaper, ReferenceStore


@dataclass
class SimilarityResult:
    """A reference paper together with its similarity score."""

    paper: ReferencePaper
    score: float  # 0.0 – 1.0

    def __repr__(self) -> str:
        return (
            f"SimilarityResult(score={self.score:.3f}, "
            f"title={self.paper.title!r})"
        )


class SimilaritySearch:
    """Find reference papers that are most similar to a query text.

    The index is rebuilt lazily whenever the underlying store changes.
    Call :meth:`rebuild_index` explicitly after bulk additions.
    """

    def __init__(self, store: ReferenceStore) -> None:
        self._store = store
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None  # sparse matrix (n_papers × n_features)
        self._indexed_ids: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rebuild_index(self) -> None:
        """(Re)build the TF-IDF index from the current store contents."""
        papers = self._store.all_papers()
        if not papers:
            self._vectorizer = None
            self._matrix = None
            self._indexed_ids = []
            return

        corpus = [p.searchable_text for p in papers]
        self._indexed_ids = [p.id for p in papers]
        self._vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=1,
            stop_words="english",
            sublinear_tf=True,
        )
        self._matrix = self._vectorizer.fit_transform(corpus)

    def search(
        self, query: str, top_k: int = 5, threshold: float = 0.0
    ) -> list[SimilarityResult]:
        """Return the *top_k* most similar papers for *query*.

        Parameters
        ----------
        query:
            Free-form text to search for (e.g. a paper's abstract).
        top_k:
            Maximum number of results to return.
        threshold:
            Minimum cosine-similarity score; lower-scoring papers are
            excluded even if fewer than *top_k* results remain.
        """
        if self._matrix is None or self._vectorizer is None:
            self.rebuild_index()
        if self._matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]

        results: list[SimilarityResult] = []
        for idx in np.argsort(scores)[::-1]:
            score = float(scores[idx])
            if score < threshold:
                break
            paper = self._store.get(self._indexed_ids[idx])
            if paper is not None:
                results.append(SimilarityResult(paper=paper, score=score))
            if len(results) >= top_k:
                break
        return results
