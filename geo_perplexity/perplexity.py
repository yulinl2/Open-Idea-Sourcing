"""Exact conditional perplexity via verbatim-echo with logprobs.

Computes PPL(target | context) by instructing the model to reproduce the
target text verbatim.  The logprobs of each reproduced token ARE the
conditional probabilities P(token_i | context, token_1..i-1), giving us
the true perplexity — not an approximation.

For long texts the target is chunked into windows (~800 tokens each).
Each window is echoed in a separate API call with the context + all
preceding target text in the prompt.  Logprobs are collected across all
windows and averaged.

PPL = exp( −(1/N) Σ log p(token_i) )
"""

from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import tiktoken

_MAX_CONTEXT_TOKENS = 6000   # context paper budget
_CHUNK_TOKENS = 800          # target text per echo window
_MAX_RETRIES = 3
_RETRY_BASE = 2.0

# System prompt: the model's ONLY job is to echo text verbatim.
_SYSTEM_TEMPLATE = """\
You are a precise text reproduction system.  You have been given a \
reference paper for context.  Your ONLY task is to reproduce the target \
text EXACTLY — character for character, preserving all whitespace and \
punctuation.  Output NOTHING else: no commentary, no corrections, no \
formatting changes.

--- REFERENCE PAPER ---
{context_text}
--- END REFERENCE ---"""

_USER_TEMPLATE = """\
Reproduce the following target text EXACTLY.  Output only the target \
text, nothing else.

--- TARGET TEXT ---
{chunk_text}
--- END ---"""


def _get_encoding(model: str) -> tiktoken.Encoding:
    """Return the best-guess tiktoken encoding for a model."""
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def _truncate(text: str, max_tokens: int, enc: tiktoken.Encoding) -> str:
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])


def _chunk_text(text: str, chunk_tokens: int, enc: tiktoken.Encoding) -> list[str]:
    """Split text into chunks of approximately chunk_tokens tokens.

    Splits on sentence boundaries ('. ', '\\n') when possible so the
    model sees coherent fragments.
    """
    tokens = enc.encode(text)
    if len(tokens) <= chunk_tokens:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_tokens, len(tokens))
        chunk = enc.decode(tokens[start:end])

        # Try to split at a sentence boundary near the end
        if end < len(tokens):
            for sep in [". ", ".\n", "\n\n", "\n", "; ", ", "]:
                last = chunk.rfind(sep)
                if last > len(chunk) // 2:
                    chunk = chunk[: last + len(sep)]
                    end = start + len(enc.encode(chunk))
                    break

        chunks.append(chunk)
        start = end

    return chunks


@dataclass
class PerplexityResult:
    """Result of a single perplexity estimation."""

    context_id: str
    context_title: str
    model: str
    perplexity: float
    avg_logprob: float
    n_tokens: int
    n_chunks: int
    context_type: str  # "cited", "self", "random"
    error: str = ""
    context_source: str = ""  # "abstract", "tldr", "full_text_llm", "full_text_raw"
    context_tokens: int = 0  # token count of the context text used


def _echo_one_chunk(
    context_text: str,
    chunk_text: str,
    model: str,
    client,
    enc: tiktoken.Encoding,
) -> tuple[list[float], str]:
    """Echo a single chunk and return (logprobs_list, error_string)."""
    system_msg = _SYSTEM_TEMPLATE.format(context_text=context_text)
    user_msg = _USER_TEMPLATE.format(chunk_text=chunk_text)

    # Budget: the chunk might be up to _CHUNK_TOKENS, but the model may
    # produce slightly more or fewer tokens.  Give 20 % headroom.
    max_out = int(len(enc.encode(chunk_text)) * 1.2) + 32

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=max_out,
                temperature=0.0,
                logprobs=True,
                top_logprobs=1,
            )

            choice = response.choices[0]
            if not choice.logprobs or not choice.logprobs.content:
                return [], "No logprobs returned by API"

            return [t.logprob for t in choice.logprobs.content], ""

        except Exception as exc:
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BASE * (2 ** (attempt - 1)))
                continue
            return [], str(exc)


def estimate_perplexity(
    context_text: str,
    target_text: str,
    model: str,
    client,
    context_id: str = "",
    context_title: str = "",
    context_type: str = "cited",
) -> PerplexityResult:
    """Compute exact PPL(target_text | context_text) via verbatim echo.

    The target text is chunked, each chunk is echoed by the model with
    logprobs=True, and the token-level log-probabilities are aggregated
    across all chunks into a single perplexity score.
    """
    enc = _get_encoding(model)

    # Truncate context to budget
    ctx = _truncate(context_text, _MAX_CONTEXT_TOKENS, enc)

    # Chunk the target
    chunks = _chunk_text(target_text, _CHUNK_TOKENS, enc)

    all_logprobs: list[float] = []
    errors: list[str] = []

    for i, chunk in enumerate(chunks):
        lps, err = _echo_one_chunk(ctx, chunk, model, client, enc)
        if err:
            errors.append(f"chunk {i + 1}/{len(chunks)}: {err}")
        all_logprobs.extend(lps)

        # Rate-limit between chunks
        if i < len(chunks) - 1:
            time.sleep(0.3)

    n_tokens = len(all_logprobs)
    if n_tokens == 0:
        return PerplexityResult(
            context_id=context_id,
            context_title=context_title,
            model=model,
            perplexity=float("nan"),
            avg_logprob=float("nan"),
            n_tokens=0,
            n_chunks=len(chunks),
            context_type=context_type,
            error="; ".join(errors) or "zero tokens collected",
        )

    avg_lp = sum(all_logprobs) / n_tokens
    # Clamp to avoid overflow: logprobs are negative, so -avg_lp is
    # positive.  math.exp can overflow for very large values.
    clamped = min(-avg_lp, 700)  # e^700 ≈ 1e304, near float64 max
    ppl = math.exp(clamped)

    return PerplexityResult(
        context_id=context_id,
        context_title=context_title,
        model=model,
        perplexity=ppl,
        avg_logprob=avg_lp,
        n_tokens=n_tokens,
        n_chunks=len(chunks),
        context_type=context_type,
        error="; ".join(errors) if errors else "",
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

    Returns one PerplexityResult per (context, model) pair.
    """
    results: list[PerplexityResult] = []

    # (text, id, title, type, source)
    contexts: list[tuple[str, str, str, str, str]] = []

    # Self-perplexity
    contexts.append((target_text, "self", "Target paper (self)", "self", "self"))

    # Each cited paper
    for paper in cited_papers:
        if paper.has_content:
            contexts.append((
                paper.best_text,
                paper.paper_id or paper.arxiv_id,
                paper.title,
                "cited",
                getattr(paper, "content_source", "") or "",
            ))

    # Random reference
    if random_ref and random_ref.has_content:
        contexts.append((
            random_ref.best_text,
            random_ref.paper_id or random_ref.arxiv_id,
            random_ref.title,
            "random",
            getattr(random_ref, "content_source", "") or "",
        ))

    total = len(contexts) * len(models)
    done = 0

    for ctx_text, ctx_id, ctx_title, ctx_type, ctx_source in contexts:
        enc = _get_encoding(models[0])
        ctx_tok_count = len(enc.encode(ctx_text))
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
            result.context_source = ctx_source
            result.context_tokens = ctx_tok_count
            results.append(result)
            done += 1

            if progress_callback:
                progress_callback(done, total)

            ppl_str = f"{result.perplexity:.2f}" if math.isfinite(result.perplexity) else "ERROR"
            print(
                f"  [perplexity] {done}/{total}: {model} | "
                f"{ctx_type}:{ctx_title[:40]}… → PPL={ppl_str} "
                f"({result.n_tokens}tok, {result.n_chunks}chunks)",
                file=sys.stderr,
            )

            # Delay between full evaluations
            time.sleep(0.5)

    return results
