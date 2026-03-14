"""Core novelty evaluator — the heart of the system.

This module orchestrates three analysis passes using an LLM:

1. **Duplication detection** — is the paper essentially a copy of known work?
2. **Combination detection** — is the paper just assembling existing components
   without a unifying insight?
3. **Methodological equivalence** — does the paper re-derive a known method
   under different notation or framing?

Each pass is implemented as a prompt sent to a *callable* LLM backend so
that the class can be used with any provider (OpenAI, local models, stubs)
and is straightforward to test without live API calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .paper_parser import ParsedPaper
from .similarity_search import SimilarityResult


# Type alias for the LLM callable
LLMCallable = Callable[[str], str]


@dataclass
class NoveltyDimension:
    """Result of one novelty-analysis dimension."""

    name: str
    verdict: str        # e.g. "HIGH", "MEDIUM", "LOW", "UNCLEAR"
    explanation: str
    references: list[str] = field(default_factory=list)


@dataclass
class NoveltyReport:
    """Aggregated novelty evaluation for a single paper."""

    paper_title: str
    overall_verdict: str          # "NOVEL", "MARGINAL", "NOT_NOVEL"
    confidence: str               # "HIGH", "MEDIUM", "LOW"
    summary: str
    dimensions: list[NoveltyDimension] = field(default_factory=list)
    similar_papers: list[SimilarityResult] = field(default_factory=list)
    raw_llm_responses: dict[str, str] = field(default_factory=dict)


class NoveltyEvaluator:
    """Evaluate the genuine novelty of an academic paper.

    Parameters
    ----------
    llm:
        Callable that receives a prompt string and returns the LLM response.
        Example::

            import openai
            client = openai.OpenAI()
            def call_openai(prompt: str) -> str:
                r = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                )
                return r.choices[0].message.content

    top_k_similar:
        How many similar papers to surface from the reference store.
    similarity_threshold:
        Minimum cosine-similarity score to include a reference paper.
    """

    def __init__(
        self,
        llm: LLMCallable,
        top_k_similar: int = 5,
        similarity_threshold: float = 0.05,
    ) -> None:
        self._llm = llm
        self._top_k = top_k_similar
        self._threshold = similarity_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        paper: ParsedPaper,
        similar_papers: Optional[list[SimilarityResult]] = None,
    ) -> NoveltyReport:
        """Run all evaluation passes and return a :class:`NoveltyReport`.

        Parameters
        ----------
        paper:
            The parsed paper to evaluate.
        similar_papers:
            Pre-computed similarity results.  If *None*, LLM analysis
            proceeds without reference anchoring.
        """
        similar_papers = similar_papers or []
        content = paper.key_content()
        refs_text = self._format_references(similar_papers)
        raw: dict[str, str] = {}

        dup = self._check_duplication(content, refs_text, raw)
        combo = self._check_combination(content, refs_text, raw)
        equiv = self._check_equivalence(content, refs_text, raw)

        overall, confidence, summary = self._synthesise(
            paper.title, dup, combo, equiv, raw
        )

        return NoveltyReport(
            paper_title=paper.title,
            overall_verdict=overall,
            confidence=confidence,
            summary=summary,
            dimensions=[dup, combo, equiv],
            similar_papers=similar_papers,
            raw_llm_responses=raw,
        )

    # ------------------------------------------------------------------
    # Analysis passes
    # ------------------------------------------------------------------

    def _check_duplication(
        self, content: str, refs_text: str, raw: dict[str, str]
    ) -> NoveltyDimension:
        """Detect whether the paper directly duplicates existing work."""
        prompt = _DUPLICATION_PROMPT.format(
            paper_content=content, reference_papers=refs_text
        )
        response = self._llm(prompt)
        raw["duplication"] = response
        verdict, explanation, refs = _parse_dimension_response(response)
        return NoveltyDimension(
            name="Direct Duplication",
            verdict=verdict,
            explanation=explanation,
            references=refs,
        )

    def _check_combination(
        self, content: str, refs_text: str, raw: dict[str, str]
    ) -> NoveltyDimension:
        """Detect whether the paper is merely a combination of prior works."""
        prompt = _COMBINATION_PROMPT.format(
            paper_content=content, reference_papers=refs_text
        )
        response = self._llm(prompt)
        raw["combination"] = response
        verdict, explanation, refs = _parse_dimension_response(response)
        return NoveltyDimension(
            name="Simple Combination",
            verdict=verdict,
            explanation=explanation,
            references=refs,
        )

    def _check_equivalence(
        self, content: str, refs_text: str, raw: dict[str, str]
    ) -> NoveltyDimension:
        """Detect methodological equivalence to known methods."""
        prompt = _EQUIVALENCE_PROMPT.format(
            paper_content=content, reference_papers=refs_text
        )
        response = self._llm(prompt)
        raw["equivalence"] = response
        verdict, explanation, refs = _parse_dimension_response(response)
        return NoveltyDimension(
            name="Methodological Equivalence",
            verdict=verdict,
            explanation=explanation,
            references=refs,
        )

    def _synthesise(
        self,
        title: str,
        dup: NoveltyDimension,
        combo: NoveltyDimension,
        equiv: NoveltyDimension,
        raw: dict[str, str],
    ) -> tuple[str, str, str]:
        """Ask the LLM to synthesise the three dimension results."""
        prompt = _SYNTHESIS_PROMPT.format(
            paper_title=title,
            duplication_result=f"Verdict: {dup.verdict}\n{dup.explanation}",
            combination_result=f"Verdict: {combo.verdict}\n{combo.explanation}",
            equivalence_result=f"Verdict: {equiv.verdict}\n{equiv.explanation}",
        )
        response = self._llm(prompt)
        raw["synthesis"] = response
        return _parse_synthesis_response(response)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_references(similar: list[SimilarityResult]) -> str:
        if not similar:
            return "No reference papers provided."
        lines = []
        for i, r in enumerate(similar, 1):
            p = r.paper
            lines.append(
                f"{i}. [{p.id}] {p.title} "
                f"({p.year or 'year unknown'}) — similarity {r.score:.2f}\n"
                f"   Abstract: {p.abstract[:300]}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_DUPLICATION_PROMPT = """You are a rigorous academic novelty reviewer.

TASK: Determine whether the submitted paper is a direct duplicate of any
known or referenced work. Direct duplication means the core ideas,
methods, or results are essentially identical to prior art, even if the
wording or framing differ.

SUBMITTED PAPER:
{paper_content}

REFERENCE PAPERS (most similar by text):
{reference_papers}

INSTRUCTIONS:
- Respond with a structured analysis.
- Start with VERDICT: <HIGH|MEDIUM|LOW> (LOW = paper is NOT a duplicate).
- Then write EXPLANATION: one or two paragraphs.
- Then write REFERENCES: comma-separated IDs of papers that are duplicated
  (or "none").
"""

_COMBINATION_PROMPT = """You are a rigorous academic novelty reviewer.

TASK: Determine whether the submitted paper is merely a simple combination
of existing works without a unifying contribution. Identify the individual
components, trace each to its origin, and assess whether their combination
constitutes a genuine insight.

SUBMITTED PAPER:
{paper_content}

REFERENCE PAPERS (most similar by text):
{reference_papers}

INSTRUCTIONS:
- Respond with a structured analysis.
- Start with VERDICT: <HIGH|MEDIUM|LOW> (LOW = not a simple combination).
- Then write EXPLANATION: one or two paragraphs describing which components
  come from which prior works, and whether the combination adds value.
- Then write REFERENCES: comma-separated IDs of source papers (or "none").
"""

_EQUIVALENCE_PROMPT = """You are a rigorous academic novelty reviewer.

TASK: Identify whether the methods proposed in the submitted paper are
subtly equivalent to well-established methodologies, even if the notation,
framing, or application domain differ. Look for mathematical equivalences,
algorithmic re-derivations, or conceptual renamings.

SUBMITTED PAPER:
{paper_content}

REFERENCE PAPERS (most similar by text):
{reference_papers}

INSTRUCTIONS:
- Respond with a structured analysis.
- Start with VERDICT: <HIGH|MEDIUM|LOW> (LOW = no equivalence found).
- Then write EXPLANATION: describe any equivalences found, citing the
  established method.
- Then write REFERENCES: comma-separated IDs of equivalent papers (or "none").
"""

_SYNTHESIS_PROMPT = """You are a senior programme-committee member.

Given the individual novelty analyses below for the paper titled
"{paper_title}", produce a final holistic verdict.

DUPLICATION ANALYSIS:
{duplication_result}

COMBINATION ANALYSIS:
{combination_result}

EQUIVALENCE ANALYSIS:
{equivalence_result}

INSTRUCTIONS:
Respond with:
OVERALL_VERDICT: <NOVEL|MARGINAL|NOT_NOVEL>
CONFIDENCE: <HIGH|MEDIUM|LOW>
SUMMARY: two to four sentences explaining the overall conclusion and the
main reasons behind it.
"""


# ---------------------------------------------------------------------------
# Response parsers
# ---------------------------------------------------------------------------

import re as _re


def _parse_dimension_response(
    text: str,
) -> tuple[str, str, list[str]]:
    """Extract (verdict, explanation, reference_ids) from a dimension response."""
    verdict = _extract_field(text, "VERDICT", default="UNCLEAR")
    explanation = _extract_field(text, "EXPLANATION", default=text.strip())
    refs_raw = _extract_field(text, "REFERENCES", default="none")
    refs = [
        r.strip()
        for r in _re.split(r"[,;]+", refs_raw)
        if r.strip().lower() not in {"none", ""}
    ]
    return verdict.strip(), explanation.strip(), refs


def _parse_synthesis_response(text: str) -> tuple[str, str, str]:
    """Extract (overall_verdict, confidence, summary) from a synthesis response."""
    verdict = _extract_field(text, "OVERALL_VERDICT", default="UNCLEAR")
    confidence = _extract_field(text, "CONFIDENCE", default="LOW")
    summary = _extract_field(text, "SUMMARY", default=text.strip())
    return verdict.strip(), confidence.strip(), summary.strip()


def _extract_field(text: str, field_name: str, default: str = "") -> str:
    """Return the value after ``FIELD_NAME:`` up to the next capitalised key."""
    pattern = _re.compile(
        rf"(?:^|\n){field_name}:\s*(.*?)(?=\n[A-Z_]{{2,}}:|\Z)",
        _re.DOTALL | _re.IGNORECASE,
    )
    m = pattern.search(text)
    if m:
        return m.group(1).strip()
    return default
