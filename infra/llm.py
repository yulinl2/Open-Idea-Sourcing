"""Thin LLM call wrapper with audit recording.

Supports both OpenAI Responses API and Anthropic Messages API.
All calls are recorded into the AuditLog for full reproducibility.

Backend is auto-detected from the client type.
Includes retry-with-backoff for rate limit (429) errors.

Anthropic prompt caching: system prompts and large stable user-message
prefixes are marked with cache_control to avoid re-processing repeated
content across rounds. See https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
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
) -> str:
    """Make a single LLM call and record it in the audit log.

    Auto-detects whether client is OpenAI or Anthropic.
    Retries up to MAX_RETRIES times on rate limit errors with exponential backoff.

    Args:
        cache_user_prefix: If provided, this string is sent as a separate
            content block BEFORE the main user message, marked for Anthropic
            prompt caching. Use for large stable content (paper text, reference
            text, round history prefix) that repeats across calls.
    """
    backend = _detect_backend(client)
    t0 = time.time()

    call_fn = _call_anthropic if backend == "anthropic" else _call_openai
    text, input_tokens, output_tokens, resp_id = _call_with_retry(
        call_fn, client, model, system, user, max_tokens, temperature,
        step_name, cache_user_prefix,
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
        metadata={"response_id": resp_id, "backend": backend},
    )
    audit.add_step(step)
    return text


def _call_with_retry(call_fn, client, model, system, user, max_tokens,
                     temperature, step_name, cache_user_prefix=None):
    """Retry an LLM call on rate limit errors with exponential backoff."""
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return call_fn(client, model, system, user, max_tokens,
                           temperature, cache_user_prefix)
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
) -> tuple[str, int, int, str]:
    """Call the Anthropic Messages API with prompt caching.

    Caching strategy:
    - System prompt is always marked for caching (it repeats across all calls
      of the same type within a run).
    - If cache_user_prefix is provided, it's sent as a separate content block
      before the main user message, also marked for caching. This is useful
      for large stable content like paper text or reference text.
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
        # If the user message itself is large, still just a plain string.
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
) -> tuple[str, int, int, str]:
    """Call the OpenAI Responses API."""
    # OpenAI handles caching automatically; just combine prefix + user
    full_user = f"{cache_user_prefix}\n\n{user}" if cache_user_prefix else user
    response = client.responses.create(
        model=model,
        instructions=system,
        input=full_user,
        max_output_tokens=max_tokens,
        temperature=temperature,
    )
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
