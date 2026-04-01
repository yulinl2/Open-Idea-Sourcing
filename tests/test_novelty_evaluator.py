"""Tests for open_idea_sourcing.novelty_evaluator."""

import pytest

from open_idea_sourcing.novelty_evaluator import (
    DomainReference,
    IdeaDecomposition,
    NoveltyDimension,
    NoveltyEvaluator,
    NoveltyReport,
    PipelineContext,
    RunMetadata,
    SimilarityAnnotation,
    _extract_field,
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
    "1. Only evaluated on NLP benchmarks"
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

@pytest.mark.slow
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
        assert "REF-1" in text


class TestFormatReferencesRefNFormat:
    def test_first_reference_uses_ref_1(self):
        similar = [SimilarityResult(paper=SAMPLE_REFERENCE, score=0.9)]
        text = NoveltyEvaluator.format_references(similar)
        assert "REF-1" in text

    def test_second_reference_uses_ref_2(self):
        ref2 = ReferencePaper(id="bert2019", title="BERT", abstract="BERT paper.", year=2019)
        similar = [
            SimilarityResult(paper=SAMPLE_REFERENCE, score=0.9),
            SimilarityResult(paper=ref2, score=0.7),
        ]
        text = NoveltyEvaluator.format_references(similar)
        assert "REF-1" in text
        assert "REF-2" in text

    def test_ref_n_label_precedes_bracket_id(self):
        similar = [SimilarityResult(paper=SAMPLE_REFERENCE, score=0.9)]
        text = NoveltyEvaluator.format_references(similar)
        ref1_pos = text.index("REF-1")
        bracket_pos = text.index("[att2017]")
        assert ref1_pos < bracket_pos

    def test_format_references_empty_unchanged(self):
        assert "No reference papers provided" in NoveltyEvaluator.format_references([])


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
        assert d.concept_tree is None

    def test_fields_stored(self):
        d = IdeaDecomposition(
            core_concept="Core.",
            concept_tree="1. Root concept\n2. Sub-component",
        )
        assert d.core_concept == "Core."
        assert d.concept_tree == "1. Root concept\n2. Sub-component"


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
        assert isinstance(d, IdeaDecomposition)

    def test_missing_core_concept_falls_back_to_full_text(self):
        d = _parse_decomposition_response("Some random text without fields.")
        assert d.core_concept != ""

    def test_missing_lists_default_to_empty(self):
        d = _parse_decomposition_response("CORE_CONCEPT: Simple idea.\n")
        assert d.concept_tree is None

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

@pytest.mark.slow
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

@pytest.mark.slow
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


@pytest.mark.slow
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
DERIVATION_MAP:
- attention mechanism: REF-1, REF-2
- training recipe: REF-3
COMBINATION_ANALYSIS: The submitted paper combines multi-head attention from REF-1 with the training recipe from REF-3, yielding a moderately novel synthesis.
NOVEL_ELEMENTS:
- Dynamic masking strategy
- Adaptive learning rate schedule
"""


class TestParseSimilarPaperAnnotationsResponse:
    def test_returns_list_of_similarity_annotations(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert isinstance(result, list)
        assert all(isinstance(a, SimilarityAnnotation) for a in result)

    def test_correct_number_of_annotations(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert len(result) == 1  # 1-to-all: always returns a single annotation

    def test_derivation_map_keys_extracted(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert "attention mechanism" in result[0].derivation_map

    def test_derivation_map_refs_extracted(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        refs = result[0].derivation_map["attention mechanism"]
        assert "REF-1" in refs
        assert "REF-2" in refs

    def test_combination_analysis_extracted(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert "multi-head attention" in result[0].combination_analysis

    def test_novel_elements_extracted(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert "Dynamic masking strategy" in result[0].novel_elements

    def test_empty_response_returns_single_empty_annotation(self):
        result = _parse_similar_paper_annotations_response("")
        assert len(result) == 1
        assert result[0].derivation_map == {}
        assert result[0].combination_analysis == ""
        assert result[0].novel_elements == []

    def test_unstructured_response_returns_single_empty_annotation(self):
        result = _parse_similar_paper_annotations_response(
            "Some preamble without any structured markers."
        )
        assert len(result) == 1
        assert result[0].derivation_map == {}

    def test_paper_id_defaults_to_empty(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert result[0].paper_id == ""

    def test_training_recipe_component_present(self):
        result = _parse_similar_paper_annotations_response(_ANNOTATION_RESPONSE)
        assert "training recipe" in result[0].derivation_map
        assert "REF-3" in result[0].derivation_map["training recipe"]


@pytest.mark.slow
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

from open_idea_sourcing.novelty_evaluator import ConceptNode


class TestConceptNode:
    def test_leaf_node(self):
        node = ConceptNode(label="leaf")
        assert node.label == "leaf"
        assert node.children == []

    def test_node_with_children(self):
        child = ConceptNode(label="child")
        parent = ConceptNode(label="parent", children=[child])
        assert parent.children[0].label == "child"

    def test_default_children_empty(self):
        node = ConceptNode(label="x")
        assert node.children == []

    def test_deep_nesting(self):
        leaf = ConceptNode(label="leaf")
        mid = ConceptNode(label="mid", children=[leaf])
        root = ConceptNode(label="root", children=[mid])
        assert root.children[0].children[0].label == "leaf"


# ---------------------------------------------------------------------------
# _parse_concept_tree_text
# ---------------------------------------------------------------------------

from open_idea_sourcing.novelty_evaluator import _parse_concept_tree_text


class TestParseConceptTreeText:
    def test_empty_returns_none(self):
        assert _parse_concept_tree_text("") is None

    def test_whitespace_only_returns_none(self):
        assert _parse_concept_tree_text("   \n   ") is None

    def test_single_line_no_indent_returns_single_root(self):
        result = _parse_concept_tree_text("Problem")
        assert result is not None
        assert result.label == "Problem"
        assert result.children == []

    def test_multiple_non_indented_lines_returns_none(self):
        result = _parse_concept_tree_text("Problem\nMethod\nEvidence")
        assert result is None

    def test_two_level_tree(self):
        text = "Problem\n  Sub-problem A\n  Sub-problem B"
        root = _parse_concept_tree_text(text)
        assert root is not None
        assert root.label == "Problem"
        assert len(root.children) == 2
        assert root.children[0].label == "Sub-problem A"
        assert root.children[1].label == "Sub-problem B"

    def test_three_level_tree(self):
        text = (
            "Problem\n"
            "  Sub-problem A\n"
            "    Detail 1\n"
            "    Detail 2\n"
            "  Sub-problem B\n"
        )
        root = _parse_concept_tree_text(text)
        assert root is not None
        assert root.label == "Problem"
        assert len(root.children) == 2
        assert len(root.children[0].children) == 2
        assert root.children[0].children[0].label == "Detail 1"

    def test_four_space_indent(self):
        text = "Root\n    Child A\n    Child B"
        root = _parse_concept_tree_text(text)
        assert root is not None
        assert len(root.children) == 2
        assert root.children[0].label == "Child A"

    def test_multiple_root_level_items(self):
        text = "Problem\n  Sub A\nMethod\n  Component A"
        result = _parse_concept_tree_text(text)
        # Multiple depth-0 items → virtual root with 2 children
        assert result is not None
        assert len(result.children) == 2
        assert result.children[0].label == "Problem"
        assert result.children[1].label == "Method"

    def test_blank_lines_skipped(self):
        text = "Root\n\n  Child A\n\n  Child B\n"
        root = _parse_concept_tree_text(text)
        assert root is not None
        assert len(root.children) == 2

    def test_parse_decomp_response_includes_concept_tree(self):
        text = (
            "CORE_CONCEPT: A new method.\n"
            "CONCEPT_TREE:\n"
            "1. Problem\n"
            "2. Sub A\n"
            "IMPLEMENTATION_STEPS:\n"
            "1. Step one\n"
            "2. Step two\n"
            "ASSUMPTIONS:\n"
            "1. Assumes X\n"
            "LIMITATIONS:\n"
            "1. Limited to Y\n"
        )
        d = _parse_decomposition_response(text)
        assert d.concept_tree is not None
        assert isinstance(d.concept_tree, str)
        assert "Problem" in d.concept_tree


# ---------------------------------------------------------------------------
# _format_decomp_context
# ---------------------------------------------------------------------------

from open_idea_sourcing.novelty_evaluator import _format_decomp_context


class TestFormatDecompContext:
    def test_none_returns_placeholder(self):
        result = _format_decomp_context(None)
        assert "no decomposition" in result.lower()

    def test_includes_core_concept(self):
        d = IdeaDecomposition(core_concept="A dynamic attention mechanism.")
        result = _format_decomp_context(d)
        assert "dynamic attention" in result.lower()

    def test_includes_sub_ideas_when_no_tree(self):
        d = IdeaDecomposition(
            core_concept="Core with details.",
            concept_tree=None,
        )
        result = _format_decomp_context(d)
        assert "Core with details." in result

    def test_tree_preferred_over_sub_ideas(self):
        d = IdeaDecomposition(
            core_concept="Core.",
            concept_tree="1. Root\n2. Child",
        )
        result = _format_decomp_context(d)
        assert "Root" in result
        assert "Child" in result

    def test_includes_implementation_steps(self):
        d = IdeaDecomposition(
            core_concept="Core.",
            concept_tree="1. Plan\n2. Step 1\n3. Step 2",
        )
        result = _format_decomp_context(d)
        assert "Step 1" in result
        assert "Step 2" in result

    def test_empty_decomp_has_core_concept(self):
        d = IdeaDecomposition(core_concept="Just this.")
        result = _format_decomp_context(d)
        assert "Just this." in result


# ---------------------------------------------------------------------------
# NoveltyEvaluator decomposition_llm param
# ---------------------------------------------------------------------------

class TestDecompositionLlm:
    def test_decomposition_llm_used_for_decompose(self):
        """When decomposition_llm is set, it (not llm) is called for decomposition."""
        main_calls = []
        decomp_calls = []

        def main_llm(prompt: str) -> str:
            main_calls.append(prompt)
            return "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none"

        def decomp_llm(prompt: str) -> str:
            decomp_calls.append(prompt)
            return _DECOMP_RESPONSE

        evaluator = NoveltyEvaluator(llm=main_llm, decomposition_llm=decomp_llm)
        evaluator.evaluate(SAMPLE_PAPER)
        assert len(decomp_calls) == 1
        assert len(main_calls) == 5  # dup+combo+equiv+synth+domain_refs

    def test_fallback_to_main_llm_when_no_decomp_llm(self):
        calls = []
        def llm(prompt: str) -> str:
            calls.append(prompt)
            return "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none"
        evaluator = NoveltyEvaluator(llm=llm)
        evaluator.evaluate(SAMPLE_PAPER)
        # All 6 calls go through the same llm
        assert len(calls) == 6


# ---------------------------------------------------------------------------
# NoveltyEvaluator.decompose_idea() public method
# ---------------------------------------------------------------------------

class TestDecomposeIdeaPublicMethod:
    def test_returns_idea_decomposition(self):
        evaluator = NoveltyEvaluator(llm=lambda _: _DECOMP_RESPONSE)
        raw: dict = {}
        result = evaluator.decompose_idea(SAMPLE_PAPER, raw)
        assert isinstance(result, IdeaDecomposition)
        assert result.core_concept != ""

    def test_raw_stored(self):
        evaluator = NoveltyEvaluator(llm=lambda _: _DECOMP_RESPONSE)
        raw: dict = {}
        evaluator.decompose_idea(SAMPLE_PAPER, raw)
        assert "idea_decomposition" in raw

    def test_evaluate_skips_decomposition_when_passed(self):
        calls = []
        def llm(prompt: str) -> str:
            calls.append(prompt)
            return "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none"
        evaluator = NoveltyEvaluator(llm=llm)
        pre_decomp = IdeaDecomposition(core_concept="Pre-computed.")
        evaluator.evaluate(SAMPLE_PAPER, idea_decomposition=pre_decomp)
        # 5 calls: dup+combo+equiv+synth+domain_refs (decomp skipped)
        assert len(calls) == 5

    def test_decomp_fed_into_evaluate_shows_in_report(self):
        evaluator = NoveltyEvaluator(llm=lambda _: "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none")
        pre_decomp = IdeaDecomposition(core_concept="Pre-computed concept.")
        report = evaluator.evaluate(SAMPLE_PAPER, idea_decomposition=pre_decomp)
        assert report.idea_decomposition.core_concept == "Pre-computed concept."


# ---------------------------------------------------------------------------
# Helpers for evaluate_with_context tests
# ---------------------------------------------------------------------------

def _mock_llm_response(prompt: str) -> str:
    """Generic mock LLM that returns valid structured responses for all passes."""
    return (
        "VERDICT: LOW\n"
        "EXPLANATION: No significant overlap.\n"
        "REFERENCES: none\n"
        "OVERALL_VERDICT: NOVEL\n"
        "CONFIDENCE: HIGH\n"
        "SUMMARY: Paper is novel."
    )


# ---------------------------------------------------------------------------
# NoveltyEvaluator.evaluate_with_context()
# ---------------------------------------------------------------------------

class TestEvaluateWithContext:
    def test_evaluate_with_context_returns_novelty_report(self):
        """evaluate_with_context should return a NoveltyReport."""
        evaluator = NoveltyEvaluator(llm=_mock_llm_response)
        paper = ParsedPaper(title="Test", abstract="Test abstract.", full_text="Test full text.")
        ctx = PipelineContext(paper=paper, metadata=RunMetadata(model="test-model"))
        report = evaluator.evaluate_with_context(ctx)
        assert isinstance(report, NoveltyReport)
        assert report.paper_title == "Test"

    def test_evaluate_with_context_uses_precomputed_decomposition(self):
        """When ctx.idea_decomposition is set, the decomposition LLM call is skipped."""
        decomp_calls = []

        def llm(prompt: str) -> str:
            if "CORE_CONCEPT:" in prompt or "Decompose" in prompt:
                decomp_calls.append(prompt)
                return "CORE_CONCEPT: test\nASSUMPTIONS:\n1. none\nLIMITATIONS:\n1. none"
            return _mock_llm_response(prompt)

        evaluator = NoveltyEvaluator(llm=llm)
        paper = ParsedPaper(title="T", abstract="A", full_text="F")
        decomp = IdeaDecomposition(core_concept="pre-computed")
        ctx = PipelineContext(
            paper=paper,
            metadata=RunMetadata(model="test"),
            idea_decomposition=decomp,
        )
        report = evaluator.evaluate_with_context(ctx)
        assert report.idea_decomposition.core_concept == "pre-computed"
        assert len(decomp_calls) == 0

    def test_evaluate_with_context_writes_dimensions_to_ctx(self):
        """After evaluate_with_context, ctx.dimensions should have 3 entries."""
        evaluator = NoveltyEvaluator(llm=_mock_llm_response)
        paper = ParsedPaper(title="T", abstract="A", full_text="F")
        ctx = PipelineContext(paper=paper, metadata=RunMetadata(model="test"))
        evaluator.evaluate_with_context(ctx)
        assert len(ctx.dimensions) == 3  # duplication, combination, equivalence

    def test_evaluate_with_context_skips_domain_refs_when_precomputed(self):
        """Pre-populated ctx.domain_references suppresses the domain-refs LLM call."""
        calls = []

        def llm(prompt: str) -> str:
            calls.append(prompt)
            return _mock_llm_response(prompt)

        evaluator = NoveltyEvaluator(llm=llm)
        paper = ParsedPaper(title="T", abstract="A", full_text="F")
        pre_refs = [DomainReference(title="Pre-computed ref")]
        ctx = PipelineContext(
            paper=paper,
            metadata=RunMetadata(model="test"),
            domain_references=pre_refs,
        )
        evaluator.evaluate_with_context(ctx)
        # domain_refs call should not have been made
        assert ctx.domain_references[0].title == "Pre-computed ref"
        # Only decomp + dup + combo + equiv + synth = 5 calls (no domain refs)
        assert len(calls) == 5

    def test_evaluate_with_context_appends_jobs_to_metadata(self):
        """evaluate_with_context should add PipelineJob entries to ctx.metadata."""
        evaluator = NoveltyEvaluator(llm=_mock_llm_response)
        paper = ParsedPaper(title="T", abstract="A", full_text="F")
        metadata = RunMetadata(model="test")
        ctx = PipelineContext(paper=paper, metadata=metadata)
        evaluator.evaluate_with_context(ctx)
        assert len(ctx.metadata.jobs) > 0

    def test_pipeline_context_ref_sources_field(self):
        """PipelineContext should have a ref_sources dict field."""
        paper = ParsedPaper(title="T", abstract="A", full_text="F")
        ctx = PipelineContext(paper=paper, metadata=RunMetadata())
        assert isinstance(ctx.ref_sources, dict)
        ctx.ref_sources["paper123"] = "online"
        assert ctx.ref_sources["paper123"] == "online"

    def test_pipeline_context_stage_runtimes_field(self):
        """PipelineContext should have a stage_runtimes dict field."""
        paper = ParsedPaper(title="T", abstract="A", full_text="F")
        ctx = PipelineContext(paper=paper, metadata=RunMetadata())
        assert isinstance(ctx.stage_runtimes, dict)
        ctx.stage_runtimes["parsing"] = 0.5
        assert ctx.stage_runtimes["parsing"] == 0.5

    def test_pipeline_context_search_queries_and_online_papers(self):
        """PipelineContext should have search_queries list and online_papers list."""
        paper = ParsedPaper(title="T", abstract="A", full_text="F")
        ctx = PipelineContext(paper=paper, metadata=RunMetadata())
        assert isinstance(ctx.search_queries, list)
        assert isinstance(ctx.online_papers, list)
        ctx.search_queries.append("deep learning transformers")
        ctx.online_papers.append(object())
        assert len(ctx.search_queries) == 1
        assert len(ctx.online_papers) == 1


# ---------------------------------------------------------------------------
# Accumulated context in Stage 5 dimension chain
# ---------------------------------------------------------------------------

class TestAccumulatedStage5Context:
    """Stage 5 dimension checks pass prior verdicts as accumulated context."""

    def test_combination_receives_duplication_context(self):
        """combination prompt should include prior duplication verdict text."""
        prompts_seen = []

        def llm(prompt: str) -> str:
            prompts_seen.append(prompt)
            if "PRIOR ANALYSIS" in prompt and "Duplication" in prompt:
                return "VERDICT: LOW\nEXPLANATION: Not a combination.\nREFERENCES: none"
            if "direct duplicate" in prompt.lower() or "TASK: Determine whether the submitted paper is a direct duplicate" in prompt:
                return "VERDICT: HIGH\nEXPLANATION: Very similar to prior work.\nREFERENCES: REF-1"
            return _mock_llm_response(prompt)

        evaluator = NoveltyEvaluator(llm=llm)
        prior = NoveltyDimension(name="Direct Duplication", verdict="HIGH", explanation="Very similar to prior work.")
        result = evaluator._check_combination("paper", "refs", {}, prior_dup=prior)
        combo_prompts = [p for p in prompts_seen if "PRIOR ANALYSIS" in p and "Duplication" in p]
        assert len(combo_prompts) >= 1
        assert "HIGH" in combo_prompts[0]

    def test_equivalence_receives_both_prior_verdicts(self):
        """equivalence prompt should include both duplication and combination verdicts."""
        prompts_seen = []

        def llm(prompt: str) -> str:
            prompts_seen.append(prompt)
            return "VERDICT: LOW\nEXPLANATION: No equivalence.\nREFERENCES: none"

        evaluator = NoveltyEvaluator(llm=llm)
        prior_dup = NoveltyDimension(name="Direct Duplication", verdict="MEDIUM", explanation="Partially similar.")
        prior_combo = NoveltyDimension(name="Simple Combination", verdict="LOW", explanation="Not a simple combo.")
        evaluator._check_equivalence("paper", "refs", {}, prior_dup=prior_dup, prior_combo=prior_combo)

        equiv_prompts = [p for p in prompts_seen if "PRIOR ANALYSIS" in p]
        assert len(equiv_prompts) >= 1
        assert "MEDIUM" in equiv_prompts[0] or "Partially similar" in equiv_prompts[0]
        assert "LOW" in equiv_prompts[0] or "Not a simple combo" in equiv_prompts[0]

    def test_evaluate_chains_context_through_stages(self):
        """evaluate() should chain dup→combo→equiv with accumulated context."""
        prior_verdicts_in_combo = []
        prior_verdicts_in_equiv = []

        def llm(prompt: str) -> str:
            # Equivalence prompt uniquely contains "Combination Check" in its PRIOR ANALYSIS
            if "PRIOR ANALYSIS — Combination Check" in prompt:
                if "PRIOR ANALYSIS" in prompt:
                    prior_verdicts_in_equiv.append(prompt)
                return "VERDICT: LOW\nEXPLANATION: No equivalence.\nREFERENCES: none"
            # Combination prompt uniquely contains "Duplication Check" but NOT "Combination Check"
            if "PRIOR ANALYSIS — Duplication Check" in prompt:
                if "PRIOR ANALYSIS" in prompt:
                    prior_verdicts_in_combo.append(prompt)
                return "VERDICT: MEDIUM\nEXPLANATION: Partly assembled.\nREFERENCES: REF-1"
            return _mock_llm_response(prompt)

        evaluator = NoveltyEvaluator(llm=llm)
        paper = ParsedPaper(title="T", abstract="A", full_text="F")
        report = evaluator.evaluate(paper)
        # Combo prompt should contain the dup verdict; equiv should contain both priors
        assert len(prior_verdicts_in_combo) >= 1, "combination prompt should include duplication prior"
        assert len(prior_verdicts_in_equiv) >= 1, "equivalence prompt should include prior analyses"

    def test_no_prior_context_when_not_provided(self):
        """When prior_dup is None, combination prompt should still work."""
        evaluator = NoveltyEvaluator(llm=lambda p: "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none")
        result = evaluator._check_combination("paper", "refs", {})
        assert result.verdict == "LOW"

    def test_no_prior_context_equivalence(self):
        """When no priors, equivalence prompt should still work."""
        evaluator = NoveltyEvaluator(llm=lambda p: "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none")
        result = evaluator._check_equivalence("paper", "refs", {})
        assert result.verdict == "LOW"
