"""Exact conditional perplexity via verbatim-echo with logprobs.

Computes PPL(target | context) by instructing the model to reproduce the
target text verbatim.  The logprobs of each reproduced token ARE the
conditional probabilities P(token_i | context, token_1..i-1), giving us
the true perplexity — not an approximation.

For long texts the target is chunked into windows (~2000 tokens each).
Each window is echoed in a separate API call with the context in the
system prompt.  Logprobs are collected across all windows and averaged.

Multiple (context, model) evaluations run concurrently via a thread pool,
throttled by a token-budget rate limiter that tracks TPM consumption to
avoid 429 errors.

PPL = exp( −(1/N) Σ log p(token_i) )
"""

from __future__ import annotations

import math
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

import tiktoken

_MAX_CONTEXT_TOKENS = 6000   # context paper budget
_CHUNK_TOKENS = 2000         # target text per echo window (was 800)
_MAX_RETRIES = 4             # retry attempts (was 3)
_RETRY_BASE = 2.0
_MAX_CONCURRENT = 4          # max parallel API calls
_TPM_LIMIT = 25_000          # conservative TPM budget (headroom below 30K)

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


# ── Encoding cache ─────────────────────────────────────────────────
_encoding_cache: dict[str, tiktoken.Encoding] = {}
_encoding_lock = threading.Lock()


def _get_encoding(model: str) -> tiktoken.Encoding:
    """Return the best-guess tiktoken encoding for a model (cached)."""
    with _encoding_lock:
        if model not in _encoding_cache:
            try:
                _encoding_cache[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                _encoding_cache[model] = tiktoken.get_encoding("cl100k_base")
        return _encoding_cache[model]


# ── Token-budget rate limiter ──────────────────────────────────────

class _TokenBucketLimiter:
    """Thread-safe rate limiter that tracks tokens-per-minute usage.

    Callers ``acquire(n)`` before making an API call; the method blocks
    until the rolling 60-second token budget has room for *n* tokens.
    """

    def __init__(self, tpm_limit: int = _TPM_LIMIT):
        self._tpm_limit = tpm_limit
        self._lock = threading.Lock()
        self._log: list[tuple[float, int]] = []

    def acquire(self, tokens: int) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                # Expire entries older than 60 s
                self._log = [(t, n) for t, n in self._log if now - t < 60]
                used = sum(n for _, n in self._log)
                if used + tokens <= self._tpm_limit:
                    self._log.append((now, tokens))
                    return
            time.sleep(1.0)


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
    limiter: Optional[_TokenBucketLimiter] = None,
    *,
    _sys_token_count: int = 0,
) -> tuple[list[float], str]:
    """Echo a single chunk and return (logprobs_list, error_string).

    If *limiter* is provided, acquires token budget before each API call.
    *_sys_token_count* is the pre-computed token count of the system
    message (avoids re-encoding the same context for every chunk).
    """
    system_msg = _SYSTEM_TEMPLATE.format(context_text=context_text)
    user_msg = _USER_TEMPLATE.format(chunk_text=chunk_text)

    # Budget: the chunk might be up to _CHUNK_TOKENS, but the model may
    # produce slightly more or fewer tokens.  Give 20 % headroom.
    chunk_tok = len(enc.encode(chunk_text))
    max_out = int(chunk_tok * 1.2) + 32

    # Rate-limit: reserve estimated total tokens before calling the API
    if limiter:
        sys_tok = _sys_token_count or len(enc.encode(system_msg))
        user_tok = len(enc.encode(user_msg))
        limiter.acquire(sys_tok + user_tok + max_out)

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
                wait = _RETRY_BASE * (2 ** (attempt - 1))
                # Double the wait on rate-limit errors
                exc_str = str(exc)
                if "429" in exc_str or "rate_limit" in exc_str.lower():
                    wait *= 2
                time.sleep(wait)
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
    *,
    _chunks: Optional[list[str]] = None,
    _enc: Optional[tiktoken.Encoding] = None,
    _limiter: Optional[_TokenBucketLimiter] = None,
) -> PerplexityResult:
    """Compute exact PPL(target_text | context_text) via verbatim echo.

    The target text is chunked, each chunk is echoed by the model with
    logprobs=True, and the token-level log-probabilities are aggregated
    across all chunks into a single perplexity score.

    Optional kwargs (used by ``compute_all_perplexities`` for batching):
        _chunks:  pre-computed target chunks (avoids redundant tokenization)
        _enc:     pre-loaded tiktoken encoding
        _limiter: token-budget rate limiter (replaces fixed sleeps)
    """
    enc = _enc or _get_encoding(model)

    # Truncate context to budget
    ctx = _truncate(context_text, _MAX_CONTEXT_TOKENS, enc)

    # Chunk the target (use pre-computed chunks when available)
    chunks = _chunks or _chunk_text(target_text, _CHUNK_TOKENS, enc)

    # Pre-compute system-message token count once for the limiter
    sys_tok = len(enc.encode(_SYSTEM_TEMPLATE.format(context_text=ctx)))

    all_logprobs: list[float] = []
    errors: list[str] = []

    for i, chunk in enumerate(chunks):
        lps, err = _echo_one_chunk(
            ctx, chunk, model, client, enc, _limiter,
            _sys_token_count=sys_tok,
        )
        if err:
            errors.append(f"chunk {i + 1}/{len(chunks)}: {err}")
        all_logprobs.extend(lps)

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
    max_workers: int = _MAX_CONCURRENT,
    tpm_limit: int = _TPM_LIMIT,
) -> list[PerplexityResult]:
    """Compute perplexity for all (context, model) combinations.

    Uses a thread pool for concurrent API calls, throttled by a
    token-budget rate limiter that prevents 429 errors.  Target text
    is chunked once per model and reused across all evaluations.

    Returns one PerplexityResult per (context, model) pair.
    """
    limiter = _TokenBucketLimiter(tpm_limit)

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

    # ── Pre-compute per-model data (chunk once, encode once) ────────
    enc_by_model: dict[str, tiktoken.Encoding] = {}
    chunks_by_model: dict[str, list[str]] = {}
    for model in models:
        enc = _get_encoding(model)
        enc_by_model[model] = enc
        chunks_by_model[model] = _chunk_text(target_text, _CHUNK_TOKENS, enc)

    # Pre-compute context token counts (avoids redundant encoding in workers)
    ctx_tok_counts: dict[tuple[int, str], int] = {}
    for ci, (ctx_text, *_) in enumerate(contexts):
        for model in models:
            ctx_tok_counts[(ci, model)] = min(
                len(enc_by_model[model].encode(ctx_text)), _MAX_CONTEXT_TOKENS,
            )

    # ── Build job list, sorted by estimated cost (cheapest first) ───
    # Processing cheaper evaluations first fills TPM gaps efficiently
    # and lets us overlap small-context calls with rate-limit waits.
    jobs: list[tuple[int, int, str]] = []  # (est_tokens, ctx_idx, model)
    for ci in range(len(contexts)):
        for model in models:
            n_chunks = len(chunks_by_model[model])
            est = ctx_tok_counts[(ci, model)] * n_chunks
            jobs.append((est, ci, model))
    jobs.sort()

    total = len(jobs)
    done_count = [0]
    _progress_lock = threading.Lock()

    n_chunks_info = ", ".join(
        f"{m}={len(chunks_by_model[m])}ch" for m in models
    )
    print(
        f"  [perplexity] {total} evaluations, {n_chunks_info}, "
        f"workers={min(max_workers, total)}, tpm_limit={tpm_limit}",
        file=sys.stderr,
    )

    def _run_one(ci: int, model: str) -> PerplexityResult:
        ctx_text, ctx_id, ctx_title, ctx_type, ctx_source = contexts[ci]
        enc = enc_by_model[model]
        chunks = chunks_by_model[model]

        result = estimate_perplexity(
            context_text=ctx_text,
            target_text="",  # unused when _chunks is provided
            model=model,
            client=client,
            context_id=ctx_id,
            context_title=ctx_title,
            context_type=ctx_type,
            _chunks=chunks,
            _enc=enc,
            _limiter=limiter,
        )
        result.context_source = ctx_source
        result.context_tokens = ctx_tok_counts[(ci, model)]

        with _progress_lock:
            done_count[0] += 1
            ppl_str = (
                f"{result.perplexity:.2f}"
                if math.isfinite(result.perplexity) else "ERROR"
            )
            print(
                f"  [perplexity] {done_count[0]}/{total}: {model} | "
                f"{ctx_type}:{ctx_title[:40]}… → PPL={ppl_str} "
                f"({result.n_tokens}tok, {result.n_chunks}ch)",
                file=sys.stderr,
            )
            if progress_callback:
                progress_callback(done_count[0], total)

        return result

    # ── Execute concurrently ────────────────────────────────────────
    results: list[PerplexityResult] = []
    effective_workers = min(max_workers, total)

    if effective_workers <= 1:
        for _, ci, model in jobs:
            results.append(_run_one(ci, model))
    else:
        with ThreadPoolExecutor(max_workers=effective_workers) as pool:
            futures = {
                pool.submit(_run_one, ci, model): (ci, model)
                for _, ci, model in jobs
            }
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as exc:
                    ci, model = futures[future]
                    _, ctx_id, ctx_title, ctx_type, ctx_source = contexts[ci]
                    results.append(PerplexityResult(
                        context_id=ctx_id,
                        context_title=ctx_title,
                        model=model,
                        perplexity=float("nan"),
                        avg_logprob=float("nan"),
                        n_tokens=0,
                        n_chunks=0,
                        context_type=ctx_type,
                        error=f"worker exception: {exc}",
                        context_source=ctx_source,
                    ))

    return results
