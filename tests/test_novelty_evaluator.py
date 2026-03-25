"""Tests for open_idea_sourcing.novelty_evaluator."""

import pytest

from open_idea_sourcing.novelty_evaluator import (
    ConceptNode,
    DomainReference,
    IdeaDecomposition,
    NoveltyDimension,
    NoveltyEvaluator,
    NoveltyReport,
    SimilarityAnnotation,
    _extract_field,
    _parse_concept_tree_text,
    _parse_decomposition_response,
    _parse_dimension_response,
    _parse_domain_references_response,
    _parse_numbered_list,
    _parse_similar_paper_annotations_response,
    _parse_synthesis_response,
)
from open_idea_sourcing.paper_parser import ParsedPaper
from open_idea_sourcing.reference_store import ReferencePaper, ReferenceStore
from open_idea_sourcing.similarity_search import SimilarityResult


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

SAMPLE_PAPER = ParsedPaper(
    title="A Novel Attention Mechanism",
    abstract="We propose an improved attention mechanism for transformers.",
    full_text=(
        "A Novel Attention Mechanism\n\n"
        "Abstract\n"
        "We propose an improved attention mechanism for transformers.\n\n"
        "Introduction\n"
        "Attention is fundamental in modern NLP. We extend the work of "
        "Vaswani et al. by adding dynamic masking."
    ),
)

SAMPLE_REFERENCE = ReferencePaper(
    id="att2017",
    title="Attention Is All You Need",
    abstract="We propose the Transformer based on attention mechanisms.",
    year=2017,
)


def _make_llm(responses: dict[str, str]):
    """Return a fake LLM that echoes canned responses based on keyword lookup."""
    call_count = {"n": 0}

    def llm(prompt: str) -> str:
        call_count["n"] += 1
        for keyword, response in responses.items():
            if keyword.lower() in prompt.lower():
                return response
        return "VERDICT: LOW\nEXPLANATION: No issue found.\nREFERENCES: none"

    llm.call_count = call_count
    return llm


_DUP_RESPONSE = (
    "VERDICT: HIGH\n"
    "EXPLANATION: This paper duplicates the attention mechanism from att2017.\n"
    "REFERENCES: att2017"
)
_COMBO_RESPONSE = (
    "VERDICT: MEDIUM\n"
    "EXPLANATION: The paper combines attention with dynamic masking.\n"
    "REFERENCES: att2017, bert2019"
)
_EQUIV_RESPONSE = (
    "VERDICT: LOW\n"
    "EXPLANATION: No direct methodological equivalence found.\n"
    "REFERENCES: none"
)
_SYNTH_RESPONSE = (
    "OVERALL_VERDICT: NOT_NOVEL\n"
    "CONFIDENCE: HIGH\n"
    "SUMMARY: The paper is largely a duplicate of prior attention work."
)
_DECOMP_RESPONSE = (
    "CORE_CONCEPT: A dynamic masking extension of the Transformer attention mechanism.\n"
    "SUB_IDEAS:\n"
    "1. Dynamic attention masking\n"
    "2. Integration with standard Transformer blocks\n"
    "ASSUMPTIONS:\n"
    "1. Input sequences are tokenised uniformly\n"
    "LIMITATIONS:\n"
    "1. Only evaluated on NLP benchmarks\n"
    "CONCEPT_TREE:\n"
    "Dynamic Masking Transformer\n"
    "  Problem: Standard attention lacks input-dependent masking\n"
    "    Gap: Fixed mask patterns cannot adapt to content\n"
    "  Method: Dynamic attention masking mechanism\n"
    "    Component: Learnable gating function\n"
    "      Implementation: Element-wise sigmoid activation\n"
    "    Integration: Standard Transformer encoder blocks\n"
    "  Evaluation: NLP benchmarks only\n"
    "    Limitation: Narrow evaluation scope\n"
)
_DOMAIN_REFS_RESPONSE = (
    "REFERENCES:\n"
    "1. TITLE: Attention Is All You Need | AUTHORS: Vaswani et al. | YEAR: 2017 | RELEVANCE: Foundational Transformer work\n"
    "2. TITLE: BERT | AUTHORS: Devlin et al. | YEAR: 2018 | RELEVANCE: Pre-training with masked attention"
)


def _make_full_llm():
    """LLM that returns appropriate canned responses for each pass."""
    responses_in_order = [
        _DECOMP_RESPONSE,
        _DUP_RESPONSE,
        _COMBO_RESPONSE,
        _EQUIV_RESPONSE,
        _SYNTH_RESPONSE,
        _DOMAIN_REFS_RESPONSE,
    ]
    call_idx = {"i": 0}

    def llm(_prompt: str) -> str:
        idx = call_idx["i"]
        call_idx["i"] += 1
        if idx < len(responses_in_order):
            return responses_in_order[idx]
        return "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none"

    return llm


# ---------------------------------------------------------------------------
# Unit tests for response parsers
# ---------------------------------------------------------------------------

class TestExtractField:
    def test_extracts_simple_field(self):
        text = "VERDICT: HIGH\nEXPLANATION: Because of X.\nREFERENCES: p1"
        assert _extract_field(text, "VERDICT") == "HIGH"

    def test_extracts_multiline_field(self):
        text = "VERDICT: LOW\nEXPLANATION: Line one.\nLine two.\nREFERENCES: none"
        expl = _extract_field(text, "EXPLANATION")
        assert "Line one" in expl
        assert "Line two" in expl

    def test_returns_default_when_field_missing(self):
        assert _extract_field("nothing here", "VERDICT", default="X") == "X"

    def test_case_insensitive(self):
        text = "verdict: MEDIUM\n"
        assert _extract_field(text, "VERDICT") == "MEDIUM"

    def test_returns_default_when_field_value_is_empty(self):
        """An empty field value should fall back to *default*, not return ''."""
        text = "VERDICT: HIGH\nEXPLANATION:\nREFERENCES: att2017"
        assert _extract_field(text, "EXPLANATION", default="fallback") == "fallback"

    def test_does_not_consume_newline_after_colon(self):
        """The field value must not bleed into the next field when the value is blank.

        Previously, the greedy ``\\s*`` after the colon consumed the newline,
        causing ``(.*?)`` to capture the *next* field's content.
        """
        text = "VERDICT: HIGH\nEXPLANATION:\nREFERENCES: att2017"
        expl = _extract_field(text, "EXPLANATION", default="")
        assert "REFERENCES" not in expl

    def test_lowercase_label_in_value_does_not_terminate_field(self):
        """A ``word:`` at the start of a line inside a field value must not cut
        the field short.  Only all-uppercase labels like ``REFERENCES:`` should
        act as field terminators.
        """
        text = (
            "EXPLANATION: The method relies on attention.\n"
            "Note: this extends prior work.\n"
            "REFERENCES: att2017"
        )
        expl = _extract_field(text, "EXPLANATION")
        assert "Note: this extends prior work" in expl

    def test_uppercase_label_still_terminates_field(self):
        """An all-uppercase ``FIELD:`` at the start of a line must still mark
        the end of the preceding field.
        """
        text = "EXPLANATION: Some explanation.\nREFERENCES: p1"
        expl = _extract_field(text, "EXPLANATION")
        assert "REFERENCES" not in expl

    def test_handles_markdown_bold_wrapped_fields(self):
        """Fields wrapped in ``**...**`` should still be parsed correctly.

        LLMs sometimes return ``**FIELD:** value`` or ``**FIELD:**\\nvalue``
        instead of the plain ``FIELD: value`` format the prompt requests.
        """
        text = (
            "**VERDICT:** HIGH\n"
            "**EXPLANATION:** The paper is novel.\n"
            "**REFERENCES:** none"
        )
        assert _extract_field(text, "VERDICT") == "HIGH"
        assert "novel" in _extract_field(text, "EXPLANATION")

    def test_bold_wrapped_field_does_not_bleed_into_next(self):
        """A bold-wrapped field terminator must stop the preceding field."""
        text = (
            "**VERDICT:** LOW\n"
            "**EXPLANATION:** Fine.\n"
            "**REFERENCES:** p1"
        )
        expl = _extract_field(text, "EXPLANATION")
        assert "REFERENCES" not in expl

    def test_bold_wrapped_multiline_list_field(self):
        """Bold-wrapped label with a numbered list value should parse fully."""
        text = (
            "**CORE_CONCEPT:** Central idea here.\n"
            "**SUB_IDEAS:**\n"
            "1. First sub-idea\n"
            "2. Second sub-idea\n"
            "**ASSUMPTIONS:**\n"
            "1. Assumes linearity"
        )
        sub_ideas_raw = _extract_field(text, "SUB_IDEAS")
        from open_idea_sourcing.novelty_evaluator import _parse_numbered_list
        items = _parse_numbered_list(sub_ideas_raw)
        assert items == ["First sub-idea", "Second sub-idea"]

    def test_full_decomp_with_bold_wrapped_fields(self):
        """_parse_decomposition_response should correctly parse bold-wrapped LLM output."""
        text = (
            "**CORE_CONCEPT:** A conformal inference approach for ITE estimation.\n"
            "**SUB_IDEAS:**\n"
            "1. Coverage guarantees in finite samples\n"
            "2. Doubly robust property\n"
            "**ASSUMPTIONS:**\n"
            "1. Potential outcome framework\n"
            "**LIMITATIONS:**\n"
            "1. Requires accurate propensity estimation"
        )
        d = _parse_decomposition_response(text)
        assert "conformal" in d.core_concept.lower()
        assert len(d.sub_ideas) == 2
        assert len(d.assumptions) == 1
        assert len(d.limitations) == 1


class TestParseDimensionResponse:
    def test_parses_all_fields(self):
        verdict, explanation, refs = _parse_dimension_response(_DUP_RESPONSE)
        assert verdict == "HIGH"
        assert "att2017" in explanation
        assert "att2017" in refs

    def test_empty_references(self):
        text = "VERDICT: LOW\nEXPLANATION: Fine.\nREFERENCES: none"
        _, _, refs = _parse_dimension_response(text)
        assert refs == []

    def test_multiple_references(self):
        text = "VERDICT: MEDIUM\nEXPLANATION: ...\nREFERENCES: p1, p2, p3"
        _, _, refs = _parse_dimension_response(text)
        assert set(refs) == {"p1", "p2", "p3"}

    def test_empty_explanation_does_not_capture_next_field(self):
        """When EXPLANATION value is empty, its text must not be set to only
        the next field's content (regression for the greedy ``\\s*`` bug).
        """
        text = "VERDICT: HIGH\nEXPLANATION:\nREFERENCES: att2017"
        _, explanation, _ = _parse_dimension_response(text)
        # Old bug: explanation was set to exactly "REFERENCES: att2017"
        assert explanation != "REFERENCES: att2017"

    def test_explanation_preserved_when_value_contains_lowercase_labels(self):
        """Inline ``word:`` labels in the explanation must not truncate it."""
        text = (
            "VERDICT: LOW\n"
            "EXPLANATION: The paper is novel.\nNote: see section 3.\n"
            "REFERENCES: none"
        )
        _, explanation, _ = _parse_dimension_response(text)
        assert "Note: see section 3" in explanation


class TestParseSynthesisResponse:
    def test_parses_synthesis(self):
        verdict, confidence, summary = _parse_synthesis_response(_SYNTH_RESPONSE)
        assert verdict == "NOT_NOVEL"
        assert confidence == "HIGH"
        assert "duplicate" in summary.lower()

    def test_empty_summary_falls_back_to_full_response(self):
        """When SUMMARY is present but empty the full response text is used."""
        text = "OVERALL_VERDICT: NOVEL\nCONFIDENCE: HIGH\nSUMMARY:"
        _, _, summary = _parse_synthesis_response(text)
        # Should not be blank — falls back to the raw LLM response text.
        assert summary != ""

    def test_summary_not_blank_when_response_has_no_summary_field(self):
        """When there is no SUMMARY field the full response text is used."""
        text = "OVERALL_VERDICT: NOVEL\nCONFIDENCE: HIGH\nThe paper is novel."
        _, _, summary = _parse_synthesis_response(text)
        assert summary != ""


# ---------------------------------------------------------------------------
# Unit tests for NoveltyEvaluator
# ---------------------------------------------------------------------------

class TestNoveltyEvaluator:
    def _make_similar(self):
        return [
            SimilarityResult(paper=SAMPLE_REFERENCE, score=0.85)
        ]

    def test_evaluate_returns_novelty_report(self):
        llm = _make_full_llm()
        evaluator = NoveltyEvaluator(llm=llm)
        report = evaluator.evaluate(SAMPLE_PAPER, similar_papers=self._make_similar())
        assert isinstance(report, NoveltyReport)

    def test_report_has_correct_title(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert report.paper_title == SAMPLE_PAPER.title

    def test_report_has_three_dimensions(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert len(report.dimensions) == 3

    def test_dimension_names(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        names = {d.name for d in report.dimensions}
        assert "Direct Duplication" in names
        assert "Simple Combination" in names
        assert "Methodological Equivalence" in names

    def test_overall_verdict_set(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert report.overall_verdict in {
            "NOVEL", "MARGINAL", "NOT_NOVEL", "UNCLEAR"
        }

    def test_raw_llm_responses_stored(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert "duplication" in report.raw_llm_responses
        assert "combination" in report.raw_llm_responses
        assert "equivalence" in report.raw_llm_responses
        assert "synthesis" in report.raw_llm_responses

    def test_similar_papers_attached_to_report(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        similar = self._make_similar()
        report = evaluator.evaluate(SAMPLE_PAPER, similar_papers=similar)
        assert report.similar_papers == similar

    def test_evaluate_without_references(self):
        """Evaluator should work fine with no reference papers provided."""
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert report is not None

    def test_llm_called_exactly_six_times(self):
        calls = []
        def counting_llm(prompt: str) -> str:
            calls.append(prompt)
            return "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none"

        evaluator = NoveltyEvaluator(llm=counting_llm)
        evaluator.evaluate(SAMPLE_PAPER)
        # 3 dimension passes + 1 synthesis + 1 idea decomposition + 1 domain refs
        assert len(calls) == 6

    def test_duplication_high_leads_to_not_novel(self):
        """When duplication is HIGH, synthesis should reflect that."""
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER, similar_papers=self._make_similar())
        # Our canned synthesis says NOT_NOVEL
        assert report.overall_verdict == "NOT_NOVEL"

    def test_format_references_empty(self):
        text = NoveltyEvaluator.format_references([])
        assert "No reference papers provided" in text

    def test_format_references_shows_title(self):
        similar = [SimilarityResult(paper=SAMPLE_REFERENCE, score=0.9)]
        text = NoveltyEvaluator.format_references(similar)
        assert "Attention Is All You Need" in text
        assert "0.90" in text


# ---------------------------------------------------------------------------
# NoveltyEvaluator.evaluate() with metadata (job log)
# ---------------------------------------------------------------------------

class TestNoveltyEvaluatorJobLog:
    def _make_metadata(self) -> "RunMetadata":
        from open_idea_sourcing.novelty_evaluator import RunMetadata
        return RunMetadata(model="gpt-test", input_source="paper.txt")

    def test_evaluate_with_metadata_appends_six_jobs(self):
        meta = self._make_metadata()
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        evaluator.evaluate(SAMPLE_PAPER, metadata=meta)
        # 6 LLM jobs: duplication, combination, equivalence, synthesis,
        # idea decomposition, domain references
        assert len(meta.jobs) == 6

    def test_evaluate_job_names(self):
        meta = self._make_metadata()
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        evaluator.evaluate(SAMPLE_PAPER, metadata=meta)
        names = [j.name for j in meta.jobs]
        assert "Duplication check" in names
        assert "Combination check" in names
        assert "Equivalence check" in names
        assert "Synthesis" in names
        assert "Idea decomposition" in names
        assert "Domain references" in names

    def test_evaluate_job_agent_includes_model(self):
        meta = self._make_metadata()
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        evaluator.evaluate(SAMPLE_PAPER, metadata=meta)
        for job in meta.jobs:
            assert "gpt-test" in job.agent

    def test_evaluate_without_metadata_no_jobs(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert report.metadata is None

    def test_evaluate_jobs_have_non_negative_durations(self):
        meta = self._make_metadata()
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        evaluator.evaluate(SAMPLE_PAPER, metadata=meta)
        for job in meta.jobs:
            assert job.duration_s >= 0.0

    def test_pre_existing_jobs_are_preserved(self):
        from open_idea_sourcing.novelty_evaluator import PipelineJob, RunMetadata
        meta = RunMetadata(model="gpt-test", input_source="paper.txt")
        meta.jobs.append(PipelineJob(
            name="Parse paper", agent="PaperParser",
            offset_s=0.0, duration_s=0.3,
            input_summary="paper.txt",
            output_summary='"My Paper", 500 chars',
        ))
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        evaluator.evaluate(SAMPLE_PAPER, metadata=meta)
        # 1 pre-existing + 6 from evaluator = 7
        assert len(meta.jobs) == 7
        assert meta.jobs[0].name == "Parse paper"


# ---------------------------------------------------------------------------
# IdeaDecomposition dataclass
# ---------------------------------------------------------------------------

class TestIdeaDecomposition:
    def test_default_lists_empty(self):
        d = IdeaDecomposition(core_concept="A new method.")
        assert d.sub_ideas == []
        assert d.assumptions == []
        assert d.limitations == []

    def test_fields_stored(self):
        d = IdeaDecomposition(
            core_concept="Core.",
            sub_ideas=["A", "B"],
            assumptions=["X"],
            limitations=["Y"],
        )
        assert d.core_concept == "Core."
        assert d.sub_ideas == ["A", "B"]
        assert d.assumptions == ["X"]
        assert d.limitations == ["Y"]


# ---------------------------------------------------------------------------
# DomainReference dataclass
# ---------------------------------------------------------------------------

class TestDomainReference:
    def test_defaults(self):
        ref = DomainReference(title="Some Paper")
        assert ref.authors == ""
        assert ref.year == ""
        assert ref.relevance == ""

    def test_all_fields(self):
        ref = DomainReference(
            title="Attention Is All You Need",
            authors="Vaswani et al.",
            year="2017",
            relevance="Foundational Transformer work",
        )
        assert ref.title == "Attention Is All You Need"
        assert ref.authors == "Vaswani et al."
        assert ref.year == "2017"
        assert "Transformer" in ref.relevance


# ---------------------------------------------------------------------------
# _parse_numbered_list
# ---------------------------------------------------------------------------

class TestParseNumberedList:
    def test_parses_dot_separated(self):
        text = "1. First item\n2. Second item\n3. Third item"
        items = _parse_numbered_list(text)
        assert items == ["First item", "Second item", "Third item"]

    def test_parses_paren_separated(self):
        text = "1) Alpha\n2) Beta"
        items = _parse_numbered_list(text)
        assert items == ["Alpha", "Beta"]

    def test_ignores_non_numbered_lines(self):
        text = "Header\n1. Item one\nsome text\n2. Item two"
        items = _parse_numbered_list(text)
        assert items == ["Item one", "Item two"]

    def test_empty_text(self):
        assert _parse_numbered_list("") == []

    def test_no_numbered_items(self):
        assert _parse_numbered_list("just plain text\nwith no numbers") == []


# ---------------------------------------------------------------------------
# _parse_decomposition_response
# ---------------------------------------------------------------------------

class TestParseDecompositionResponse:
    def test_parses_full_response(self):
        d = _parse_decomposition_response(_DECOMP_RESPONSE)
        assert "dynamic masking" in d.core_concept.lower()
        assert "Dynamic attention masking" in d.sub_ideas
        assert "Input sequences are tokenised uniformly" in d.assumptions
        assert "Only evaluated on NLP benchmarks" in d.limitations

    def test_missing_core_concept_falls_back_to_full_text(self):
        d = _parse_decomposition_response("Some random text without fields.")
        assert d.core_concept != ""

    def test_missing_lists_default_to_empty(self):
        d = _parse_decomposition_response("CORE_CONCEPT: Simple idea.\n")
        assert d.sub_ideas == []
        assert d.assumptions == []
        assert d.limitations == []

    def test_returns_idea_decomposition_instance(self):
        d = _parse_decomposition_response(_DECOMP_RESPONSE)
        assert isinstance(d, IdeaDecomposition)


# ---------------------------------------------------------------------------
# _parse_domain_references_response
# ---------------------------------------------------------------------------

class TestParseDomainReferencesResponse:
    def test_parses_two_references(self):
        refs = _parse_domain_references_response(_DOMAIN_REFS_RESPONSE)
        assert len(refs) == 2

    def test_first_reference_title(self):
        refs = _parse_domain_references_response(_DOMAIN_REFS_RESPONSE)
        assert refs[0].title == "Attention Is All You Need"

    def test_first_reference_year(self):
        refs = _parse_domain_references_response(_DOMAIN_REFS_RESPONSE)
        assert refs[0].year == "2017"

    def test_first_reference_authors(self):
        refs = _parse_domain_references_response(_DOMAIN_REFS_RESPONSE)
        assert "Vaswani" in refs[0].authors

    def test_first_reference_relevance(self):
        refs = _parse_domain_references_response(_DOMAIN_REFS_RESPONSE)
        assert "Transformer" in refs[0].relevance

    def test_second_reference_title(self):
        refs = _parse_domain_references_response(_DOMAIN_REFS_RESPONSE)
        assert refs[1].title == "BERT"

    def test_returns_list_of_domain_references(self):
        refs = _parse_domain_references_response(_DOMAIN_REFS_RESPONSE)
        assert all(isinstance(r, DomainReference) for r in refs)

    def test_empty_response_returns_empty_list(self):
        refs = _parse_domain_references_response("REFERENCES:\n")
        assert refs == []

    def test_lines_without_title_are_skipped(self):
        text = "REFERENCES:\n1. AUTHORS: Nobody | YEAR: 2020 | RELEVANCE: Unclear\n"
        refs = _parse_domain_references_response(text)
        assert refs == []


# ---------------------------------------------------------------------------
# NoveltyEvaluator — enriched fields
# ---------------------------------------------------------------------------

class TestNoveltyEvaluatorEnrichedReport:
    def test_evaluate_returns_idea_decomposition(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert report.idea_decomposition is not None
        assert isinstance(report.idea_decomposition, IdeaDecomposition)

    def test_evaluate_returns_domain_references(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert isinstance(report.domain_references, list)

    def test_idea_decomposition_has_core_concept(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert report.idea_decomposition.core_concept != ""

    def test_domain_references_has_entries(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert len(report.domain_references) == 2

    def test_raw_llm_responses_include_decomposition(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert "idea_decomposition" in report.raw_llm_responses

    def test_raw_llm_responses_include_domain_references(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert "domain_references" in report.raw_llm_responses


# ---------------------------------------------------------------------------
# NoveltyEvaluator._decompose_idea / _find_domain_references (isolated)
# ---------------------------------------------------------------------------

class TestDecomposeIdeaMethod:
    def test_calls_llm_once(self):
        calls = []
        def llm(prompt: str) -> str:
            calls.append(prompt)
            return _DECOMP_RESPONSE
        evaluator = NoveltyEvaluator(llm=llm)
        raw: dict = {}
        result = evaluator._decompose_idea("some content", raw)
        assert len(calls) == 1

    def test_prompt_contains_paper_content(self):
        received = []
        def llm(prompt: str) -> str:
            received.append(prompt)
            return _DECOMP_RESPONSE
        evaluator = NoveltyEvaluator(llm=llm)
        evaluator._decompose_idea("unique content string xyz", {})
        assert "unique content string xyz" in received[0]

    def test_response_stored_in_raw(self):
        evaluator = NoveltyEvaluator(llm=lambda _: _DECOMP_RESPONSE)
        raw: dict = {}
        evaluator._decompose_idea("content", raw)
        assert raw.get("idea_decomposition") == _DECOMP_RESPONSE

    def test_returns_idea_decomposition(self):
        evaluator = NoveltyEvaluator(llm=lambda _: _DECOMP_RESPONSE)
        result = evaluator._decompose_idea("content", {})
        assert isinstance(result, IdeaDecomposition)
        assert result.core_concept != ""


class TestFindDomainReferencesMethod:
    def test_calls_llm_once(self):
        calls = []
        def llm(prompt: str) -> str:
            calls.append(prompt)
            return _DOMAIN_REFS_RESPONSE
        evaluator = NoveltyEvaluator(llm=llm)
        evaluator._find_domain_references("content", "No references.", {})
        assert len(calls) == 1

    def test_prompt_contains_paper_content(self):
        received = []
        def llm(prompt: str) -> str:
            received.append(prompt)
            return _DOMAIN_REFS_RESPONSE
        evaluator = NoveltyEvaluator(llm=llm)
        evaluator._find_domain_references("special content abc", "refs", {})
        assert "special content abc" in received[0]

    def test_response_stored_in_raw(self):
        evaluator = NoveltyEvaluator(llm=lambda _: _DOMAIN_REFS_RESPONSE)
        raw: dict = {}
        evaluator._find_domain_references("content", "refs", raw)
        assert raw.get("domain_references") == _DOMAIN_REFS_RESPONSE

    def test_returns_list_of_domain_references(self):
        evaluator = NoveltyEvaluator(llm=lambda _: _DOMAIN_REFS_RESPONSE)
        result = evaluator._find_domain_references("content", "refs", {})
        assert isinstance(result, list)
        assert all(isinstance(r, DomainReference) for r in result)


# ---------------------------------------------------------------------------
# _parse_similar_paper_annotations_response
# ---------------------------------------------------------------------------

_ANNOTATION_RESPONSE = """\
PAPER [arxiv-1904.06019]:
OVERLAP: Both use mini-batch gradient descent and momentum optimisers.
DIFFERENCES: The submitted paper targets image classification; the reference focuses on language models.
DERIVATION: The learning-rate scheduling heuristic in the submitted paper appears adapted from Shallue et al. 2019.

PAPER [bert2018]:
OVERLAP: Both pre-train on large text corpora.
DIFFERENCES: The submitted paper uses a custom tokeniser instead of WordPiece.
DERIVATION: None identified.
"""


class TestParseSimilarPaperAnnotationsResponse:
    def test_returns_list_of_similarity_annotations(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert isinstance(result, list)
        assert all(isinstance(a, SimilarityAnnotation) for a in result)

    def test_correct_number_of_annotations(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert len(result) == 2

    def test_first_annotation_paper_id(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert result[0].paper_id == "arxiv-1904.06019"

    def test_second_annotation_paper_id(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert result[1].paper_id == "bert2018"

    def test_overlap_extracted(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert "mini-batch gradient descent" in result[0].overlap

    def test_differences_extracted(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert "image classification" in result[0].differences

    def test_derivation_extracted(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert "learning-rate scheduling" in result[0].derivation

    def test_empty_response_returns_empty_list(self):
        result = _parse_similar_paper_annotations_response("")
        assert result == []

    def test_malformed_blocks_skipped(self):
        result = _parse_similar_paper_annotations_response(
            "Some preamble without any PAPER markers."
        )
        assert result == []

    def test_none_derivation_preserved(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert result[1].derivation == "None identified."


class TestAnnotateSimilarPapersMethod:
    def test_calls_llm_and_stores_in_raw(self):
        evaluator = NoveltyEvaluator(llm=lambda _: _ANNOTATION_RESPONSE)
        paper_ref = ReferencePaper(
            id="arxiv-1904.06019",
            title="Data Parallelism",
            abstract="abstract",
        )
        similar = [SimilarityResult(paper=paper_ref, score=0.5)]
        raw: dict = {}
        result = evaluator._annotate_similar_papers("content", similar, raw)
        assert "similar_paper_annotations" in raw
        assert raw["similar_paper_annotations"] == _ANNOTATION_RESPONSE

    def test_returns_list_of_similarity_annotations(self):
        evaluator = NoveltyEvaluator(llm=lambda _: _ANNOTATION_RESPONSE)
        paper_ref = ReferencePaper(
            id="arxiv-1904.06019",
            title="Data Parallelism",
            abstract="abstract",
        )
        similar = [SimilarityResult(paper=paper_ref, score=0.5)]
        result = evaluator._annotate_similar_papers("content", similar, {})
        assert isinstance(result, list)
        assert len(result) >= 1
        assert isinstance(result[0], SimilarityAnnotation)


# ---------------------------------------------------------------------------
# ConceptNode dataclass
# ---------------------------------------------------------------------------

class TestConceptNode:
    def test_default_children_empty(self):
        node = ConceptNode(label="Root")
        assert node.children == []

    def test_label_stored(self):
        node = ConceptNode(label="My node")
        assert node.label == "My node"

    def test_children_stored(self):
        child = ConceptNode(label="Child")
        root = ConceptNode(label="Root", children=[child])
        assert len(root.children) == 1
        assert root.children[0].label == "Child"

    def test_nested_children(self):
        grandchild = ConceptNode(label="Grandchild")
        child = ConceptNode(label="Child", children=[grandchild])
        root = ConceptNode(label="Root", children=[child])
        assert root.children[0].children[0].label == "Grandchild"


# ---------------------------------------------------------------------------
# _parse_concept_tree_text
# ---------------------------------------------------------------------------

_TREE_TEXT = (
    "Dynamic Masking Transformer\n"
    "  Problem: Standard attention lacks input-dependent masking\n"
    "    Gap: Fixed mask patterns cannot adapt to content\n"
    "  Method: Dynamic attention masking mechanism\n"
    "    Component: Learnable gating function\n"
    "    Integration: Standard Transformer encoder blocks\n"
)


class TestParseConceptTreeText:
    def test_returns_concept_node_instance(self):
        result = _parse_concept_tree_text(_TREE_TEXT)
        assert isinstance(result, ConceptNode)

    def test_root_label(self):
        result = _parse_concept_tree_text(_TREE_TEXT)
        assert result.label == "Dynamic Masking Transformer"

    def test_root_has_two_children(self):
        result = _parse_concept_tree_text(_TREE_TEXT)
        assert len(result.children) == 2

    def test_first_child_label(self):
        result = _parse_concept_tree_text(_TREE_TEXT)
        assert result.children[0].label == "Problem: Standard attention lacks input-dependent masking"

    def test_second_child_label(self):
        result = _parse_concept_tree_text(_TREE_TEXT)
        assert result.children[1].label == "Method: Dynamic attention masking mechanism"

    def test_grandchild_of_problem(self):
        result = _parse_concept_tree_text(_TREE_TEXT)
        problem_node = result.children[0]
        assert len(problem_node.children) == 1
        assert "Gap" in problem_node.children[0].label

    def test_method_has_two_children(self):
        result = _parse_concept_tree_text(_TREE_TEXT)
        method_node = result.children[1]
        assert len(method_node.children) == 2

    def test_empty_text_returns_none(self):
        assert _parse_concept_tree_text("") is None

    def test_whitespace_only_returns_none(self):
        assert _parse_concept_tree_text("   \n  \n") is None

    def test_single_line_returns_root_only(self):
        result = _parse_concept_tree_text("Just a root node\n")
        assert result is not None
        assert result.label == "Just a root node"
        assert result.children == []

    def test_blank_lines_ignored(self):
        text = "Root\n\n  Child 1\n\n  Child 2\n"
        result = _parse_concept_tree_text(text)
        assert len(result.children) == 2

    def test_four_space_indent(self):
        text = "Root\n    Child A\n        Grandchild A1\n    Child B\n"
        result = _parse_concept_tree_text(text)
        assert len(result.children) == 2
        assert len(result.children[0].children) == 1

    def test_deep_nesting(self):
        text = (
            "Root\n"
            "  L1\n"
            "    L2\n"
            "      L3\n"
            "        L4\n"
        )
        result = _parse_concept_tree_text(text)
        l1 = result.children[0]
        l2 = l1.children[0]
        l3 = l2.children[0]
        l4 = l3.children[0]
        assert l4.label == "L4"

    def test_multiple_top_level_subtrees(self):
        """Siblings at the same level should all be children of root."""
        text = "Root\n  A\n    A1\n  B\n    B1\n  C\n"
        result = _parse_concept_tree_text(text)
        assert len(result.children) == 3

    def test_parses_decomp_response_tree(self):
        """The tree embedded in _DECOMP_RESPONSE should parse without error."""
        concept_tree_raw = (
            "Dynamic Masking Transformer\n"
            "  Problem: Standard attention lacks input-dependent masking\n"
            "    Gap: Fixed mask patterns cannot adapt to content\n"
            "  Method: Dynamic attention masking mechanism\n"
            "    Component: Learnable gating function\n"
            "      Implementation: Element-wise sigmoid activation\n"
            "    Integration: Standard Transformer encoder blocks\n"
            "  Evaluation: NLP benchmarks only\n"
            "    Limitation: Narrow evaluation scope\n"
        )
        result = _parse_concept_tree_text(concept_tree_raw)
        assert result is not None
        assert result.label == "Dynamic Masking Transformer"
        assert len(result.children) == 3


# ---------------------------------------------------------------------------
# IdeaDecomposition — concept_tree field
# ---------------------------------------------------------------------------

class TestIdeaDecompositionConceptTree:
    def test_concept_tree_defaults_to_none(self):
        d = IdeaDecomposition(core_concept="A new method.")
        assert d.concept_tree is None

    def test_concept_tree_can_be_set(self):
        tree = ConceptNode(label="Root", children=[ConceptNode(label="Child")])
        d = IdeaDecomposition(core_concept="Core.", concept_tree=tree)
        assert d.concept_tree is not None
        assert d.concept_tree.label == "Root"


# ---------------------------------------------------------------------------
# _parse_decomposition_response — with CONCEPT_TREE section
# ---------------------------------------------------------------------------

class TestParseDecompositionWithConceptTree:
    def test_parses_concept_tree_from_full_response(self):
        d = _parse_decomposition_response(_DECOMP_RESPONSE)
        assert d.concept_tree is not None

    def test_concept_tree_root_label(self):
        d = _parse_decomposition_response(_DECOMP_RESPONSE)
        assert d.concept_tree.label == "Dynamic Masking Transformer"

    def test_concept_tree_has_children(self):
        d = _parse_decomposition_response(_DECOMP_RESPONSE)
        assert len(d.concept_tree.children) > 0

    def test_concept_tree_none_when_absent(self):
        response = (
            "CORE_CONCEPT: Simple idea.\n"
            "SUB_IDEAS:\n1. Item\n"
            "ASSUMPTIONS:\n1. Uniform input\n"
            "LIMITATIONS:\n1. Narrow scope\n"
        )
        d = _parse_decomposition_response(response)
        assert d.concept_tree is None

    def test_flat_fields_still_populated(self):
        """Flat fields must still work alongside the concept tree."""
        d = _parse_decomposition_response(_DECOMP_RESPONSE)
        assert len(d.sub_ideas) == 2
        assert len(d.assumptions) == 1
        assert len(d.limitations) == 1
