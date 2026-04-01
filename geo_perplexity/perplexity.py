"""Conditional perplexity estimation using OpenAI chat completions with logprobs.

Estimates PPL(target | context) by:
1. Placing the context paper in the system message
2. Placing the first ~40% of the target paper as a user-message prefix
3. Generating a continuation with logprobs=True
4. Computing PPL = exp(-mean(token_logprobs))

Lower PPL → target is more predictable given context → less novel.
Higher PPL → target is surprising given context → more novel.
"""

from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass
from typing import Optional

import tiktoken

_MAX_CONTEXT_TOKENS = 4000   # truncate context paper to this
_MAX_PREFIX_TOKENS = 3000    # first ~40% of target as prefix
_GENERATION_TOKENS = 500     # tokens to generate for logprob sampling
_MAX_RETRIES = 3
_RETRY_BASE = 2.0

# System prompt for perplexity estimation
_SYSTEM_TEMPLATE = """\
You are an expert academic writer continuing a research paper. You have read \
the following reference paper for context:

--- REFERENCE PAPER ---
{context_text}
--- END REFERENCE ---

Continue the target paper text below exactly as it would naturally proceed. \
Output ONLY the continuation text, no meta-commentary."""


@dataclass
class PerplexityResult:
    """Result of a single perplexity estimation."""

    context_id: str
    context_title: str
    model: str
    perplexity: float
    avg_logprob: float
    n_tokens: int
    context_type: str  # "cited", "self", "random"
    error: str = ""


def _truncate_to_tokens(text: str, max_tokens: int, encoding_name: str = "cl100k_base") -> str:
    """Truncate text to a maximum number of tokens."""
    try:
        enc = tiktoken.get_encoding(encoding_name)
    except Exception:
        # Rough fallback: ~4 chars per token
        return text[: max_tokens * 4]

    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])


def _split_target(text: str, prefix_ratio: float = 0.4) -> tuple[str, str]:
    """Split target text into prefix (for prompt) and remainder."""
    split_point = int(len(text) * prefix_ratio)
    # Find a sentence boundary near the split point
    for i in range(split_point, min(split_point + 500, len(text))):
        if text[i] in ".!?\n":
            split_point = i + 1
            break
    return text[:split_point], text[split_point:]


def estimate_perplexity(
    context_text: str,
    target_text: str,
    model: str,
    client,  # openai.OpenAI instance
    context_id: str = "",
    context_title: str = "",
    context_type: str = "cited",
) -> PerplexityResult:
    """Estimate perplexity of target_text conditioned on context_text.

    Parameters
    ----------
    context_text:
        The reference/context paper text.
    target_text:
        The target paper text whose perplexity we measure.
    model:
        OpenAI model name (e.g., "gpt-5.4", "gpt-4o").
    client:
        An openai.OpenAI client instance.
    context_id:
        Identifier for the context paper (for reporting).
    context_title:
        Title of the context paper (for reporting).
    context_type:
        One of "cited", "self", "random".

    Returns
    -------
    PerplexityResult
        Contains the estimated perplexity and metadata.
    """
    # Truncate context
    ctx = _truncate_to_tokens(context_text, _MAX_CONTEXT_TOKENS)
    system_msg = _SYSTEM_TEMPLATE.format(context_text=ctx)

    # Split target into prefix (prompt) and what we want to predict
    prefix, _ = _split_target(target_text)
    prefix = _truncate_to_tokens(prefix, _MAX_PREFIX_TOKENS)

    user_msg = f"Continue this paper:\n\n{prefix}"

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=_GENERATION_TOKENS,
                temperature=0.0,
                logprobs=True,
                top_logprobs=1,
            )

            # Extract logprobs
            choice = response.choices[0]
            if not choice.logprobs or not choice.logprobs.content:
                return PerplexityResult(
                    context_id=context_id,
                    context_title=context_title,
                    model=model,
                    perplexity=float("inf"),
                    avg_logprob=float("-inf"),
                    n_tokens=0,
                    context_type=context_type,
                    error="No logprobs returned",
                )

            logprobs = [t.logprob for t in choice.logprobs.content]
            n_tokens = len(logprobs)
            avg_logprob = sum(logprobs) / n_tokens if n_tokens > 0 else float("-inf")
            ppl = math.exp(-avg_logprob) if avg_logprob > float("-inf") else float("inf")

            return PerplexityResult(
                context_id=context_id,
                context_title=context_title,
                model=model,
                perplexity=ppl,
                avg_logprob=avg_logprob,
                n_tokens=n_tokens,
                context_type=context_type,
            )

        except Exception as exc:
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BASE * (2 ** (attempt - 1))
                print(
                    f"  [perplexity] {model} error ({exc}), retry {attempt}/{_MAX_RETRIES} "
                    f"in {delay:.0f}s",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue

            return PerplexityResult(
                context_id=context_id,
                context_title=context_title,
                model=model,
                perplexity=float("inf"),
                avg_logprob=float("-inf"),
                n_tokens=0,
                context_type=context_type,
                error=str(exc),
            )


def compute_all_perplexities(
    target_text: str,
    cited_papers: list,  # list[CitedPaper]
    random_ref: Optional[object],  # CitedPaper or None
    models: list[str],
    client,
    *,
    progress_callback=None,
) -> list[PerplexityResult]:
    """Compute perplexity for all (context, model) combinations.

    Parameters
    ----------
    target_text:
        Full text of the target paper.
    cited_papers:
        List of CitedPaper objects with full_text populated.
    random_ref:
        A CitedPaper from the broader field (not in cited list), or None.
    models:
        List of model names to evaluate.
    client:
        OpenAI client.
    progress_callback:
        Optional callable(done, total) for progress reporting.

    Returns
    -------
    list[PerplexityResult]
        One result per (context, model) pair.
    """
    results: list[PerplexityResult] = []

    # Build the list of all (context, type) pairs
    contexts: list[tuple[str, str, str, str]] = []  # (text, id, title, type)

    # Self-perplexity
    contexts.append((target_text, "self", "Target paper (self)", "self"))

    # Each cited paper
    for paper in cited_papers:
        if paper.has_content:
            contexts.append((
                paper.best_text,
                paper.paper_id or paper.arxiv_id,
                paper.title,
                "cited",
            ))

    # Random reference
    if random_ref and random_ref.has_content:
        contexts.append((
            random_ref.best_text,
            random_ref.paper_id or random_ref.arxiv_id,
            random_ref.title,
            "random",
        ))

    total = len(contexts) * len(models)
    done = 0

    for ctx_text, ctx_id, ctx_title, ctx_type in contexts:
        for model in models:
            result = estimate_perplexity(
                context_text=ctx_text,
                target_text=target_text,
                model=model,
                client=client,
                context_id=ctx_id,
                context_title=ctx_title,
                context_type=ctx_type,
            )
            results.append(result)
            done += 1

            if progress_callback:
                progress_callback(done, total)
            else:
                print(
                    f"  [perplexity] {done}/{total}: {model} | "
                    f"{ctx_type}:{ctx_title[:40]}... → PPL={result.perplexity:.2f}",
                    file=sys.stderr,
                )

            # Small delay to avoid rate limits
            time.sleep(0.5)

    return results
