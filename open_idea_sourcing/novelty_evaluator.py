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

import pathlib as _pathlib
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from .paper_parser import ParsedPaper
from .similarity_search import SimilarityResult


# Type alias for the LLM callable
LLMCallable = Callable[[str], str]

_PROMPTS_DIR = _pathlib.Path(__file__).resolve().parent / "prompts"


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    return (_PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


@dataclass
class PipelineJob:
    """Record of a single pipeline step execution.

    Attributes
    ----------
    name:
        Human-readable step name, e.g. ``"Duplication check"``.
    agent:
        Component that performed the step, e.g. ``"LLM (gpt-5.4)"``.
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
        Name of the LLM used (e.g. ``"gpt-5.4"``).
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
    decomposition_model: str = ""  # separate model used for Stage 2 (when set)
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
class ConceptNode:
    """A node in the hierarchical concept tree."""
    label: str
    children: list[ConceptNode] = field(default_factory=list)


@dataclass
class IdeaDecomposition:
    """Structured decomposition of the paper's core idea.

    Attributes
    ----------
    core_concept:
        One-sentence description of the central contribution.
    concept_tree:
        Hierarchical breakdown of the contribution.  Fully adaptive —
        the LLM determines depth, breadth, and granularity based on
        the paper's content and scientific significance.
    """

    core_concept: str
    concept_tree: ConceptNode | None = None


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
    """LLM-generated derivation analysis comparing the submitted paper against
    the full pool of similar reference papers.

    Attributes
    ----------
    derivation_map:
        Mapping from concept-tree component label to source REF-N labels.
        E.g. ``{"attention mechanism": ["REF-1", "REF-3"], "training recipe": ["REF-2"]}``.
    combination_analysis:
        Prose analysis of whether the paper combines subsets of references.
    novel_elements:
        Elements that appear not derivable from any listed reference.
    paper_id:
        Kept for backward compatibility (set to empty string for 1-to-all mode).
    """

    derivation_map: dict[str, list[str]] = field(default_factory=dict)
    combination_analysis: str = ""
    novel_elements: list[str] = field(default_factory=list)
    paper_id: str = ""


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
    # Maps paper_id → primary source label ("user", "paper-cited", "online", "domain")
    ref_sources: dict[str, str] = field(default_factory=dict)


@dataclass
class PipelineContext:
    """Shared state bus threaded through all pipeline stages.

    Each stage reads from and writes to this object.  Using
    ``PipelineContext`` as the shared bus (rather than function
    parameters) makes it possible to:

    * Inspect or checkpoint pipeline state at any point mid-run.
    * Replay any stage independently without re-running earlier stages.
    * Swap any stage implementation (e.g. swap the parser, the retriever,
      or a single dimension check) without touching adjacent stages.
    * Run reliable ablations — separate the effects of model choice, prompt
      design, and pipeline structure cleanly.
    """

    paper: ParsedPaper
    metadata: RunMetadata
    raw_llm_responses: dict[str, str] = field(default_factory=dict)
    idea_decomposition: IdeaDecomposition | None = None
    similar_papers: list[SimilarityResult] = field(default_factory=list)
    domain_references: list[DomainReference] = field(default_factory=list)
    similar_paper_annotations: list[SimilarityAnnotation] = field(default_factory=list)
    dimensions: list[NoveltyDimension] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)
    online_papers: list = field(default_factory=list)
    stage_runtimes: dict[str, float] = field(default_factory=dict)
    # Maps paper_id → source label ("user", "paper-cited", "online", "domain")
    ref_sources: dict[str, str] = field(default_factory=dict)


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
                    model="gpt-5.4",
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
        top_k_similar: int = 10_000,
        similarity_threshold: float = 0.1,
        decomposition_llm: LLMCallable | None = None,
    ) -> None:
        self._llm = llm
        self._top_k = top_k_similar
        self._threshold = similarity_threshold
        self._decomposition_llm = decomposition_llm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_domain_references(
        self,
        content: str,
        refs_text: str,
        raw: dict[str, str],
        decomp: IdeaDecomposition | None = None,
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
        return self._find_domain_references(content, refs_text, raw, decomp=decomp)

    def decompose_idea(self, paper: ParsedPaper, raw: dict[str, str]) -> IdeaDecomposition:
        """Decompose *paper*'s core idea into structured components (Stage 2).

        Calling this before :meth:`evaluate` (Stage 3+) lets the concept tree
        inform query generation in the online retrieval step.

        Parameters
        ----------
        paper:
            The parsed paper to decompose.
        raw:
            Mutable dict into which the raw LLM response is stored under
            ``"idea_decomposition"``.

        Returns
        -------
        IdeaDecomposition
            Structured breakdown of the paper's core idea.
        """
        return self._decompose_idea(paper.key_content(), raw)

    def evaluate(
        self,
        paper: ParsedPaper,
        similar_papers: Optional[list[SimilarityResult]] = None,
        metadata: Optional[RunMetadata] = None,
        _run_start: Optional[float] = None,
        domain_references: Optional[list[DomainReference]] = None,
        _domain_references_raw: Optional[dict[str, str]] = None,
        idea_decomposition: Optional[IdeaDecomposition] = None,
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
        # Apply threshold filtering
        similar_papers = [
            p for p in similar_papers if p.score >= self._threshold
        ]
        content = paper.key_content()
        refs_text = self.format_references(similar_papers)
        raw: dict[str, str] = {}
        refs_summary = f"{len(similar_papers)} reference paper(s)"
        agent = f"LLM ({metadata.model})" if (metadata and metadata.model) else "LLM"
        run_start = _run_start if _run_start is not None else time.monotonic()

        # Idea decomposition runs FIRST — it provides the structural context
        # that informs all subsequent novelty analysis passes.
        t0 = time.monotonic()
        if idea_decomposition is not None:
            idea_decomp = idea_decomposition
            t1 = time.monotonic()
        else:
            idea_decomp = self._decompose_idea(content, raw)
            t1 = time.monotonic()
        dup = self._check_duplication(content, refs_text, raw, decomp=idea_decomp)
        t2 = time.monotonic()
        combo = self._check_combination(content, refs_text, raw, decomp=idea_decomp, prior_dup=dup)
        t3 = time.monotonic()
        equiv = self._check_equivalence(content, refs_text, raw, decomp=idea_decomp, prior_dup=dup, prior_combo=combo)
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
            annotations = self._annotate_similar_papers(content, similar_papers, raw, decomp=idea_decomp)
            t7 = time.monotonic()

        if metadata is not None:
            jobs: list[PipelineJob] = []
            if idea_decomposition is None:
                jobs.append(PipelineJob(
                    name="Idea decomposition",
                    agent=agent,
                    offset_s=round(t0 - run_start, 3),
                    duration_s=round(t1 - t0, 3),
                    input_summary="paper content",
                    output_summary="concept tree" if idea_decomp.concept_tree else "core concept only",
                ))
            jobs += [
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

    def evaluate_with_context(self, ctx: "PipelineContext") -> "NoveltyReport":
        """Run all evaluation passes using *ctx* as the shared state bus.

        Reads inputs from *ctx* and writes all results back to it, making
        this the ablation-friendly entry point for the evaluation stage.

        When ``ctx.idea_decomposition`` is already populated (e.g. pre-run
        at Stage 2), the internal decomposition LLM call is skipped.
        Likewise, when ``ctx.domain_references`` is already populated
        (pre-run at Stage 3d), the internal domain-references call is
        skipped and no duplicate ``PipelineJob`` entry is added.

        Reads
        -----
        ctx.paper, ctx.similar_papers, ctx.idea_decomposition,
        ctx.domain_references, ctx.metadata, ctx.raw_llm_responses

        Writes
        ------
        ctx.idea_decomposition, ctx.domain_references,
        ctx.similar_paper_annotations, ctx.dimensions, ctx.raw_llm_responses,
        ctx.metadata.jobs (appended)

        Parameters
        ----------
        ctx:
            Shared pipeline context.

        Returns
        -------
        NoveltyReport
            Fully assembled report with all dimension verdicts and metadata.
        """
        similar_papers = [
            p for p in ctx.similar_papers if p.score >= self._threshold
        ]
        content = ctx.paper.key_content()
        refs_text = self.format_references(similar_papers)
        raw = ctx.raw_llm_responses
        refs_summary = f"{len(similar_papers)} reference paper(s)"
        agent = (
            f"LLM ({ctx.metadata.model})"
            if (ctx.metadata and ctx.metadata.model)
            else "LLM"
        )
        run_start = time.monotonic()

        decomp_ran_internally = False
        t0 = time.monotonic()
        if ctx.idea_decomposition is not None:
            idea_decomp = ctx.idea_decomposition
            t1 = time.monotonic()
        else:
            idea_decomp = self._decompose_idea(content, raw)
            ctx.idea_decomposition = idea_decomp
            decomp_ran_internally = True
            t1 = time.monotonic()

        dup = self._check_duplication(content, refs_text, raw, decomp=idea_decomp)
        t2 = time.monotonic()
        combo = self._check_combination(content, refs_text, raw, decomp=idea_decomp, prior_dup=dup)
        t3 = time.monotonic()
        equiv = self._check_equivalence(content, refs_text, raw, decomp=idea_decomp, prior_dup=dup, prior_combo=combo)
        t4 = time.monotonic()
        overall, confidence, summary = self._synthesise(
            ctx.paper.title, dup, combo, equiv, raw
        )
        t5 = time.monotonic()

        domain_refs_ran_internally = False
        if ctx.domain_references:
            domain_refs = ctx.domain_references
            t6 = t5
        else:
            domain_refs = self._find_domain_references(content, refs_text, raw)
            ctx.domain_references = domain_refs
            domain_refs_ran_internally = True
            t6 = time.monotonic()

        annotations: list[SimilarityAnnotation] = []
        t7 = t6
        if similar_papers:
            annotations = self._annotate_similar_papers(
                content, similar_papers, raw, decomp=idea_decomp
            )
            ctx.similar_paper_annotations = annotations
            t7 = time.monotonic()

        ctx.dimensions = [dup, combo, equiv]

        if ctx.metadata is not None:
            jobs: list[PipelineJob] = []
            if decomp_ran_internally:
                jobs.append(PipelineJob(
                    name="Idea decomposition",
                    agent=agent,
                    offset_s=round(t0 - run_start, 3),
                    duration_s=round(t1 - t0, 3),
                    input_summary="paper content",
                    output_summary="concept tree" if idea_decomp.concept_tree else "core concept only",
                ))
            jobs += [
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
            if domain_refs_ran_internally:
                jobs.append(PipelineJob(
                    name="Domain references",
                    agent=agent,
                    offset_s=round(t5 - run_start, 3),
                    duration_s=round(t6 - t5, 3),
                    input_summary=f"paper content + {refs_summary}",
                    output_summary=f"{len(domain_refs)} domain reference(s)",
                ))
            if annotations:
                jobs.append(PipelineJob(
                    name="Reference annotation",
                    agent=agent,
                    offset_s=round(t6 - run_start, 3),
                    duration_s=round(t7 - t6, 3),
                    input_summary=f"paper + {len(similar_papers)} similar paper(s)",
                    output_summary=f"{len(annotations)} annotation(s)",
                ))
            ctx.metadata.jobs.extend(jobs)

        return NoveltyReport(
            paper_title=ctx.paper.title,
            overall_verdict=overall,
            confidence=confidence,
            summary=summary,
            dimensions=[dup, combo, equiv],
            similar_papers=similar_papers,
            raw_llm_responses=dict(raw),
            metadata=ctx.metadata,
            idea_decomposition=idea_decomp,
            domain_references=domain_refs,
            similar_paper_annotations=annotations,
            ref_sources=dict(ctx.ref_sources),
        )

    # ------------------------------------------------------------------
    # Analysis passes
    # ------------------------------------------------------------------

    def _check_duplication(
        self, content: str, refs_text: str, raw: dict[str, str],
        decomp: IdeaDecomposition | None = None,
    ) -> NoveltyDimension:
        """Detect whether the paper directly duplicates existing work."""
        prompt = _DUPLICATION_PROMPT.format(
            paper_content=content,
            reference_papers=refs_text,
            decomposition=_format_decomp_context(decomp),
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
        self, content: str, refs_text: str, raw: dict[str, str],
        decomp: IdeaDecomposition | None = None,
        prior_dup: "NoveltyDimension | None" = None,
    ) -> NoveltyDimension:
        """Detect whether the paper is merely a combination of prior works.

        Parameters
        ----------
        prior_dup:
            Result of the duplication check (Stage 5a).  When provided, the
            combination prompt receives it as ``PRIOR ANALYSIS`` context so
            this pass builds on — rather than duplicates — the prior verdict.
        """
        prior_text = (
            f"Verdict: {prior_dup.verdict}\n{prior_dup.explanation}"
            if prior_dup is not None
            else "Not yet performed."
        )
        prompt = _COMBINATION_PROMPT.format(
            paper_content=content,
            reference_papers=refs_text,
            decomposition=_format_decomp_context(decomp),
            prior_duplication=prior_text,
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
        self, content: str, refs_text: str, raw: dict[str, str],
        decomp: IdeaDecomposition | None = None,
        prior_dup: "NoveltyDimension | None" = None,
        prior_combo: "NoveltyDimension | None" = None,
    ) -> NoveltyDimension:
        """Detect methodological equivalence to known methods.

        Parameters
        ----------
        prior_dup:
            Result of the duplication check (Stage 5a).
        prior_combo:
            Result of the combination check (Stage 5b).
        When provided, both are passed as ``PRIOR ANALYSIS`` context so this
        pass builds on the accumulated evidence from earlier checks.
        """
        dup_text = (
            f"Verdict: {prior_dup.verdict}\n{prior_dup.explanation}"
            if prior_dup is not None
            else "Not yet performed."
        )
        combo_text = (
            f"Verdict: {prior_combo.verdict}\n{prior_combo.explanation}"
            if prior_combo is not None
            else "Not yet performed."
        )
        prompt = _EQUIVALENCE_PROMPT.format(
            paper_content=content,
            reference_papers=refs_text,
            decomposition=_format_decomp_context(decomp),
            prior_duplication=dup_text,
            prior_combination=combo_text,
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
        llm = self._decomposition_llm if self._decomposition_llm is not None else self._llm
        prompt = _IDEA_DECOMPOSITION_PROMPT.format(paper_content=content)
        response = llm(prompt)
        raw["idea_decomposition"] = response
        return _parse_decomposition_response(response)

    def _find_domain_references(
        self, content: str, refs_text: str, raw: dict[str, str],
        decomp: IdeaDecomposition | None = None,
    ) -> list[DomainReference]:
        """Ask the LLM to identify key domain references for this paper."""
        prompt = _DOMAIN_REFERENCES_PROMPT.format(
            paper_content=content,
            reference_papers=refs_text,
            decomposition=_format_decomp_context(decomp),
        )
        response = self._llm(prompt)
        raw["domain_references"] = response
        return _parse_domain_references_response(response)

    def _annotate_similar_papers(
        self, content: str, similar: list[SimilarityResult], raw: dict[str, str],
        decomp: IdeaDecomposition | None = None,
    ) -> list[SimilarityAnnotation]:
        """Ask the LLM to annotate each similar paper with comparative analysis.

        Generates per-paper overlap, differences, and derivation annotations
        comparing the submitted paper against each pre-matched reference.
        """
        prompt = _SIMILAR_PAPERS_ANNOTATION_PROMPT.format(
            paper_content=content,
            reference_papers=self.format_references(similar),
            decomposition=_format_decomp_context(decomp),
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
                f"REF-{i} [{p.id}]: {p.title} "
                f"({p.year or 'year unknown'}) — similarity {r.score:.2f}\n"
                f"   Abstract: {p.abstract[:300]}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prompt templates (loaded from prompts/ directory)
# ---------------------------------------------------------------------------

_DUPLICATION_PROMPT = _load_prompt("duplication")
_COMBINATION_PROMPT = _load_prompt("combination")
_EQUIVALENCE_PROMPT = _load_prompt("equivalence")
_SYNTHESIS_PROMPT = _load_prompt("synthesis")
_IDEA_DECOMPOSITION_PROMPT = _load_prompt("decomposition")
_DOMAIN_REFERENCES_PROMPT = _load_prompt("domain_references")
_SIMILAR_PAPERS_ANNOTATION_PROMPT = _load_prompt("annotation")


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
    """Extract an :class:`IdeaDecomposition` from an LLM response."""
    core_concept = _extract_field(text, "CORE_CONCEPT", default=text.strip())
    concept_tree_raw = _extract_field(text, "CONCEPT_TREE", default="")
    concept_tree = _parse_concept_tree_text(concept_tree_raw) if concept_tree_raw.strip() else None
    return IdeaDecomposition(
        core_concept=core_concept,
        concept_tree=concept_tree,
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
    """Extract a single 1-to-all derivation annotation from an LLM response."""
    derivation_map_raw = _extract_field(text, "DERIVATION_MAP", default="")
    combination_analysis = _extract_field(text, "COMBINATION_ANALYSIS", default="")
    novel_elements_raw = _extract_field(text, "NOVEL_ELEMENTS", default="")

    # Parse derivation map: "- component: REF-1, REF-3"
    derivation_map: dict[str, list[str]] = {}
    for line in derivation_map_raw.splitlines():
        line = line.strip().lstrip("-").strip()
        if ":" in line:
            component, refs_str = line.split(":", 1)
            component = component.strip()
            if component:
                refs = [r.strip() for r in refs_str.split(",") if r.strip()]
                derivation_map[component] = refs

    # Parse novel elements list
    novel_elements = [
        line.strip().lstrip("-•*").strip()
        for line in novel_elements_raw.splitlines()
        if line.strip().lstrip("-•*").strip()
    ]

    return [SimilarityAnnotation(
        derivation_map=derivation_map,
        combination_analysis=combination_analysis,
        novel_elements=novel_elements,
    )]


def _parse_concept_tree_text(text: str) -> "ConceptNode | None":
    """Parse an indented text outline into a :class:`ConceptNode` tree.

    Auto-detects the indent unit from the first indented line.
    Returns ``None`` when *text* is empty or contains no indented lines.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None

    # Detect indent unit: first line that has leading whitespace.
    indent_unit = ""
    for ln in lines:
        stripped = ln.lstrip()
        if len(ln) > len(stripped):
            indent_unit = ln[: len(ln) - len(stripped)]
            break

    if not indent_unit:
        # No indented lines — either a single-level flat list or one item.
        return None if len(lines) > 1 else ConceptNode(label=lines[0].strip())

    # Build the tree: virtual_root collects all depth-0 items.
    virtual_root = ConceptNode(label="")
    # ancestors[d] = most-recently-seen node at depth d; index 0 = virtual_root.
    ancestors: list[ConceptNode] = [virtual_root]
    for ln in lines:
        stripped = ln.lstrip()
        leading = ln[: len(ln) - len(stripped)]
        depth = len(leading) // len(indent_unit)
        node = ConceptNode(label=stripped)
        # Trim ancestors to the parent level.
        del ancestors[depth + 1 :]
        parent = ancestors[depth] if depth < len(ancestors) else ancestors[-1]
        parent.children.append(node)
        ancestors.append(node)   # ancestors[depth + 1] = node

    if not virtual_root.children:
        return None
    if len(virtual_root.children) == 1:
        return virtual_root.children[0]
    return virtual_root  # virtual root with multiple depth-0 children


def _concept_tree_to_text(node: "ConceptNode", indent: int = 0) -> str:
    """Render a :class:`ConceptNode` tree as an indented text string.

    Uses 2-space indentation per level.  Suitable for embedding in LLM
    prompts where box-drawing characters may confuse the tokeniser.
    """
    prefix = "  " * indent
    lines = [f"{prefix}{node.label}"]
    for child in node.children:
        lines.append(_concept_tree_to_text(child, indent + 1))
    return "\n".join(lines)


def _format_decomp_context(decomp: "IdeaDecomposition | None") -> str:
    """Return a concise text representation of *decomp* for LLM prompt injection."""
    if decomp is None:
        return "(no decomposition available)"

    parts: list[str] = [f"Core concept: {decomp.core_concept}"]

    if decomp.concept_tree is not None:
        tree_str = _concept_tree_to_text(decomp.concept_tree)
        if tree_str:
            parts.append("Concept tree:\n" + tree_str)

    return "\n\n".join(parts)
