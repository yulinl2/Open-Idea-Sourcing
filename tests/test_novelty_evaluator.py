"""Tests for open_idea_sourcing.novelty_evaluator."""

import pytest

from open_idea_sourcing.novelty_evaluator import (
    NoveltyDimension,
    NoveltyEvaluator,
    NoveltyReport,
    _extract_field,
    _parse_dimension_response,
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
_RECON_RESPONSE = (
    "VERDICT: HIGH\n"
    "EXPLANATION: The contribution is the expected next step from the problem "
    "setup; an expert would readily reconstruct it from existing literature.\n"
    "REFERENCES: att2017"
)
_SYNTH_RESPONSE = (
    "OVERALL_VERDICT: NOT_NOVEL\n"
    "CONFIDENCE: HIGH\n"
    "SUMMARY: The paper is largely a duplicate of prior attention work."
)


def _make_full_llm():
    """LLM that returns appropriate canned responses for each pass."""
    responses_in_order = [
        _DUP_RESPONSE,
        _COMBO_RESPONSE,
        _EQUIV_RESPONSE,
        _RECON_RESPONSE,
        _SYNTH_RESPONSE,
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

    def test_report_has_four_dimensions(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert len(report.dimensions) == 4

    def test_dimension_names(self):
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        names = {d.name for d in report.dimensions}
        assert "Direct Duplication" in names
        assert "Simple Combination" in names
        assert "Methodological Equivalence" in names
        assert "Intellectual Contribution (Reconstruction Test)" in names

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
        assert "reconstruction" in report.raw_llm_responses
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

    def test_llm_called_exactly_five_times(self):
        calls = []
        def counting_llm(prompt: str) -> str:
            calls.append(prompt)
            return "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none"

        evaluator = NoveltyEvaluator(llm=counting_llm)
        evaluator.evaluate(SAMPLE_PAPER)
        # 4 dimension passes + 1 synthesis pass
        assert len(calls) == 5

    def test_duplication_high_leads_to_not_novel(self):
        """When duplication is HIGH, synthesis should reflect that."""
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER, similar_papers=self._make_similar())
        # Our canned synthesis says NOT_NOVEL
        assert report.overall_verdict == "NOT_NOVEL"

    def test_format_references_empty(self):
        text = NoveltyEvaluator._format_references([])
        assert "No reference papers provided" in text

    def test_format_references_shows_title(self):
        similar = [SimilarityResult(paper=SAMPLE_REFERENCE, score=0.9)]
        text = NoveltyEvaluator._format_references(similar)
        assert "Attention Is All You Need" in text
        assert "0.90" in text


# ---------------------------------------------------------------------------
# NoveltyEvaluator.evaluate() with metadata (job log)
# ---------------------------------------------------------------------------

class TestNoveltyEvaluatorJobLog:
    def _make_metadata(self) -> "RunMetadata":
        from open_idea_sourcing.novelty_evaluator import RunMetadata
        return RunMetadata(model="gpt-test", input_source="paper.txt")

    def test_evaluate_with_metadata_appends_five_jobs(self):
        meta = self._make_metadata()
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        evaluator.evaluate(SAMPLE_PAPER, metadata=meta)
        # 4 LLM dimension jobs + 1 synthesis job
        assert len(meta.jobs) == 5

    def test_evaluate_job_names(self):
        meta = self._make_metadata()
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        evaluator.evaluate(SAMPLE_PAPER, metadata=meta)
        names = [j.name for j in meta.jobs]
        assert "Duplication check" in names
        assert "Combination check" in names
        assert "Equivalence check" in names
        assert "Reconstruction check" in names
        assert "Synthesis" in names

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
        # 1 pre-existing + 5 from evaluator = 6
        assert len(meta.jobs) == 6
        assert meta.jobs[0].name == "Parse paper"


# ---------------------------------------------------------------------------
# Tests for the reconstruction dimension (_check_reconstruction)
# ---------------------------------------------------------------------------

class TestReconstructionDimension:
    """Tests for the min-hint max-recovery reconstruction analysis pass."""

    def test_reconstruction_dimension_in_report(self):
        """Reconstruction dimension must appear in the report's dimensions list."""
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        names = [d.name for d in report.dimensions]
        assert "Intellectual Contribution (Reconstruction Test)" in names

    def test_reconstruction_verdict_stored_in_raw(self):
        """Raw LLM response for the reconstruction pass must be stored."""
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        assert "reconstruction" in report.raw_llm_responses

    def test_reconstruction_high_verdict_parsed(self):
        """A HIGH reconstruction verdict is correctly parsed from the LLM response."""
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        recon_dim = next(
            d for d in report.dimensions
            if d.name == "Intellectual Contribution (Reconstruction Test)"
        )
        assert recon_dim.verdict == "HIGH"

    def test_reconstruction_explanation_not_empty(self):
        """Reconstruction explanation must be non-empty."""
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER)
        recon_dim = next(
            d for d in report.dimensions
            if d.name == "Intellectual Contribution (Reconstruction Test)"
        )
        assert recon_dim.explanation.strip() != ""

    def test_reconstruction_references_parsed(self):
        """References cited in the reconstruction response must be parsed."""
        evaluator = NoveltyEvaluator(llm=_make_full_llm())
        report = evaluator.evaluate(SAMPLE_PAPER, similar_papers=[
            SimilarityResult(paper=SAMPLE_REFERENCE, score=0.85)
        ])
        recon_dim = next(
            d for d in report.dimensions
            if d.name == "Intellectual Contribution (Reconstruction Test)"
        )
        assert "att2017" in recon_dim.references

    def test_reconstruction_low_verdict_for_novel_paper(self):
        """A LOW reconstruction verdict (non-obvious contribution) is correctly handled."""
        low_recon_response = (
            "VERDICT: LOW\n"
            "EXPLANATION: The contribution is a surprising non-obvious insight "
            "that could not be reconstructed from the problem setup alone.\n"
            "REFERENCES: none"
        )
        responses = [
            _DUP_RESPONSE, _COMBO_RESPONSE, _EQUIV_RESPONSE,
            low_recon_response, _SYNTH_RESPONSE,
        ]
        call_idx = {"i": 0}

        def sequential_llm(_prompt: str) -> str:
            idx = call_idx["i"]
            call_idx["i"] += 1
            if idx < len(responses):
                return responses[idx]
            return "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none"

        evaluator = NoveltyEvaluator(llm=sequential_llm)
        report = evaluator.evaluate(SAMPLE_PAPER)
        recon_dim = next(
            d for d in report.dimensions
            if d.name == "Intellectual Contribution (Reconstruction Test)"
        )
        assert recon_dim.verdict == "LOW"

    def test_reconstruction_prompt_contains_min_hint_keywords(self):
        """The reconstruction prompt must include the test's key framing."""
        captured_prompts = []

        def capture_llm(prompt: str) -> str:
            captured_prompts.append(prompt)
            return "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none"

        evaluator = NoveltyEvaluator(llm=capture_llm)
        evaluator.evaluate(SAMPLE_PAPER)
        # The 4th call (index 3) is the reconstruction pass
        recon_prompt = captured_prompts[3]
        assert "reconstruct" in recon_prompt.lower()
        assert "expert" in recon_prompt.lower()

    def test_reconstruction_synthesis_includes_reconstruction_result(self):
        """The synthesis prompt must include the reconstruction analysis."""
        captured_prompts = []

        def capture_llm(prompt: str) -> str:
            captured_prompts.append(prompt)
            return "VERDICT: LOW\nEXPLANATION: ok\nREFERENCES: none"

        evaluator = NoveltyEvaluator(llm=capture_llm)
        evaluator.evaluate(SAMPLE_PAPER)
        # The 5th call (index 4) is the synthesis pass
        synth_prompt = captured_prompts[4]
        assert "reconstruction" in synth_prompt.lower()
