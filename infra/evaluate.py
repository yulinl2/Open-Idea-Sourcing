"""Teacher evaluation of student reconstructions.

The teacher model scores each student output on multiple dimensions,
enabling quantitative comparison across conditions and modes.
"""

from __future__ import annotations

import json
import re
from typing import Any

from infra.audit import AuditLog
from infra.llm import llm_call

EVAL_PROMPT = """\
You are the Teacher evaluating a Student's attempt to reconstruct part of a
research paper. You have access to the ORIGINAL paper and the Student's output.

## Scoring rubric

Rate each dimension from 1 (poor) to 5 (excellent):

1. **problem_understanding** (1-5): Does the student correctly identify and
   articulate the core research problem?

2. **technical_depth** (1-5): Is the technical content (math, algorithms,
   proofs) at a publishable level of rigor?

3. **novelty_alignment** (1-5): How well does the student's proposed approach
   align with the actual paper's key insight? (5 = very close conceptually,
   1 = completely different direction)

4. **reference_usage** (1-5): Does the student effectively leverage the
   available references to build their argument? (Rate N/A as 3 if no
   references were provided.)

5. **writing_quality** (1-5): Is the output well-organized, clearly written,
   and at the level expected for the reconstruction type?

6. **completeness** (1-5): Does the output cover all aspects expected for
   this reconstruction type?

## Also provide

- **novelty_gap**: A brief explanation of what the student missed about the
  paper's actual contribution — the "delta" between what references suggest
  and what the paper actually does.
- **strongest_aspect**: What the student did best.
- **weakest_aspect**: Where the student fell most short.

## Output format

```json
{
  "scores": {
    "problem_understanding": <1-5>,
    "technical_depth": <1-5>,
    "novelty_alignment": <1-5>,
    "reference_usage": <1-5>,
    "writing_quality": <1-5>,
    "completeness": <1-5>
  },
  "composite_score": <average of all scores, 1 decimal>,
  "novelty_gap": "...",
  "strongest_aspect": "...",
  "weakest_aspect": "...",
  "brief_rationale": "1-2 sentence overall assessment"
}
```
"""


def evaluate_reconstruction(
    client,
    teacher_model: str,
    paper_text: str,
    student_output: str,
    mode: str,
    condition: str,
    audit: AuditLog,
) -> dict[str, Any]:
    """Teacher evaluates a single student reconstruction.

    Returns the parsed evaluation dict, or a fallback dict on parse failure.
    """
    user_msg = (
        f"## Reconstruction type: {mode}\n"
        f"## Condition: {condition}\n\n"
        f"## Original paper (first 30k chars)\n\n"
        f"{paper_text[:30_000]}\n\n"
        f"## Student output\n\n"
        f"{student_output}\n"
    )

    response = llm_call(
        client, teacher_model,
        system=EVAL_PROMPT,
        user=user_msg,
        audit=audit,
        step_name=f"evaluate_{condition}_{mode}",
        max_tokens=1024,
        temperature=0.2,
    )

    return _parse_eval(response)


def _parse_eval(text: str) -> dict[str, Any]:
    """Parse evaluation JSON from teacher response."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {
        "scores": {},
        "composite_score": 0,
        "novelty_gap": text[:500],
        "parse_error": True,
    }
