"""Teacher evaluation of student reconstructions.

The teacher model scores each student output on multiple dimensions,
enabling quantitative comparison across conditions and modes.

Supports two evaluation modes:
- Independent scoring: each output scored individually against the original
- Pairwise comparison: two outputs (with_refs vs no_refs) compared side-by-side
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

Rate each dimension from 1 (poor) to 5 (excellent). USE THE FULL RANGE.
Do not default to 2 or 3 for everything — carefully compare the student's
work to the original paper and discriminate between levels.

1. **problem_understanding** (1-5): Does the student correctly identify and
   articulate the core research problem?
   - 5 = precisely identifies the exact problem the paper addresses, including subtle aspects
   - 4 = correctly identifies the main problem but misses nuances
   - 3 = identifies a related problem in the right area
   - 2 = vaguely in the right field but misframes the specific problem
   - 1 = completely misidentifies the problem

2. **technical_depth** (1-5): Is the technical content (math, algorithms,
   proofs) at a publishable level of rigor?
   - 5 = rigorous proofs/derivations at the level of the original paper
   - 4 = mostly rigorous with minor gaps
   - 3 = correct high-level math but lacks detailed derivations
   - 2 = math is present but hand-wavy or contains errors
   - 1 = no meaningful technical content

3. **novelty_alignment** (1-5): How well does the student's proposed approach
   align with the actual paper's KEY INSIGHT — the core mechanism or idea
   that makes the paper's contribution non-obvious?

   IMPORTANT: First identify the paper's key insight in one sentence. Then
   check whether the student's approach contains that SPECIFIC mechanism.
   Do not give a 2 just because the student "proposes something generic" —
   distinguish between:

   - 5 = independently arrived at essentially the same core mechanism
         (e.g., both use weighted conformal inference for counterfactual bounds)
   - 4 = captured the main direction but missed important specifics
         (e.g., uses conformal methods for treatment effects but different weighting)
   - 3 = related approach in the right subfield but different mechanism
         (e.g., uses conformal prediction but for a different purpose)
   - 2 = generic approach that doesn't capture what's novel
         (e.g., proposes ensemble methods with no conformal component)
   - 1 = completely different direction or fundamentally misunderstands
         (e.g., proposes a deep learning architecture for a statistical problem)

4. **writing_quality** (1-5): Is the output well-organized, clearly written,
   and at the level expected for the reconstruction type?

5. **completeness** (1-5): Does the output cover all aspects expected for
   this reconstruction type?

## Also provide

- **key_insight_identified**: State the original paper's key insight in ONE
  sentence. Then state whether the student captured it (yes/partially/no).
- **novelty_gap**: The specific delta between the student's approach and the
  paper's actual contribution. What did the paper do that the student's
  reconstruction does NOT capture? Be precise about the mechanism.
- **reconstruction_difficulty**: Rate 1-5 how much GENUINE INSIGHT was required
  to go from the problem statement + available references to the paper's actual
  approach. Consider:
  - 1 = the paper's approach is a straightforward application of the references
  - 2 = requires combining known techniques in a somewhat obvious way
  - 3 = requires a non-trivial conceptual step beyond the references
  - 4 = requires significant creative insight not suggested by the references
  - 5 = the approach is a completely novel conceptual framework
- **reference_impact**: If the student was given references, did they
  substantively USE them to get closer to the paper's approach? (yes/no/partial/N/A)
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
  "key_insight_identified": "Paper's key insight: ... Student captured: yes/partially/no",
  "novelty_alignment_rationale": "1-2 sentences explaining the novelty_alignment score",
  "novelty_gap": "...",
  "reconstruction_difficulty": <1-5>,
  "reference_impact": "yes/no/partial/N/A",
  "strongest_aspect": "...",
  "weakest_aspect": "..."
}
```
"""


PAIRWISE_PROMPT = """\
You are the Teacher in a controlled experiment comparing two student attempts
to reconstruct the same research paper. One student had access to REFERENCE
PAPERS (Output A), the other had NO REFERENCES (Output B).

Your job: determine whether the references helped the student get closer
to the original paper's contribution.

## Instructions

1. First, identify the original paper's KEY INSIGHT in one sentence.
2. Read both outputs carefully.
3. For each output, assess whether it captures the key insight.
4. Compare them directly: did references help, hurt, or make no difference?

IMPORTANT: Do NOT assume references always help. If the reference is UNRELATED
to the paper, it should have zero or negative impact. Report what you actually see.

Use the full 1-7 scale — do NOT default to the middle:
- 7 = A is dramatically better (references clearly helped achieve core insight)
- 6 = A is substantially better
- 5 = A is somewhat better
- 4 = No meaningful difference (references didn't help)
- 3 = B is somewhat better (references may have distracted)
- 2 = B is substantially better
- 1 = B is dramatically better (references actively hurt)

## Output format

```json
{
  "paper_key_insight": "One sentence describing the original paper's core contribution",
  "output_a_captures_insight": "yes/partially/no — explain briefly",
  "output_b_captures_insight": "yes/partially/no — explain briefly",
  "reference_impact_score": <1-7>,
  "reference_impact_rationale": "2-3 sentences explaining the comparison",
  "output_a_unique_strengths": "What A does that B doesn't",
  "output_b_unique_strengths": "What B does that A doesn't",
  "which_is_closer_to_original": "A/B/tied",
  "confidence": "high/medium/low"
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
    previous_response_id: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Teacher evaluates a single student reconstruction.

    Returns (parsed_eval_dict, response_id). The response_id can be passed
    back to chain subsequent evaluation calls for the same mode/paper.
    """
    # Paper text is stable across rounds — cache it as prefix
    paper_prefix = (
        f"## Reconstruction type: {mode}\n"
        f"## Condition: {condition}\n\n"
        f"## Original paper (first 30k chars)\n\n"
        f"{paper_text[:30_000]}"
    )
    user_msg = f"## Student output\n\n{student_output}\n"

    response, resp_id = llm_call(
        client, teacher_model,
        system=EVAL_PROMPT,
        user=user_msg,
        audit=audit,
        step_name=f"evaluate_{condition}_{mode}",
        max_tokens=1024,
        temperature=0.2,
        cache_user_prefix=paper_prefix,
        previous_response_id=previous_response_id,
    )

    return _parse_eval(response), resp_id


def evaluate_pairwise(
    client,
    teacher_model: str,
    paper_text: str,
    output_with_refs: str,
    output_no_refs: str,
    mode: str,
    audit: AuditLog,
) -> dict[str, Any]:
    """Compare with_refs vs no_refs outputs side-by-side.

    Returns the parsed pairwise comparison dict.
    """
    # Paper text is stable — cache it
    paper_prefix = (
        f"## Reconstruction type: {mode}\n\n"
        f"## Original paper (first 30k chars)\n\n"
        f"{paper_text[:30_000]}"
    )
    user_msg = (
        f"## Output A (student WITH reference papers)\n\n"
        f"{output_with_refs[:15_000]}\n\n"
        f"## Output B (student WITHOUT reference papers)\n\n"
        f"{output_no_refs[:15_000]}\n"
    )

    response, _ = llm_call(
        client, teacher_model,
        system=PAIRWISE_PROMPT,
        user=user_msg,
        audit=audit,
        step_name=f"pairwise_{mode}",
        max_tokens=1024,
        temperature=0.2,
        cache_user_prefix=paper_prefix,
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
