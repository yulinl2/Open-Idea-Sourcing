"""Thin LLM call wrapper with audit recording.

Supports both OpenAI Responses API and Anthropic Messages API.
All calls are recorded into the AuditLog for full reproducibility.

Backend is auto-detected from the client type.
Includes retry-with-backoff for rate limit (429) errors.

Caching strategies:
- Anthropic: system prompts and large stable user-message prefixes are
  marked with cache_control (ephemeral) to avoid re-processing.
- OpenAI: stateful multi-turn via previous_response_id chains repeated
  context (paper text, round history) across calls within a mode.
"""

from __future__ import annotations

import time
from typing import Any

from infra.audit import AuditLog, StepRecord

# Retry config for 429 rate limits
MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 30  # 30s, 60s, 120s, 240s

# Minimum token count to bother caching a user-message prefix block.
# Anthropic requires cached blocks to be ≥1024 tokens for Sonnet, ≥2048 for Opus.
# We use 1024 as a safe floor; the API will silently ignore the marker if too small.
_MIN_CACHE_TOKENS_APPROX = 1024
_CHARS_PER_TOKEN_APPROX = 4  # rough estimate for cache eligibility check


def create_context_seed(
    client,
    model: str,
    paper_text: str,
    audit: AuditLog,
    paper_id: str = "",
) -> str | None:
    """Create a paper-context seed response for cross-call context sharing.

    OpenAI path: sends a minimal prompt with the paper text, returns a
    response_id that subsequent calls can reference via previous_response_id.
    This means the paper text (often 30K+ chars) is processed exactly once
    per paper, then reused across all modes, rounds, and call types.

    Anthropic path: returns None. Anthropic's cache_control with ephemeral
    TTL (5 min) already handles cross-call caching automatically — no
    explicit seed is needed.
    """
    backend = _detect_backend(client)
    if backend == "anthropic":
        return None  # cache_control handles this

    # OpenAI: create a seed response with paper text
    t0 = time.time()
    seed_system = (
        "You are a research paper analysis system. "
        "Acknowledge receipt of the paper context below. "
        "Respond with only: CONTEXT_LOADED"
    )
    seed_user = f"## Paper context (first 30k chars)\n\n{paper_text[:30_000]}"

    try:
        response = client.responses.create(
            model=model,
            instructions=seed_system,
            input=seed_user,
            max_output_tokens=16,
            temperature=0.0,
        )
        resp_id = getattr(response, "id", "")
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, "usage") and response.usage:
            input_tokens = getattr(response.usage, "input_tokens", 0) or 0
            output_tokens = getattr(response.usage, "output_tokens", 0) or 0

        duration = time.time() - t0
        step = StepRecord(
            step_name="create_context_seed",
            model=model,
            system_prompt=seed_system,
            user_prompt=f"[paper context for {paper_id}, {len(seed_user)} chars]",
            response="CONTEXT_LOADED",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_seconds=round(duration, 2),
            metadata={"response_id": resp_id, "backend": backend,
                       "paper_id": paper_id},
        )
        audit.add_step(step)
        print(f"  [seed] Paper context seeded ({input_tokens} input tokens, "
              f"resp_id={resp_id[:20]}...)")
        return resp_id
    except Exception as e:
        print(f"  [seed] Failed to create context seed: {e}")
        return None


def llm_call(
    client,
    model: str,
    system: str,
    user: str,
    audit: AuditLog,
    step_name: str,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    cache_user_prefix: str | None = None,
    previous_response_id: str | None = None,
) -> tuple[str, str]:
    """Make a single LLM call and record it in the audit log.

    Auto-detects whether client is OpenAI or Anthropic.
    Retries up to MAX_RETRIES times on rate limit errors with exponential backoff.

    Args:
        cache_user_prefix: (Anthropic) Sent as a separate cached content block
            BEFORE the main user message. Use for large stable content (paper
            text) that repeats across calls.
        previous_response_id: (OpenAI) Chain this call to a previous response,
            enabling the API to reuse cached context. When set, only the new
            user message is sent — the API already has prior turns in memory.

    Returns:
        (response_text, response_id) — response_id can be passed as
        previous_response_id to subsequent calls for stateful chaining.
    """
    backend = _detect_backend(client)
    t0 = time.time()

    call_fn = _call_anthropic if backend == "anthropic" else _call_openai
    text, input_tokens, output_tokens, resp_id = _call_with_retry(
        call_fn, client, model, system, user, max_tokens, temperature,
        step_name, cache_user_prefix, previous_response_id,
    )

    duration = time.time() - t0

    # For audit, combine prefix + user into a single string
    full_user = f"{cache_user_prefix}\n\n{user}" if cache_user_prefix else user

    step = StepRecord(
        step_name=step_name,
        model=model,
        system_prompt=system,
        user_prompt=full_user,
        response=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_seconds=round(duration, 2),
        metadata={
            "response_id": resp_id,
            "backend": backend,
            "chained_from": previous_response_id or "",
        },
    )
    audit.add_step(step)
    return text, resp_id


def _call_with_retry(call_fn, client, model, system, user, max_tokens,
                     temperature, step_name, cache_user_prefix=None,
                     previous_response_id=None):
    """Retry an LLM call on rate limit errors with exponential backoff."""
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return call_fn(client, model, system, user, max_tokens,
                           temperature, cache_user_prefix, previous_response_id)
        except Exception as e:
            if _is_rate_limit(e) and attempt < MAX_RETRIES:
                wait = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                print(f"  [retry] {step_name}: rate limited, waiting {wait}s "
                      f"(attempt {attempt + 1}/{MAX_RETRIES})...")
                time.sleep(wait)
                last_err = e
            else:
                raise
    raise last_err  # unreachable, but satisfies type checkers


def _is_rate_limit(e: Exception) -> bool:
    """Check if an exception is a rate limit error (429)."""
    # Anthropic SDK
    if type(e).__name__ == "RateLimitError":
        return True
    # Check for status_code attribute
    if hasattr(e, "status_code") and getattr(e, "status_code") == 429:
        return True
    # OpenAI SDK
    if "429" in str(e) and "rate" in str(e).lower():
        return True
    return False


def _detect_backend(client) -> str:
    """Detect whether client is OpenAI or Anthropic."""
    module = type(client).__module__
    if "anthropic" in module:
        return "anthropic"
    return "openai"


def _call_anthropic(
    client, model: str, system: str, user: str,
    max_tokens: int, temperature: float,
    cache_user_prefix: str | None = None,
    previous_response_id: str | None = None,
) -> tuple[str, int, int, str]:
    """Call the Anthropic Messages API with prompt caching.

    Note: previous_response_id is ignored for Anthropic (stateless API).
    Caching is handled via cache_control markers instead.
    """
    # System prompt: use content-block format with cache_control
    system_blocks = [
        {
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    # User message: optionally split into cached prefix + dynamic suffix
    if cache_user_prefix and len(cache_user_prefix) > _MIN_CACHE_TOKENS_APPROX * _CHARS_PER_TOKEN_APPROX:
        user_content = [
            {
                "type": "text",
                "text": cache_user_prefix,
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": user,
            },
        ]
    else:
        # No prefix or prefix too small to cache — send as single block.
        if cache_user_prefix:
            user_content = f"{cache_user_prefix}\n\n{user}"
        else:
            user_content = user

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_blocks,
        messages=[{"role": "user", "content": user_content}],
    )
    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text

    input_tokens = getattr(response.usage, "input_tokens", 0) or 0
    output_tokens = getattr(response.usage, "output_tokens", 0) or 0
    resp_id = getattr(response, "id", "")
    return text, input_tokens, output_tokens, resp_id


def _call_openai(
    client, model: str, system: str, user: str,
    max_tokens: int, temperature: float,
    cache_user_prefix: str | None = None,
    previous_response_id: str | None = None,
) -> tuple[str, int, int, str]:
    """Call the OpenAI Responses API with optional stateful chaining.

    When previous_response_id is set, the API reuses cached context from
    the referenced response. Only the new user input needs to be sent,
    dramatically reducing input tokens for repeated-context scenarios
    like iterative refinement rounds.
    """
    full_user = f"{cache_user_prefix}\n\n{user}" if cache_user_prefix else user

    kwargs: dict[str, Any] = {
        "model": model,
        "input": full_user,
        "max_output_tokens": max_tokens,
        "temperature": temperature,
    }

    if previous_response_id:
        # Stateful chain: API already has system + prior turns in memory.
        # We still pass instructions for safety, but input tokens for the
        # cached prefix are not re-charged.
        kwargs["previous_response_id"] = previous_response_id
        kwargs["instructions"] = system
    else:
        kwargs["instructions"] = system

    response = client.responses.create(**kwargs)
    text = _extract_openai_text(response)

    input_tokens = 0
    output_tokens = 0
    if hasattr(response, "usage") and response.usage:
        input_tokens = getattr(response.usage, "input_tokens", 0) or 0
        output_tokens = getattr(response.usage, "output_tokens", 0) or 0

    resp_id = getattr(response, "id", "")
    return text, input_tokens, output_tokens, resp_id


def _extract_openai_text(response: Any) -> str:
    """Extract text from an OpenAI Responses API response."""
    if hasattr(response, "output_text") and response.output_text:
        return str(response.output_text)
    if hasattr(response, "output"):
        for item in response.output:
            if hasattr(item, "type") and item.type == "message":
                for block in item.content:
                    if hasattr(block, "type") and block.type == "output_text":
                        return block.text
    return str(getattr(response, "output", ""))
