"""Thin LLM call wrapper with audit recording.

Supports both OpenAI Responses API and Anthropic Messages API.
All calls are recorded into the AuditLog for full reproducibility.

Backend is auto-detected from the client type.
"""

from __future__ import annotations

import time
from typing import Any

from infra.audit import AuditLog, StepRecord


def llm_call(
    client,
    model: str,
    system: str,
    user: str,
    audit: AuditLog,
    step_name: str,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    """Make a single LLM call and record it in the audit log.

    Auto-detects whether client is OpenAI or Anthropic.
    """
    backend = _detect_backend(client)
    t0 = time.time()

    if backend == "anthropic":
        text, input_tokens, output_tokens, resp_id = _call_anthropic(
            client, model, system, user, max_tokens, temperature
        )
    else:
        text, input_tokens, output_tokens, resp_id = _call_openai(
            client, model, system, user, max_tokens, temperature
        )

    duration = time.time() - t0

    step = StepRecord(
        step_name=step_name,
        model=model,
        system_prompt=system,
        user_prompt=user,
        response=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_seconds=round(duration, 2),
        metadata={"response_id": resp_id, "backend": backend},
    )
    audit.add_step(step)
    return text


def _detect_backend(client) -> str:
    """Detect whether client is OpenAI or Anthropic."""
    module = type(client).__module__
    if "anthropic" in module:
        return "anthropic"
    return "openai"


def _call_anthropic(
    client, model: str, system: str, user: str,
    max_tokens: int, temperature: float,
) -> tuple[str, int, int, str]:
    """Call the Anthropic Messages API."""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
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
) -> tuple[str, int, int, str]:
    """Call the OpenAI Responses API."""
    response = client.responses.create(
        model=model,
        instructions=system,
        input=user,
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
