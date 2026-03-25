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
    detail:
        Optional extended Markdown content rendered below the job table as a
        collapsible ``<details>`` block.  Empty string means no detail section.
    """

    name: str
    agent: str
    offset_s: float
    duration_s: float
    input_summary: str
    output_summary: str
    detail: str = ""


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
class IdeaDecomposition:
    """Structured decomposition of the paper's core idea.

    Attributes
    ----------
    core_concept:
        One-sentence description of the central contribution.
    sub_ideas:
        Key component ideas or sub-contributions.
    assumptions:
        Underlying assumptions the work makes.
    limitations:
        Acknowledged or implicit limitations of the approach.
    """

    core_concept: str
    sub_ideas: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class DomainReference:
    """A key reference paper in the domain identified by LLM analysis.

    Attributes
    ----------
    title:
        Title of the reference paper.
    authors:
        Author(s) of the reference paper.
    year:
        Publication year (as a string; may be approximate or empty).
    relevance:
        Brief explanation of why this reference is important.
    """

    title: str
    authors: str = ""
    year: str = ""
    relevance: str = ""


@dataclass
class SimilarityAnnotation:
    """LLM-generated comparative annotation for one similar reference paper.

    Attributes
    ----------
    paper_id:
        ID of the similar reference paper being annotated.
    overlap:
        Aspects shared between the submitted paper and this reference
        (methods, concepts, results).
    differences:
        Ways the submitted paper differs from or goes beyond this reference.
    derivation:
        Specific elements of the submitted paper that appear derived from
        or inspired by this reference.
    """

    paper_id: str
    overlap: str = ""
    differences: str = ""
    derivation: str = ""


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
    idea_decomposition: IdeaDecomposition | None = None
    domain_references: list[DomainReference] = field(default_factory=list)
    similar_paper_annotations: list[SimilarityAnnotation] = field(default_factory=list)


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

    def find_domain_references(
        self,
        content: str,
        refs_text: str,
        raw: dict[str, str],
    ) -> list[DomainReference]:
        """Identify key domain references for a paper (Stage 3d — Retrieve).

        This is a retrieval task — it contextualises the paper in its field
        using LLM analysis of the paper content and top-matched references.
        It belongs at Stage 3 (Retrieve), not Stage 5 (Evaluate), because it
        enriches the context used by the evaluation passes rather than
        producing a novelty verdict itself.

        Parameters
        ----------
        content:
            Key content of the paper (e.g. ``paper.key_content()``).
        refs_text:
            Formatted string of top-matched reference papers (e.g. from
            :meth:`format_references`).
        raw:
            Mutable dict into which the raw LLM response is stored under
            the key ``"domain_references"`` for report transparency.

        Returns
        -------
        list[DomainReference]
            LLM-identified key references contextualising the paper in its
            field.
        """
        return self._find_domain_references(content, refs_text, raw)

    def evaluate(
        self,
        paper: ParsedPaper,
        similar_papers: Optional[list[SimilarityResult]] = None,
        metadata: Optional[RunMetadata] = None,
        _run_start: Optional[float] = None,
        domain_references: Optional[list[DomainReference]] = None,
        _domain_references_raw: Optional[dict[str, str]] = None,
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
        domain_references:
            Pre-computed domain references (Stage 3d result).  When
            supplied the internal ``_find_domain_references`` LLM call is
            skipped and its :class:`PipelineJob` entry is omitted from
            ``metadata.jobs`` (the caller is responsible for recording
            that job).  Pass *None* to run the call internally (default,
            backward-compatible behaviour).
        _domain_references_raw:
            Raw LLM response dict from an external
            :meth:`find_domain_references` call.  Merged into
            ``report.raw_llm_responses`` so the JSON output stays
            complete even when domain references were pre-computed.
        """
        similar_papers = similar_papers or []
        # Apply threshold and top-k filtering
        similar_papers = [
            p for p in similar_papers if p.score >= self._threshold
        ][: self._top_k]
        content = paper.key_content()
        refs_text = self.format_references(similar_papers)
        raw: dict[str, str] = {}
        refs_summary = f"{len(similar_papers)} reference paper(s)"
        agent = f"LLM ({metadata.model})" if (metadata and metadata.model) else "LLM"
        run_start = _run_start if _run_start is not None else time.monotonic()

        # Idea decomposition runs FIRST — it provides the structural context
        # that informs all subsequent novelty analysis passes.
        t0 = time.monotonic()
        idea_decomp = self._decompose_idea(content, raw)
        t1 = time.monotonic()
        dup = self._check_duplication(content, refs_text, raw)
        t2 = time.monotonic()
        combo = self._check_combination(content, refs_text, raw)
        t3 = time.monotonic()
        equiv = self._check_equivalence(content, refs_text, raw)
        t4 = time.monotonic()
        overall, confidence, summary = self._synthesise(
            paper.title, dup, combo, equiv, raw
        )
        t5 = time.monotonic()

        # Domain references: when pre-computed at Stage 3d (by the caller),
        # skip the internal LLM call entirely and merge the caller's raw
        # response dict so report.raw_llm_responses remains complete.
        if domain_references is not None:
            domain_refs = domain_references
            if _domain_references_raw:
                raw.update(_domain_references_raw)
            t6 = t5  # domain refs time is accounted for at Stage 3d
        else:
            # Backward-compatible internal call (Stage 5d position).
            domain_refs = self._find_domain_references(content, refs_text, raw)
            t6 = time.monotonic()

        # Annotate each similar paper with overlap/differences/derivation.
        # Only runs when similar papers exist (avoids an unnecessary LLM call).
        annotations: list[SimilarityAnnotation] = []
        t7 = t6
        if similar_papers:
            annotations = self._annotate_similar_papers(content, similar_papers, raw)
            t7 = time.monotonic()

        if metadata is not None:
            jobs: list[PipelineJob] = [
                PipelineJob(
                    name="Idea decomposition",
                    agent=agent,
                    offset_s=round(t0 - run_start, 3),
                    duration_s=round(t1 - t0, 3),
                    input_summary="paper content",
                    output_summary=f"{len(idea_decomp.sub_ideas)} sub-idea(s)",
                ),
                PipelineJob(
                    name="Duplication check",
                    agent=agent,
                    offset_s=round(t1 - run_start, 3),
                    duration_s=round(t2 - t1, 3),
                    input_summary=f"paper content + {refs_summary}",
                    output_summary=f"verdict={dup.verdict}",
                ),
                PipelineJob(
                    name="Combination check",
                    agent=agent,
                    offset_s=round(t2 - run_start, 3),
                    duration_s=round(t3 - t2, 3),
                    input_summary=f"paper content + {refs_summary}",
                    output_summary=f"verdict={combo.verdict}",
                ),
                PipelineJob(
                    name="Equivalence check",
                    agent=agent,
                    offset_s=round(t3 - run_start, 3),
                    duration_s=round(t4 - t3, 3),
                    input_summary=f"paper content + {refs_summary}",
                    output_summary=f"verdict={equiv.verdict}",
                ),
                PipelineJob(
                    name="Synthesis",
                    agent=agent,
                    offset_s=round(t4 - run_start, 3),
                    duration_s=round(t5 - t4, 3),
                    input_summary="3 dimension results",
                    output_summary=f"verdict={overall}, confidence={confidence}",
                ),
            ]
            # Domain references PipelineJob is only added here when the call
            # was made internally (i.e. domain_references was not pre-computed
            # at Stage 3d).  When pre-computed, the caller adds the job entry
            # to the early_jobs list instead.
            if domain_references is None:
                jobs.append(PipelineJob(
                    name="Domain references",
                    agent=agent,
                    offset_s=round(t5 - run_start, 3),
                    duration_s=round(t6 - t5, 3),
                    input_summary=f"paper content + {refs_summary}",
                    output_summary=f"{len(domain_refs)} domain reference(s)",
                ))
            if similar_papers:
                jobs.append(PipelineJob(
                    name="Reference annotation",
                    agent=agent,
                    offset_s=round(t6 - run_start, 3),
                    duration_s=round(t7 - t6, 3),
                    input_summary=f"paper + {len(similar_papers)} similar paper(s)",
                    output_summary=f"{len(annotations)} annotation(s)",
                ))
            metadata.jobs.extend(jobs)

        return NoveltyReport(
            paper_title=paper.title,
            overall_verdict=overall,
            confidence=confidence,
            summary=summary,
            dimensions=[dup, combo, equiv],
            similar_papers=similar_papers,
            raw_llm_responses=raw,
            idea_decomposition=idea_decomp,
            domain_references=domain_refs,
            similar_paper_annotations=annotations,
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

    def _decompose_idea(
        self, content: str, raw: dict[str, str]
    ) -> IdeaDecomposition:
        """Ask the LLM to decompose the paper's core idea into components."""
        prompt = _IDEA_DECOMPOSITION_PROMPT.format(paper_content=content)
        response = self._llm(prompt)
        raw["idea_decomposition"] = response
        return _parse_decomposition_response(response)

    def _find_domain_references(
        self, content: str, refs_text: str, raw: dict[str, str]
    ) -> list[DomainReference]:
        """Ask the LLM to identify key domain references for this paper."""
        prompt = _DOMAIN_REFERENCES_PROMPT.format(
            paper_content=content, reference_papers=refs_text
        )
        response = self._llm(prompt)
        raw["domain_references"] = response
        return _parse_domain_references_response(response)

    def _annotate_similar_papers(
        self, content: str, similar: list[SimilarityResult], raw: dict[str, str]
    ) -> list[SimilarityAnnotation]:
        """Ask the LLM to annotate each similar paper with comparative analysis.

        Generates per-paper overlap, differences, and derivation annotations
        comparing the submitted paper against each pre-matched reference.
        """
        prompt = _SIMILAR_PAPERS_ANNOTATION_PROMPT.format(
            paper_content=content,
            reference_papers=self.format_references(similar),
        )
        response = self._llm(prompt)
        raw["similar_paper_annotations"] = response
        return _parse_similar_paper_annotations_response(response)

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
    def format_references(similar: list[SimilarityResult]) -> str:
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

_IDEA_DECOMPOSITION_PROMPT = """You are an expert research analyst.

TASK: Decompose the following paper's core idea into its fundamental components.

SUBMITTED PAPER:
{paper_content}

INSTRUCTIONS:
Respond with the following structured fields.

CORE_CONCEPT: One sentence describing the central contribution or idea.

SUB_IDEAS:
1. <first key component or sub-contribution>
2. <second key component or sub-contribution>
3. <additional components as needed>

ASSUMPTIONS:
1. <first underlying assumption the work makes>
2. <additional assumptions as needed>

LIMITATIONS:
1. <first acknowledged or implicit limitation>
2. <additional limitations as needed>
"""

_DOMAIN_REFERENCES_PROMPT = """You are an expert research librarian.

TASK: Identify the most important foundational and closely related works
in the domain of the following paper. Focus on seminal papers that a
reader would need to understand the context of this contribution.

SUBMITTED PAPER:
{paper_content}

ALREADY IDENTIFIED SIMILAR PAPERS (from text similarity search):
{reference_papers}

INSTRUCTIONS:
List 3 to 6 key domain references in the format below.
Each entry must appear on its own line starting with a number.

REFERENCES:
1. TITLE: <paper title> | AUTHORS: <author(s)> | YEAR: <year> | RELEVANCE: <why this reference matters>
2. TITLE: <paper title> | AUTHORS: <author(s)> | YEAR: <year> | RELEVANCE: <why this reference matters>
"""

_SIMILAR_PAPERS_ANNOTATION_PROMPT = """You are an expert research analyst.

TASK: For each similar reference paper listed below, write a concise comparative
annotation against the submitted paper. Describe shared aspects, key differences,
and any elements in the submitted paper that appear derived from or inspired by
that reference. Every claim should be grounded in the paper content provided.

SUBMITTED PAPER:
{paper_content}

SIMILAR REFERENCE PAPERS (ranked by TF-IDF cosine similarity score):
{reference_papers}

INSTRUCTIONS:
Respond with one block per reference paper, in the order listed.
Use the paper ID exactly as shown in brackets.

PAPER [<id>]:
OVERLAP: <1–2 sentences on shared methods, concepts, or results between the submitted paper and this reference>
DIFFERENCES: <1–2 sentences on what distinguishes the submitted paper from this reference>
DERIVATION: <1 sentence on what in the submitted paper appears derived from or inspired by this reference, or "None identified">
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

    The regex also accepts Markdown-bold-wrapped field names (e.g.
    ``**FIELD_NAME:**``) because LLMs sometimes format their structured
    output with bold markers around the label.
    """
    escaped_field_name = _re.escape(field_name)
    pattern = _re.compile(
        rf"(?:^|\n)(?:\*\*)?(?i:{escaped_field_name})(?:\*\*)?:(?:\*\*)?[^\S\n]*(.*?)"
        rf"(?=\n(?:\*\*)?[A-Z_]{{2,}}(?:\*\*)?:|\Z)",
        _re.DOTALL,
    )
    m = pattern.search(text)
    if m:
        value = m.group(1).strip()
        return value if value else default
    return default


def _parse_numbered_list(text: str) -> list[str]:
    """Extract items from a numbered list (``1. item``, ``2. item``, …)."""
    items = []
    for line in text.splitlines():
        line = line.strip()
        m = _re.match(r"^\d+[.)]\s+(.+)", line)
        if m:
            items.append(m.group(1).strip())
    return items


def _parse_decomposition_response(text: str) -> "IdeaDecomposition":
    """Extract an :class:`IdeaDecomposition` from an LLM response.

    Falls back gracefully: if ``CORE_CONCEPT`` is missing the full
    response text is used; if a list section is missing it defaults to
    an empty list.
    """
    core_concept = _extract_field(text, "CORE_CONCEPT", default=text.strip())
    sub_ideas_raw = _extract_field(text, "SUB_IDEAS", default="")
    assumptions_raw = _extract_field(text, "ASSUMPTIONS", default="")
    limitations_raw = _extract_field(text, "LIMITATIONS", default="")
    return IdeaDecomposition(
        core_concept=core_concept,
        sub_ideas=_parse_numbered_list(sub_ideas_raw),
        assumptions=_parse_numbered_list(assumptions_raw),
        limitations=_parse_numbered_list(limitations_raw),
    )


def _parse_domain_references_response(text: str) -> "list[DomainReference]":
    """Extract a list of :class:`DomainReference` objects from an LLM response.

    Each entry is expected on its own numbered line in the format::

        1. TITLE: <title> | AUTHORS: <authors> | YEAR: <year> | RELEVANCE: <relevance>

    Fields are parsed case-insensitively and any missing field is left as
    an empty string.  Lines that cannot be parsed are silently skipped.
    """
    refs_block = _extract_field(text, "REFERENCES", default=text.strip())
    results: list[DomainReference] = []
    for line in refs_block.splitlines():
        line = line.strip()
        # Strip optional leading number and dot/paren, e.g. "1. " or "1) "
        line = _re.sub(r"^\d+[.)]\s*", "", line).strip()
        if not line:
            continue
        # Split on " | " separators (case-insensitive field labels)
        parts = _re.split(r"\s*\|\s*", line)
        fields: dict[str, str] = {}
        for part in parts:
            m = _re.match(r"^([A-Za-z]+):\s*(.*)", part.strip(), _re.DOTALL)
            if m:
                fields[m.group(1).upper()] = m.group(2).strip()
        title = fields.get("TITLE", "")
        if not title:
            continue
        results.append(
            DomainReference(
                title=title,
                authors=fields.get("AUTHORS", ""),
                year=fields.get("YEAR", ""),
                relevance=fields.get("RELEVANCE", ""),
            )
        )
    return results


def _parse_similar_paper_annotations_response(
    text: str,
) -> "list[SimilarityAnnotation]":
    """Extract per-paper comparative annotations from an LLM response.

    Expected format (one block per paper)::

        PAPER [<id>]:
        OVERLAP: <shared aspects>
        DIFFERENCES: <distinguishing aspects>
        DERIVATION: <derived elements>

    Blocks that cannot be parsed are silently skipped; the result list
    may therefore be shorter than the number of similar papers.
    """
    results: list[SimilarityAnnotation] = []
    # Split on "PAPER [id]:" markers (case-insensitive, allowing whitespace)
    blocks = _re.split(r"(?mi)^PAPER\s*\[([^\]]+)\]\s*:", text)
    # blocks[0] is preamble; blocks[1::2] are IDs; blocks[2::2] are content
    ids = blocks[1::2]
    contents = blocks[2::2]
    for paper_id, content_block in zip(ids, contents):
        paper_id = paper_id.strip()
        if not paper_id:
            continue
        overlap = _extract_field(content_block, "OVERLAP", default="")
        differences = _extract_field(content_block, "DIFFERENCES", default="")
        derivation = _extract_field(content_block, "DERIVATION", default="")
        results.append(SimilarityAnnotation(
            paper_id=paper_id,
            overlap=overlap,
            differences=differences,
            derivation=derivation,
        ))
    return results
