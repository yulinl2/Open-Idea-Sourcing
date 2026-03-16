"""Tests for open_idea_sourcing.report_generator."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from open_idea_sourcing.novelty_evaluator import NoveltyDimension, NoveltyReport, RunMetadata
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


def _sample_metadata() -> RunMetadata:
    return RunMetadata(
        model="gpt-4o",
        input_source="my_paper.pdf",
        timestamp="2024-06-01T12:00:00Z",
        total_runtime_seconds=15.3,
        stage_runtimes={"parsing": 0.4, "similarity": 0.1, "evaluation": 14.8},
        code_version="1.0.0",
    )


class TestRunMetadata:
    def test_default_fields(self):
        m = RunMetadata()
        assert m.model == ""
        assert m.input_source == ""
        assert m.timestamp == ""
        assert m.total_runtime_seconds == 0.0
        assert m.stage_runtimes == {}
        assert m.code_version == ""

    def test_all_fields_set(self):
        m = _sample_metadata()
        assert m.model == "gpt-4o"
        assert m.input_source == "my_paper.pdf"
        assert m.timestamp == "2024-06-01T12:00:00Z"
        assert m.total_runtime_seconds == pytest.approx(15.3)
        assert m.stage_runtimes["parsing"] == pytest.approx(0.4)
        assert m.code_version == "1.0.0"


class TestSuggestFilename:
    def setup_method(self):
        self.report = _sample_report()

    def test_default_format_extension_is_md(self):
        assert suggest_filename(self.report, "markdown").endswith(".md")

    def test_text_format_extension(self):
        assert suggest_filename(self.report, "text").endswith(".txt")

    def test_json_format_extension(self):
        assert suggest_filename(self.report, "json").endswith(".json")

    def test_pdf_format_extension(self):
        assert suggest_filename(self.report, "pdf").endswith(".pdf")

    def test_filename_contains_paper_title(self):
        name = suggest_filename(self.report, "markdown")
        assert "A_Test_Paper" in name

    def test_filename_contains_timestamp_when_present(self):
        self.report.metadata = _sample_metadata()
        name = suggest_filename(self.report, "markdown")
        assert "2024-06-01" in name

    def test_filename_contains_time_component_when_present(self):
        self.report.metadata = _sample_metadata()
        name = suggest_filename(self.report, "markdown")
        # Full datetime (no colons) so same-day re-runs produce distinct names.
        assert "2024-06-01T120000" in name

    def test_filename_falls_back_gracefully_for_malformed_timestamp(self):
        self.report.metadata = RunMetadata(timestamp="not-a-date")
        name = suggest_filename(self.report, "markdown")
        # Should not raise; falls back to the first 10 chars as-is.
        assert "not-a-date" in name

    def test_filename_omits_timestamp_when_no_metadata(self):
        name = suggest_filename(self.report, "markdown")
        # No metadata => no date segment
        assert "2024" not in name

    def test_filename_starts_with_novelty_report(self):
        name = suggest_filename(self.report, "markdown")
        assert name.startswith("novelty_report_")

    def test_special_characters_sanitised(self):
        self.report.paper_title = "Paper: A & B (2024)!"
        name = suggest_filename(self.report, "markdown")
        assert ":" not in name
        assert "&" not in name
        assert "!" not in name


class TestReportGeneratorMetadataInText:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report()
        self.report.metadata = _sample_metadata()

    def test_text_contains_model(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "gpt-4o" in out

    def test_text_contains_input_source(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "my_paper.pdf" in out

    def test_text_contains_timestamp(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "2024-06-01T12:00:00Z" in out

    def test_text_contains_total_runtime(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "15.3s" in out

    def test_text_contains_stage_runtimes(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "parsing" in out
        assert "evaluation" in out

    def test_text_contains_code_version(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "1.0.0" in out

    def test_text_no_metadata_section_when_none(self):
        report = _sample_report()
        out = self.gen.generate(report, fmt="text")
        assert "RUN METADATA" not in out


class TestReportGeneratorMetadataInMarkdown:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report()
        self.report.metadata = _sample_metadata()

    def test_markdown_contains_metadata_section(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "## Run Metadata" in out

    def test_markdown_contains_model(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "gpt-4o" in out

    def test_markdown_contains_input_source(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "my_paper.pdf" in out

    def test_markdown_contains_timestamp(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "2024-06-01T12:00:00Z" in out

    def test_markdown_contains_total_runtime(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "15.3s" in out

    def test_markdown_contains_code_version(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "1.0.0" in out

    def test_markdown_no_metadata_section_when_none(self):
        report = _sample_report()
        out = self.gen.generate(report, fmt="markdown")
        assert "## Run Metadata" not in out

    def test_pdf_format_returns_markdown_string(self):
        """generate() with fmt='pdf' must return markdown (not raise)."""
        out = self.gen.generate(self.report, fmt="pdf")
        assert "# Novelty Evaluation" in out


class TestReportGeneratorMetadataInJSON:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report()
        self.report.metadata = _sample_metadata()

    def test_json_contains_metadata_key(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "metadata" in data

    def test_json_metadata_model(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert data["metadata"]["model"] == "gpt-4o"

    def test_json_metadata_input_source(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert data["metadata"]["input_source"] == "my_paper.pdf"

    def test_json_metadata_timestamp(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert data["metadata"]["timestamp"] == "2024-06-01T12:00:00Z"

    def test_json_metadata_total_runtime(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert data["metadata"]["total_runtime_seconds"] == pytest.approx(15.3)

    def test_json_metadata_stage_runtimes(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        runtimes = data["metadata"]["stage_runtimes"]
        assert "parsing" in runtimes
        assert "evaluation" in runtimes

    def test_json_metadata_code_version(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert data["metadata"]["code_version"] == "1.0.0"

    def test_json_no_metadata_key_when_none(self):
        report = _sample_report()
        data = json.loads(self.gen.generate(report, fmt="json"))
        assert "metadata" not in data


class TestGeneratePdf:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report()
        self.report.metadata = _sample_metadata()

    def test_generate_pdf_creates_file(self, tmp_path):
        pytest.importorskip("markdown")
        pytest.importorskip("weasyprint")
        out = tmp_path / "report.pdf"
        self.gen.generate_pdf(self.report, out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_generate_pdf_raises_without_markdown(self, tmp_path, monkeypatch):
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "markdown":
                raise ImportError("no markdown")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        with pytest.raises(RuntimeError, match="markdown"):
            self.gen.generate_pdf(self.report, tmp_path / "report.pdf")

    def test_generate_pdf_raises_without_weasyprint(self, tmp_path, monkeypatch):
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "weasyprint":
                raise ImportError("no weasyprint")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        # markdown must be importable for this test
        pytest.importorskip("markdown")
        with pytest.raises(RuntimeError, match="weasyprint"):
            self.gen.generate_pdf(self.report, tmp_path / "report.pdf")


# ---------------------------------------------------------------------------
# PipelineJob dataclass
# ---------------------------------------------------------------------------

from open_idea_sourcing.novelty_evaluator import PipelineJob


def _sample_jobs() -> list[PipelineJob]:
    return [
        PipelineJob(
            name="Parse paper",
            agent="PaperParser",
            offset_s=0.0,
            duration_s=0.4,
            input_summary="paper.pdf",
            output_summary='"A Test Paper", 2000 chars',
        ),
        PipelineJob(
            name="Duplication check",
            agent="LLM (gpt-4o)",
            offset_s=0.5,
            duration_s=5.2,
            input_summary="paper content + 2 reference paper(s)",
            output_summary="verdict=HIGH",
        ),
        PipelineJob(
            name="Synthesis",
            agent="LLM (gpt-4o)",
            offset_s=16.1,
            duration_s=4.8,
            input_summary="3 dimension results",
            output_summary="verdict=NOT_NOVEL, confidence=HIGH",
        ),
    ]


def _sample_report_with_jobs(verdict: str = "NOT_NOVEL") -> NoveltyReport:
    report = _sample_report(verdict)
    report.metadata = _sample_metadata()
    report.metadata.jobs = _sample_jobs()
    return report


class TestPipelineJob:
    def test_fields_stored(self):
        job = PipelineJob(
            name="Test", agent="Agent", offset_s=1.5, duration_s=3.0,
            input_summary="in", output_summary="out",
        )
        assert job.name == "Test"
        assert job.agent == "Agent"
        assert job.offset_s == 1.5
        assert job.duration_s == 3.0
        assert job.input_summary == "in"
        assert job.output_summary == "out"


class TestMetadataOnTop:
    """Verify that metadata appears BEFORE the main report body in all formats."""

    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_with_jobs()

    def test_markdown_metadata_before_verdict(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert out.index("## Run Metadata") < out.index("**Overall verdict:**")

    def test_text_metadata_before_paper_line(self):
        out = self.gen.generate(self.report, fmt="text")
        assert out.index("RUN METADATA") < out.index("Paper  :")


class TestPipelineJobLogInMarkdown:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_with_jobs()

    def test_markdown_contains_pipeline_log_section(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "## Pipeline Job Log" in out

    def test_markdown_contains_gantt_diagram(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "```mermaid" in out
        assert "gantt" in out

    def test_gantt_contains_job_names(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "Parse paper" in out
        assert "Synthesis" in out

    def test_gantt_has_sections_by_agent(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "section PaperParser" in out
        assert "section LLM (gpt-4o)" in out

    def test_markdown_job_table_contains_agents(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "PaperParser" in out
        assert "LLM (gpt-4o)" in out

    def test_markdown_no_pipeline_log_without_jobs(self):
        report = _sample_report()
        report.metadata = _sample_metadata()
        out = self.gen.generate(report, fmt="markdown")
        assert "## Pipeline Job Log" not in out
        assert "```mermaid" not in out


class TestPipelineJobLogInText:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_with_jobs()

    def test_text_contains_pipeline_job_log(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "PIPELINE JOB LOG" in out

    def test_text_contains_job_names(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "Parse paper" in out
        assert "Synthesis" in out

    def test_text_no_pipeline_log_without_jobs(self):
        report = _sample_report()
        report.metadata = _sample_metadata()
        out = self.gen.generate(report, fmt="text")
        assert "PIPELINE JOB LOG" not in out


class TestPipelineJobsInJSON:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_with_jobs()

    def test_json_metadata_has_jobs_key(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "jobs" in data["metadata"]

    def test_json_jobs_count(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert len(data["metadata"]["jobs"]) == 3

    def test_json_job_fields(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        job = data["metadata"]["jobs"][0]
        assert "name" in job
        assert "agent" in job
        assert "offset_s" in job
        assert "duration_s" in job
        assert "input_summary" in job
        assert "output_summary" in job

    def test_json_no_jobs_key_when_no_jobs(self):
        report = _sample_report()
        report.metadata = _sample_metadata()
        data = json.loads(self.gen.generate(report, fmt="json"))
        assert data["metadata"]["jobs"] == []
