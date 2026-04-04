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

## Context

The Student was given only a problem description (no solution details) and
possibly some reference papers. They were NOT shown the original paper. Your
job is to evaluate how close their reconstruction came to the actual paper's
contribution.

## Scoring rubric

Rate each dimension from 1 (poor) to 5 (excellent):

1. **problem_understanding** (1-5): Does the student correctly identify and
   articulate the core research problem?

2. **technical_depth** (1-5): Is the technical content (math, algorithms,
   proofs) at a publishable level of rigor?

3. **novelty_alignment** (1-5): How well does the student's proposed approach
   align with the actual paper's KEY INSIGHT — the core mechanism or idea
   that makes the paper's contribution non-obvious? Focus on conceptual
   alignment, not surface similarity.
   - 5 = independently arrived at essentially the same core mechanism
   - 4 = captured the main direction but missed important specifics
   - 3 = related approach in the right subfield but different mechanism
   - 2 = generic approach that doesn't capture what's novel about the paper
   - 1 = completely different direction or fundamentally misunderstands

4. **writing_quality** (1-5): Is the output well-organized, clearly written,
   and at the level expected for the reconstruction type?

5. **completeness** (1-5): Does the output cover all aspects expected for
   this reconstruction type?

## Also provide

- **novelty_gap**: The specific delta between the student's approach and the
  paper's actual contribution. What did the paper do that the student's
  reconstruction does NOT capture? Be precise about the mechanism or insight.
- **reconstruction_difficulty**: Rate 1-5 how much GENUINE INSIGHT was required
  to go from the problem statement + available references to the paper's actual
  approach. (1 = trivially derivable, 5 = highly non-obvious creative leap)
- **strongest_aspect**: What the student did best.
- **weakest_aspect**: Where the student fell most short.

## Output format

```json
{
  "scores": {
    "problem_understanding": <1-5>,
    "technical_depth": <1-5>,
    "novelty_alignment": <1-5>,
    "writing_quality": <1-5>,
    "completeness": <1-5>
  },
  "composite_score": <average of the 5 scores above, 1 decimal>,
  "novelty_alignment_rationale": "1-2 sentences explaining the novelty_alignment score",
  "novelty_gap": "...",
  "reconstruction_difficulty": <1-5>,
  "strongest_aspect": "...",
  "weakest_aspect": "..."
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
