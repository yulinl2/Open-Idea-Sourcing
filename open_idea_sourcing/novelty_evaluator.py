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

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from .paper_parser import ParsedPaper
from .similarity_search import SimilarityResult


# Type alias for the LLM callable
LLMCallable = Callable[[str], str]


@dataclass
class PipelineJob:
    """Record of a single pipeline step execution.

    Attributes
    ----------
    name:
        Human-readable step name, e.g. ``"Duplication check"``.
    agent:
        Component that performed the step, e.g. ``"LLM (gpt-4o)"``.
    offset_s:
        Seconds elapsed since the start of the run when this job began.
    duration_s:
        Wall-clock duration of the job in seconds.
    input_summary:
        Brief description of the input, e.g. ``"paper content + 3 refs"``.
    output_summary:
        Brief description of the output, e.g. ``"verdict=HIGH"``.
    """

    name: str
    agent: str
    offset_s: float
    duration_s: float
    input_summary: str
    output_summary: str


@dataclass
class RunMetadata:
    """Metadata about an evaluation run for reproducibility and debugging.

    Attributes
    ----------
    model:
        Name of the LLM used (e.g. ``"gpt-4o"``).
    input_source:
        Original filename or URL of the paper that was evaluated.
    timestamp:
        ISO 8601 UTC timestamp recorded at the start of the run.
    total_runtime_seconds:
        Wall-clock time (seconds) from start to end of the full run.
    stage_runtimes:
        Per-stage wall-clock times keyed by stage name, e.g.
        ``{"parsing": 0.3, "similarity": 0.1, "evaluation": 12.4}``.
    code_version:
        Package version string for reproducibility tracing.
    git_branch:
        Name of the Git branch the run was triggered from.
    git_commit:
        Short commit SHA (7 chars) for the code that produced the report.
    git_commit_url:
        Full URL to the commit on GitHub (e.g. ``https://github.com/org/repo/commit/<sha>``).
    ci_run_url:
        URL to the CI workflow run that produced the report (empty when run locally).
    pr_number:
        GitHub pull-request number associated with this run (e.g. ``"42"``).
        Empty when run locally or from a push that has no open PR.
    jobs:
        Ordered list of :class:`PipelineJob` entries recorded during
        evaluation, suitable for rendering a Gantt-style job log.
    """

    model: str = ""
    input_source: str = ""
    timestamp: str = ""
    total_runtime_seconds: float = 0.0
    stage_runtimes: dict[str, float] = field(default_factory=dict)
    code_version: str = ""
    git_branch: str = ""
    git_commit: str = ""
    git_commit_url: str = ""
    ci_run_url: str = ""
    pr_number: str = ""
    jobs: list[PipelineJob] = field(default_factory=list)


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
    overall_verdict: str          # "NOVEL", "MARGINAL", "NOT_NOVEL", or "UNCLEAR"
    confidence: str               # "HIGH", "MEDIUM", "LOW"
    summary: str
    dimensions: list[NoveltyDimension] = field(default_factory=list)
    similar_papers: list[SimilarityResult] = field(default_factory=list)
    raw_llm_responses: dict[str, str] = field(default_factory=dict)
    metadata: RunMetadata | None = None


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
        metadata: Optional[RunMetadata] = None,
        _run_start: Optional[float] = None,
    ) -> NoveltyReport:
        """Run all evaluation passes and return a :class:`NoveltyReport`.

        Parameters
        ----------
        paper:
            The parsed paper to evaluate.
        similar_papers:
            Pre-computed similarity results.  If *None*, LLM analysis
            proceeds without reference anchoring.
        metadata:
            Optional :class:`RunMetadata` to update with per-job timing
            entries.  When supplied, a :class:`PipelineJob` entry is
            appended to ``metadata.jobs`` for each LLM call.
        _run_start:
            ``time.monotonic()`` value from the very start of the run,
            used to compute per-job offset timestamps.  If *None*, the
            start of this call is used as the reference point.
        """
        similar_papers = similar_papers or []
        # Apply threshold and top-k filtering
        similar_papers = [
            p for p in similar_papers if p.score >= self._threshold
        ][: self._top_k]
        content = paper.key_content()
        refs_text = self._format_references(similar_papers)
        raw: dict[str, str] = {}
        refs_summary = f"{len(similar_papers)} reference paper(s)"
        agent = f"LLM ({metadata.model})" if (metadata and metadata.model) else "LLM"
        run_start = _run_start if _run_start is not None else time.monotonic()

        t0 = time.monotonic()
        dup = self._check_duplication(content, refs_text, raw)
        t1 = time.monotonic()
        combo = self._check_combination(content, refs_text, raw)
        t2 = time.monotonic()
        equiv = self._check_equivalence(content, refs_text, raw)
        t3 = time.monotonic()
        overall, confidence, summary = self._synthesise(
            paper.title, dup, combo, equiv, raw
        )
        t4 = time.monotonic()

        if metadata is not None:
            metadata.jobs.extend([
                PipelineJob(
                    name="Duplication check",
                    agent=agent,
                    offset_s=round(t0 - run_start, 3),
                    duration_s=round(t1 - t0, 3),
                    input_summary=f"paper content + {refs_summary}",
                    output_summary=f"verdict={dup.verdict}",
                ),
                PipelineJob(
                    name="Combination check",
                    agent=agent,
                    offset_s=round(t1 - run_start, 3),
                    duration_s=round(t2 - t1, 3),
                    input_summary=f"paper content + {refs_summary}",
                    output_summary=f"verdict={combo.verdict}",
                ),
                PipelineJob(
                    name="Equivalence check",
                    agent=agent,
                    offset_s=round(t2 - run_start, 3),
                    duration_s=round(t3 - t2, 3),
                    input_summary=f"paper content + {refs_summary}",
                    output_summary=f"verdict={equiv.verdict}",
                ),
                PipelineJob(
                    name="Synthesis",
                    agent=agent,
                    offset_s=round(t3 - run_start, 3),
                    duration_s=round(t4 - t3, 3),
                    input_summary="3 dimension results",
                    output_summary=f"verdict={overall}, confidence={confidence}",
                ),
            ])

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
    """Return the value after ``FIELD_NAME:`` up to the next capitalised key.

    The field name is matched case-insensitively.  The lookahead that
    detects the *next* field is intentionally case-sensitive so that
    ordinary words followed by a colon inside a field value (e.g.
    ``Note: …`` or ``Method: …``) do not prematurely terminate the
    current field.

    When the field is present but has an empty value the *default* is
    returned, which mirrors the "field not found" behaviour and lets
    callers supply a meaningful fallback in both cases.
    """
    escaped_field_name = _re.escape(field_name)
    pattern = _re.compile(
        rf"(?:^|\n)(?i:{escaped_field_name}):[^\S\n]*(.*?)(?=\n[A-Z_]{{2,}}:|\Z)",
        _re.DOTALL,
    )
    m = pattern.search(text)
    if m:
        value = m.group(1).strip()
        return value if value else default
    return default
