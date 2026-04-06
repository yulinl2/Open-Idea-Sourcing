"""TF-IDF-based text filtering to separate conceptually dense passages from routine text.

The idea: academic papers contain a mix of:
  - Routine text: standard methodology descriptions, boilerplate transitions,
    well-known definitions that any domain expert could predict
  - Conceptually dense text: novel claims, unique formulations, key results,
    new definitions that are specific to THIS paper

By computing TF-IDF against a background corpus (the cited references), we
can identify which terms in the target paper are *surprising* (high IDF) vs
*expected* (low IDF). Passages with high average TF-IDF are the conceptually
novel parts; passages with low TF-IDF are the routine parts.

Hypothesis: Running perplexity analysis on only the conceptually dense
passages should yield better separation between related vs unrelated references,
because we've removed the "shared predictability floor" of routine academic
writing.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer for academic text."""
    text = text.lower()
    # Keep alphanumeric, hyphens within words, and basic math notation
    tokens = re.findall(r"[a-z][a-z0-9\-]*(?:'[a-z]+)?|[0-9]+(?:\.[0-9]+)?", text)
    return tokens


# Common academic stopwords beyond standard English stopwords
_STOPWORDS = frozenset({
    "a", "an", "the", "of", "in", "on", "for", "to", "and", "or", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "may", "might", "shall", "can",
    "with", "from", "by", "at", "as", "that", "this", "which", "who", "whom",
    "it", "its", "we", "our", "they", "their", "he", "she", "his", "her",
    "not", "no", "if", "then", "than", "but", "also", "more", "most", "such",
    "each", "all", "any", "some", "other", "into", "about", "between", "through",
    "during", "before", "after", "above", "below", "both", "these", "those",
    "where", "when", "how", "what", "while", "so", "very", "just", "only",
    "given", "et", "al", "i-e", "e-g", "etc", "figure", "fig", "table",
    "section", "equation", "eq", "see", "note", "respectively",
    # Common academic verbs
    "show", "shows", "shown", "propose", "proposed", "consider",
    "considered", "define", "defined", "use", "used", "using", "based",
    "provide", "provides", "result", "results", "paper", "study",
    # Structural/organizational words that appear in boilerplate
    "organized", "follows", "rest", "presents", "reviews", "related",
    "work", "discuss", "discussed", "section", "chapter", "appendix",
    "outline", "remainder", "structure", "summarize", "conclude",
    "introduction", "conclusion", "acknowledgments", "references",
    "previously", "mentioned", "described", "illustrated", "depicted",
})

# Patterns that indicate boilerplate/organizational sentences
_BOILERPLATE_PATTERNS = [
    re.compile(r"(?i)the rest of (the|this) paper"),
    re.compile(r"(?i)section \d+ (reviews?|presents?|discusses?|describes?)"),
    re.compile(r"(?i)(this|the) paper is organized"),
    re.compile(r"(?i)in section \d+,? we"),
    re.compile(r"(?i)^(figure|table|fig\.|tab\.) \d+"),
    re.compile(r"(?i)as (shown|illustrated|described|discussed) (in|above|below)"),
    re.compile(r"(?i)^(see|cf\.|note that|recall that)"),
    re.compile(r"(?i)the (proof|details) (is|are) (given|provided|deferred)"),
    re.compile(r"(?i)we (note|remark|observe) that"),
    re.compile(r"(?i)for (simplicity|brevity|clarity|notational convenience)"),
]


def _filtered_tokens(text: str) -> list[str]:
    """Tokenize and remove stopwords and very short tokens."""
    return [t for t in _tokenize(text) if t not in _STOPWORDS and len(t) > 2]


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving paragraph structure."""
    # Split on sentence-ending punctuation followed by space or newline
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z(\["(]|[a-z]{1,3}\s)', text)
    # Also split on double newlines (paragraph breaks)
    result = []
    for s in sentences:
        parts = s.split("\n\n")
        result.extend(p.strip() for p in parts if p.strip())
    return [s for s in result if len(s) > 20]


def compute_idf(documents: list[str]) -> dict[str, float]:
    """Compute IDF scores from a corpus of documents.

    IDF(term) = log(N / df(term)) where df = number of docs containing term.
    Terms appearing in ALL documents get IDF=0 (completely expected).
    """
    n_docs = len(documents)
    if n_docs == 0:
        return {}

    doc_freq: Counter = Counter()
    for doc in documents:
        unique_terms = set(_filtered_tokens(doc))
        for term in unique_terms:
            doc_freq[term] += 1

    idf = {}
    for term, df in doc_freq.items():
        idf[term] = math.log(n_docs / df)
    return idf


def compute_tfidf(text: str, idf: dict[str, float]) -> dict[str, float]:
    """Compute TF-IDF scores for terms in a single document."""
    tokens = _filtered_tokens(text)
    if not tokens:
        return {}

    tf = Counter(tokens)
    max_tf = max(tf.values())

    tfidf = {}
    for term, count in tf.items():
        # Augmented TF to prevent bias toward longer documents
        tf_score = 0.5 + 0.5 * (count / max_tf)
        idf_score = idf.get(term, math.log(100))  # high IDF for unknown terms
        tfidf[term] = tf_score * idf_score
    return tfidf


@dataclass
class ScoredSentence:
    """A sentence with its TF-IDF density score."""
    text: str
    score: float
    n_keywords: int  # number of high-TF-IDF terms
    top_terms: list[str]  # most distinctive terms in this sentence
    orig_index: int = 0  # position in the original sentence list


def score_sentences(
    text: str,
    idf: dict[str, float],
    *,
    top_term_threshold: float = 0.5,
) -> list[ScoredSentence]:
    """Score each sentence in the text by its TF-IDF keyword density.

    Parameters
    ----------
    text:
        The document text to score.
    idf:
        IDF dictionary from the background corpus.
    top_term_threshold:
        Fraction of max TF-IDF score above which a term is considered a "keyword".

    Returns
    -------
    list[ScoredSentence]
        Sentences sorted by score (highest first).
    """
    tfidf = compute_tfidf(text, idf)
    if not tfidf:
        return []

    max_tfidf = max(tfidf.values()) if tfidf else 1.0
    keyword_threshold = max_tfidf * top_term_threshold

    sentences = _split_sentences(text)
    scored = []

    for idx, sent in enumerate(sentences):
        tokens = _filtered_tokens(sent)
        if not tokens:
            continue

        # Average TF-IDF of tokens in this sentence
        sent_scores = [tfidf.get(t, 0.0) for t in tokens]
        avg_score = sum(sent_scores) / len(sent_scores) if sent_scores else 0.0

        # Penalize boilerplate/organizational sentences
        is_boilerplate = any(pat.search(sent) for pat in _BOILERPLATE_PATTERNS)
        if is_boilerplate:
            avg_score *= 0.1  # heavy penalty

        # Count high-TF-IDF keywords
        keywords = [t for t in tokens if tfidf.get(t, 0) >= keyword_threshold]

        scored.append(ScoredSentence(
            text=sent,
            score=avg_score,
            n_keywords=len(keywords),
            top_terms=sorted(set(keywords), key=lambda t: tfidf.get(t, 0), reverse=True)[:5],
            orig_index=idx,
        ))

    scored.sort(key=lambda s: s.score, reverse=True)
    return scored


def filter_to_dense_passages(
    text: str,
    background_texts: list[str],
    *,
    keep_ratio: float = 0.5,
    min_sentences: int = 5,
) -> tuple[str, dict]:
    """Filter a document to keep only its most conceptually dense passages.

    Parameters
    ----------
    text:
        The target document to filter.
    background_texts:
        Corpus of reference documents (e.g., cited papers) for IDF computation.
    keep_ratio:
        Fraction of sentences to keep (by TF-IDF score), default 50%.
    min_sentences:
        Minimum number of sentences to keep regardless of ratio.

    Returns
    -------
    tuple[str, dict]
        (filtered_text, diagnostics_dict)
    """
    # Build IDF from background + target (target is part of the corpus)
    all_docs = background_texts + [text]
    idf = compute_idf(all_docs)

    # Score sentences
    scored = score_sentences(text, idf)
    if not scored:
        return text, {"error": "no sentences found", "n_sentences": 0}

    # Decide how many to keep
    n_keep = max(min_sentences, int(len(scored) * keep_ratio))
    n_keep = min(n_keep, len(scored))

    # Keep top-scoring sentences, but restore original order.
    # scored list entries carry an .orig_index set during scoring.
    kept_indices = {s.orig_index for s in scored[:n_keep]}
    all_sentences = _split_sentences(text)

    kept_in_order = []
    for idx, sent in enumerate(all_sentences):
        if idx in kept_indices:
            kept_in_order.append(sent)

    filtered_text = "\n\n".join(kept_in_order)

    # Compute diagnostics
    kept_scores = [s.score for s in scored[:n_keep]]
    dropped_scores = [s.score for s in scored[n_keep:]]
    all_top_terms: Counter = Counter()
    for s in scored[:n_keep]:
        for t in s.top_terms:
            all_top_terms[t] += 1

    diagnostics = {
        "n_sentences_total": len(scored),
        "n_sentences_kept": n_keep,
        "n_sentences_dropped": len(scored) - n_keep,
        "keep_ratio": keep_ratio,
        "original_length": len(text),
        "filtered_length": len(filtered_text),
        "compression_ratio": len(filtered_text) / len(text) if text else 0,
        "avg_score_kept": sum(kept_scores) / len(kept_scores) if kept_scores else 0,
        "avg_score_dropped": sum(dropped_scores) / len(dropped_scores) if dropped_scores else 0,
        "score_separation": (
            (sum(kept_scores) / len(kept_scores) - sum(dropped_scores) / len(dropped_scores))
            if kept_scores and dropped_scores else 0
        ),
        "top_distinctive_terms": [t for t, _ in all_top_terms.most_common(20)],
        "sample_kept": scored[0].text[:200] if scored else "",
        "sample_dropped": scored[-1].text[:200] if len(scored) > n_keep else "",
    }

    return filtered_text, diagnostics
