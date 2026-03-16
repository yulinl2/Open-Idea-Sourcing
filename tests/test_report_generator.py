"""Tests for open_idea_sourcing.report_generator."""

import json
from datetime import datetime
import pytest

from open_idea_sourcing.novelty_evaluator import (
    NoveltyDimension,
    NoveltyReport,
    PipelineJob,
    RunMetadata,
)
from open_idea_sourcing.reference_store import ReferencePaper
from open_idea_sourcing.report_generator import ReportGenerator, suggest_filename
from open_idea_sourcing.similarity_search import SimilarityResult


def _sample_report(verdict: str = "NOT_NOVEL") -> NoveltyReport:
    return NoveltyReport(
        paper_title="A Test Paper",
        overall_verdict=verdict,
        confidence="HIGH",
        summary="The paper duplicates prior attention work.",
        dimensions=[
            NoveltyDimension(
                name="Direct Duplication",
                verdict="HIGH",
                explanation="Essentially the same as att2017.",
                references=["att2017"],
            ),
            NoveltyDimension(
                name="Simple Combination",
                verdict="MEDIUM",
                explanation="Combines two known methods.",
                references=["p1", "p2"],
            ),
            NoveltyDimension(
                name="Methodological Equivalence",
                verdict="LOW",
                explanation="No equivalence found.",
                references=[],
            ),
        ],
        similar_papers=[
            SimilarityResult(
                paper=ReferencePaper(
                    id="att2017",
                    title="Attention Is All You Need",
                    abstract="Transformer paper.",
                    year=2017,
                ),
                score=0.92,
            )
        ],
    )


class TestReportGeneratorText:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report()

    def test_generates_text_output(self):
        out = self.gen.generate(self.report, fmt="text")
        assert isinstance(out, str)
        assert len(out) > 0

    def test_text_contains_title(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "A Test Paper" in out

    def test_text_contains_verdict(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "NOT_NOVEL" in out

    def test_text_contains_summary(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "attention work" in out

    def test_text_contains_dimension_names(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "DIRECT DUPLICATION" in out
        assert "SIMPLE COMBINATION" in out
        assert "METHODOLOGICAL EQUIVALENCE" in out

    def test_text_contains_similar_paper(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "Attention Is All You Need" in out

    def test_default_format_is_text(self):
        out_default = self.gen.generate(self.report)
        out_text = self.gen.generate(self.report, fmt="text")
        assert out_default == out_text


class TestReportGeneratorMarkdown:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report()

    def test_generates_markdown_output(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "# Novelty Evaluation" in out

    def test_markdown_contains_verdict_emoji(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "❌" in out  # NOT_NOVEL

    def test_markdown_novel_shows_check(self):
        out = self.gen.generate(_sample_report("NOVEL"), fmt="markdown")
        assert "✅" in out

    def test_markdown_marginal_shows_warning(self):
        out = self.gen.generate(_sample_report("MARGINAL"), fmt="markdown")
        assert "⚠️" in out

    def test_markdown_contains_table_for_similar_papers(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "| Score |" in out
        assert "0.92" in out

    def test_markdown_references_formatted(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "`att2017`" in out

    def test_markdown_no_similar_papers_skips_table(self):
        report = _sample_report()
        report.similar_papers = []
        out = self.gen.generate(report, fmt="markdown")
        assert "| Score |" not in out


class TestReportGeneratorJSON:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report()

    def test_generates_valid_json(self):
        out = self.gen.generate(self.report, fmt="json")
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_json_has_required_keys(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "paper_title" in data
        assert "overall_verdict" in data
        assert "confidence" in data
        assert "summary" in data
        assert "dimensions" in data
        assert "similar_papers" in data

    def test_json_dimensions_count(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert len(data["dimensions"]) == 3

    def test_json_similar_papers_count(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert len(data["similar_papers"]) == 1
        assert data["similar_papers"][0]["score"] == pytest.approx(0.92)

    def test_json_verdict(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert data["overall_verdict"] == "NOT_NOVEL"

    def test_json_dimension_structure(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        dim = data["dimensions"][0]
        assert "name" in dim
        assert "verdict" in dim
        assert "explanation" in dim
        assert "references" in dim


# ---------------------------------------------------------------------------
# suggest_filename
# ---------------------------------------------------------------------------

class TestSuggestFilename:
    def test_markdown_extension(self):
        assert suggest_filename("My Paper", "markdown").endswith(".md")

    def test_text_extension(self):
        assert suggest_filename("My Paper", "text").endswith(".txt")

    def test_json_extension(self):
        assert suggest_filename("My Paper", "json").endswith(".json")

    def test_slugifies_title(self):
        name = suggest_filename("Attention Is All You Need", "markdown")
        assert name == "attention-is-all-you-need.md"

    def test_strips_special_chars(self):
        name = suggest_filename("BERT: Pre-training of Deep Transformers", "json")
        assert ":" not in name
        assert name.endswith(".json")

    def test_truncates_long_title(self):
        long_title = "A" * 100
        name = suggest_filename(long_title, "markdown")
        # slug is 80 chars + ".md"
        assert len(name) <= 84

    def test_empty_title_fallback(self):
        name = suggest_filename("", "markdown")
        assert name == "novelty-report.md"

    def test_no_report_prefix(self):
        name = suggest_filename("Some Interesting Paper", "markdown")
        assert not name.startswith("report")


# ---------------------------------------------------------------------------
# RunMetadata and PipelineJob dataclasses
# ---------------------------------------------------------------------------

def _make_metadata() -> RunMetadata:
    t0 = datetime(2024, 1, 15, 12, 0, 0)
    t1 = datetime(2024, 1, 15, 12, 0, 3)
    t2 = datetime(2024, 1, 15, 12, 0, 5)
    t3 = datetime(2024, 1, 15, 12, 0, 20)
    return RunMetadata(
        started_at=t0,
        model_name="gpt-4o",
        paper_source="paper.pdf",
        finished_at=t3,
        jobs=[
            PipelineJob(
                name="Parse paper",
                agent="PaperParser",
                started_at=t0,
                finished_at=t1,
                input_summary="paper.pdf",
                output_summary='"A Test Paper", 1234 chars',
            ),
            PipelineJob(
                name="Duplication check",
                agent="LLM (gpt-4o)",
                started_at=t1,
                finished_at=t2,
                input_summary="paper content + 1 reference paper(s)",
                output_summary="verdict=HIGH",
            ),
            PipelineJob(
                name="Synthesis",
                agent="LLM (gpt-4o)",
                started_at=t2,
                finished_at=t3,
                input_summary="3 dimension results",
                output_summary="verdict=NOT_NOVEL, confidence=HIGH",
            ),
        ],
    )


def _sample_report_with_metadata(verdict: str = "NOT_NOVEL") -> NoveltyReport:
    report = _sample_report(verdict)
    report.metadata = _make_metadata()
    return report


class TestPipelineJob:
    def test_duration_s(self):
        t0 = datetime(2024, 1, 1, 0, 0, 0)
        t1 = datetime(2024, 1, 1, 0, 0, 5)
        job = PipelineJob(
            name="Test",
            agent="Agent",
            started_at=t0,
            finished_at=t1,
            input_summary="in",
            output_summary="out",
        )
        assert job.duration_s == pytest.approx(5.0)


class TestRunMetadata:
    def test_jobs_list(self):
        meta = _make_metadata()
        assert len(meta.jobs) == 3

    def test_finished_at_set(self):
        meta = _make_metadata()
        assert meta.finished_at is not None

    def test_total_duration(self):
        meta = _make_metadata()
        total = (meta.finished_at - meta.started_at).total_seconds()
        assert total == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# Metadata in text output
# ---------------------------------------------------------------------------

class TestTextWithMetadata:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_with_metadata()

    def test_text_contains_model_name(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "gpt-4o" in out

    def test_text_contains_paper_source(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "paper.pdf" in out

    def test_text_contains_pipeline_log(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "PIPELINE JOB LOG" in out

    def test_text_contains_job_names(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "Parse paper" in out
        assert "Synthesis" in out

    def test_text_without_metadata_unchanged(self):
        """Report without metadata must not contain the metadata header."""
        report = _sample_report()
        out = self.gen.generate(report, fmt="text")
        assert "RUN METADATA" not in out
        assert "PIPELINE JOB LOG" not in out


# ---------------------------------------------------------------------------
# Metadata in markdown output
# ---------------------------------------------------------------------------

class TestMarkdownWithMetadata:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_with_metadata()

    def test_markdown_contains_metadata_section(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "## Run Metadata" in out

    def test_markdown_contains_model_name(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "gpt-4o" in out

    def test_markdown_contains_pipeline_log_section(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "## Pipeline Job Log" in out

    def test_markdown_contains_gantt_diagram(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "```mermaid" in out
        assert "gantt" in out

    def test_markdown_gantt_contains_job_names(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "Parse paper" in out
        assert "Synthesis" in out

    def test_markdown_without_metadata_no_gantt(self):
        report = _sample_report()
        out = self.gen.generate(report, fmt="markdown")
        assert "```mermaid" not in out
        assert "## Run Metadata" not in out


# ---------------------------------------------------------------------------
# Metadata in JSON output
# ---------------------------------------------------------------------------

class TestJSONWithMetadata:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_with_metadata()

    def test_json_has_metadata_key(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "metadata" in data

    def test_json_metadata_has_required_fields(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        meta = data["metadata"]
        assert "model_name" in meta
        assert "paper_source" in meta
        assert "started_at" in meta
        assert "finished_at" in meta
        assert "total_duration_s" in meta
        assert "jobs" in meta

    def test_json_metadata_model_name(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert data["metadata"]["model_name"] == "gpt-4o"

    def test_json_metadata_jobs_count(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert len(data["metadata"]["jobs"]) == 3

    def test_json_metadata_job_structure(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        job = data["metadata"]["jobs"][0]
        assert "name" in job
        assert "agent" in job
        assert "started_at" in job
        assert "finished_at" in job
        assert "duration_s" in job
        assert "input_summary" in job
        assert "output_summary" in job

    def test_json_without_metadata_no_metadata_key(self):
        report = _sample_report()
        data = json.loads(self.gen.generate(report, fmt="json"))
        assert "metadata" not in data
