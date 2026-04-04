"""Thin LLM call wrapper with audit recording.

Supports the OpenAI Responses API (openai>=1.0). All calls are recorded
into the AuditLog for full reproducibility.
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

    Uses the OpenAI Responses API. Returns the text output.
    """
    t0 = time.time()
    response = client.responses.create(
        model=model,
        instructions=system,
        input=user,
        max_output_tokens=max_tokens,
        temperature=temperature,
    )
    duration = time.time() - t0

    # Extract text from response
    text = _extract_text(response)

    # Extract token counts from usage
    input_tokens = 0
    output_tokens = 0
    if hasattr(response, "usage") and response.usage:
        input_tokens = getattr(response.usage, "input_tokens", 0) or 0
        output_tokens = getattr(response.usage, "output_tokens", 0) or 0

    step = StepRecord(
        step_name=step_name,
        model=model,
        system_prompt=system,
        user_prompt=user,
        response=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_seconds=round(duration, 2),
        metadata={"response_id": getattr(response, "id", "")},
    )
    audit.add_step(step)
    return text


def _extract_text(response: Any) -> str:
    """Extract text from an OpenAI Responses API response object."""
    # Try output_text shorthand first
    if hasattr(response, "output_text") and response.output_text:
        return str(response.output_text)
    # Walk output items
    if hasattr(response, "output"):
        for item in response.output:
            if hasattr(item, "type") and item.type == "message":
                for block in item.content:
                    if hasattr(block, "type") and block.type == "output_text":
                        return block.text
    return str(getattr(response, "output", ""))
