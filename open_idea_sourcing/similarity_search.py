"""Semantic similarity search over a :class:`ReferenceStore`.

Uses TF-IDF vectorisation (``scikit-learn``) and cosine similarity to
rank reference papers by their textual closeness to a query string.
No GPU or large model download required.
"""

from __future__ import annotations

from dataclasses import dataclass

import hashlib
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

    The TF-IDF index is rebuilt automatically whenever the set of papers in
    the underlying store differs from what was indexed last.  Call
    :meth:`rebuild_index` explicitly if you need to force a rebuild for any
    other reason (e.g. after mutating paper content in-place).
    """

    def __init__(self, store: ReferenceStore) -> None:
        self._store = store
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None  # sparse matrix (n_papers × n_features)
        self._indexed_ids: list[str] = []
        # Hash of each paper's searchable_text at the time of indexing.
        # Used to detect content changes for papers with stable IDs.
        self._indexed_hashes: list[str] = []

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
            self._indexed_hashes = []
            return

        corpus = [p.searchable_text for p in papers]
        self._indexed_ids = [p.id for p in papers]
        # Track a content hash for each paper so we can detect updates where
        # the paper ID stays the same but the searchable_text changes.
        self._indexed_hashes = [
            hashlib.sha1(
                (p.searchable_text or "").encode("utf-8", "ignore")
            ).hexdigest()
            for p in papers
        ]
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
        if top_k <= 0:
            return []

        papers = self._store.all_papers()
        current_ids = [p.id for p in papers]
        current_hashes = [
            hashlib.sha1(
                (p.searchable_text or "").encode("utf-8", "ignore")
            ).hexdigest()
            for p in papers
        ]
        if (
            self._matrix is None
            or self._vectorizer is None
            or len(current_ids) != len(self._indexed_ids)
            or current_ids != self._indexed_ids
            or current_hashes != self._indexed_hashes
        ):
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
