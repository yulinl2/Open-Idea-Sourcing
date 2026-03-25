"""Tests for open_idea_sourcing.report_generator."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from open_idea_sourcing.novelty_evaluator import NoveltyDimension, NoveltyReport, RunMetadata
from open_idea_sourcing.reference_store import ReferencePaper
from open_idea_sourcing.report_generator import ReportGenerator, suggest_filename, _fmt_datetime_ny
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
        assert m.git_branch == ""
        assert m.git_commit == ""
        assert m.git_commit_url == ""
        assert m.ci_run_url == ""
        assert m.pr_number == ""

    def test_all_fields_set(self):
        m = _sample_metadata()
        assert m.model == "gpt-4o"
        assert m.input_source == "my_paper.pdf"
        assert m.timestamp == "2024-06-01T12:00:00Z"
        assert m.total_runtime_seconds == pytest.approx(15.3)
        assert m.stage_runtimes["parsing"] == pytest.approx(0.4)
        assert m.code_version == "1.0.0"

    def test_git_fields(self):
        m = RunMetadata(
            git_branch="main",
            git_commit="abc1234",
            git_commit_url="https://github.com/org/repo/commit/abc1234def",
            ci_run_url="https://github.com/org/repo/actions/runs/42",
        )
        assert m.git_branch == "main"
        assert m.git_commit == "abc1234"
        assert "abc1234def" in m.git_commit_url
        assert "runs/42" in m.ci_run_url

    def test_pr_number_default_empty(self):
        m = RunMetadata()
        assert m.pr_number == ""

    def test_pr_number_set(self):
        m = RunMetadata(pr_number="42")
        assert m.pr_number == "42"


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

    def test_filename_does_not_have_novelty_report_prefix(self):
        name = suggest_filename(self.report, "markdown")
        assert not name.startswith("novelty_report_")
        # Title should be the first component
        assert name.startswith("A_Test_Paper")

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
        raw_ts = "2024-06-01T12:00:00Z"
        assert _fmt_datetime_ny(raw_ts) in out or raw_ts in out

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
        raw_ts = "2024-06-01T12:00:00Z"
        assert _fmt_datetime_ny(raw_ts) in out or raw_ts in out

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

    def test_markdown_job_log_before_verdict(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert out.index("## Pipeline Job Log") < out.index("**Overall verdict:**")

    def test_markdown_metadata_before_job_log(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert out.index("## Run Metadata") < out.index("## Pipeline Job Log")

    def test_text_metadata_before_paper_line(self):
        out = self.gen.generate(self.report, fmt="text")
        assert out.index("RUN METADATA") < out.index("Paper  :")

    def test_text_job_log_before_paper_line(self):
        out = self.gen.generate(self.report, fmt="text")
        assert out.index("PIPELINE JOB LOG") < out.index("Paper  :")


class TestMetadataGitContext:
    """Verify that git/CI context fields appear in the rendered reports."""

    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report()
        self.report.metadata = RunMetadata(
            model="gpt-4o",
            input_source="my_paper.pdf",
            timestamp="2024-06-01T12:00:00Z",
            total_runtime_seconds=15.3,
            stage_runtimes={"parsing": 0.4},
            code_version="1.0.0",
            git_branch="feat/my-branch",
            git_commit="abc1234",
            git_commit_url="https://github.com/org/repo/commit/abc1234def",
            ci_run_url="https://github.com/org/repo/actions/runs/42",
            pr_number="19",
        )

    def test_markdown_contains_branch(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "feat/my-branch" in out

    def test_markdown_contains_commit_link(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "abc1234" in out
        assert "abc1234def" in out

    def test_markdown_commit_is_hyperlink(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "[`abc1234`](https://github.com/org/repo/commit/abc1234def)" in out

    def test_markdown_contains_ci_run_link(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "runs/42" in out

    def test_markdown_ci_run_is_hyperlink(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "Run #42" in out
        assert "https://github.com/org/repo/actions/runs/42" in out

    def test_text_contains_branch(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "feat/my-branch" in out

    def test_text_contains_commit(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "abc1234" in out

    def test_text_contains_ci_run_url(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "runs/42" in out

    def test_text_grouped_metadata_sections(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "[Run Context]" in out
        assert "[Configuration]" in out
        assert "[Performance]" in out

    def test_json_contains_git_fields(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert data["metadata"]["git_branch"] == "feat/my-branch"
        assert data["metadata"]["git_commit"] == "abc1234"
        assert "abc1234def" in data["metadata"]["git_commit_url"]
        assert "runs/42" in data["metadata"]["ci_run_url"]

    def test_markdown_commit_without_url_shows_code_span(self):
        self.report.metadata.git_commit_url = ""
        out = self.gen.generate(self.report, fmt="markdown")
        assert "`abc1234`" in out

    def test_markdown_omits_ci_run_when_empty(self):
        self.report.metadata.ci_run_url = ""
        out = self.gen.generate(self.report, fmt="markdown")
        assert "CI Run" not in out

    def test_markdown_contains_pr_number_as_link(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "#19" in out
        assert "/pull/19" in out

    def test_markdown_omits_pr_when_empty(self):
        self.report.metadata.pr_number = ""
        out = self.gen.generate(self.report, fmt="markdown")
        assert "| PR |" not in out

    def test_text_contains_pr_number(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "#19" in out

    def test_text_omits_pr_when_empty(self):
        self.report.metadata.pr_number = ""
        out = self.gen.generate(self.report, fmt="text")
        assert "PR          :" not in out

    def test_json_contains_pr_number(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert data["metadata"]["pr_number"] == "19"


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

    def test_markdown_job_table_escapes_pipe_in_job_name(self):
        """Pipe chars in job name, input_summary, output_summary must be escaped."""
        report = _sample_report_with_jobs()
        report.metadata.jobs[0].name = "Parse | paper"
        report.metadata.jobs[0].input_summary = "file | path"
        report.metadata.jobs[0].output_summary = "title | subtitle"
        out = self.gen.generate(report, fmt="markdown")
        assert r"Parse \| paper" in out
        assert r"file \| path" in out
        assert r"title \| subtitle" in out


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


# ---------------------------------------------------------------------------
# Idea Decomposition rendering
# ---------------------------------------------------------------------------

from open_idea_sourcing.novelty_evaluator import IdeaDecomposition, DomainReference, ConceptNode
from open_idea_sourcing.report_generator import _render_concept_tree_ascii, _concept_node_to_dict


def _sample_concept_tree() -> "ConceptNode":
    return ConceptNode(
        label="Dynamic Masking Transformer",
        children=[
            ConceptNode(
                label="Attention Module",
                children=[
                    ConceptNode(label="Dynamic masking layer"),
                    ConceptNode(label="Softmax attention"),
                ],
            ),
            ConceptNode(
                label="Integration Layer",
                children=[
                    ConceptNode(label="Standard Transformer blocks"),
                ],
            ),
        ],
    )


def _sample_decomposition() -> IdeaDecomposition:
    return IdeaDecomposition(
        core_concept="A dynamic masking extension of Transformer attention.",
        sub_ideas=["Dynamic attention masking", "Standard Transformer integration"],
        assumptions=["Uniform tokenisation"],
        limitations=["Evaluated on NLP benchmarks only"],
        concept_tree=_sample_concept_tree(),
        implementation_steps=[
            "Implement dynamic masking module",
            "Integrate with standard Transformer architecture",
            "Evaluate on NLP benchmarks",
        ],
    )


def _sample_domain_refs() -> list[DomainReference]:
    return [
        DomainReference(
            title="Attention Is All You Need",
            authors="Vaswani et al.",
            year="2017",
            relevance="Foundational Transformer work",
        ),
        DomainReference(
            title="BERT",
            authors="Devlin et al.",
            year="2018",
            relevance="Pre-training with masked attention",
        ),
    ]


def _sample_report_enriched() -> NoveltyReport:
    report = _sample_report()
    report.idea_decomposition = _sample_decomposition()
    report.domain_references = _sample_domain_refs()
    return report


class TestIdeaDecompositionInText:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_enriched()

    def test_text_contains_idea_decomposition_section(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "IDEA DECOMPOSITION" in out

    def test_text_contains_core_concept(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "dynamic masking" in out.lower()

    def test_text_contains_concept_tree(self):
        out = self.gen.generate(self.report, fmt="text")
        # ASCII tree connectors should appear
        assert "├──" in out or "└──" in out

    def test_text_concept_tree_root_label(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "Dynamic Masking Transformer" in out

    def test_text_concept_tree_child_label(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "Attention Module" in out

    def test_text_contains_assumptions(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "Uniform tokenisation" in out

    def test_text_contains_limitations(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "NLP benchmarks" in out

    def test_text_contains_implementation_roadmap(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "Implementation roadmap:" in out
        assert "Implement dynamic masking module" in out

    def test_text_implementation_steps_ordered(self):
        out = self.gen.generate(self.report, fmt="text")
        # All three steps should appear
        assert "Integrate with standard Transformer architecture" in out
        assert "Evaluate on NLP benchmarks" in out

    def test_text_no_decomposition_section_when_none(self):
        report = _sample_report()
        out = self.gen.generate(report, fmt="text")
        assert "IDEA DECOMPOSITION" not in out

    def test_text_idea_decomposition_before_verdict(self):
        out = self.gen.generate(self.report, fmt="text")
        assert out.index("IDEA DECOMPOSITION") < out.index("Paper  :")


class TestIdeaDecompositionInMarkdown:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_enriched()

    def test_markdown_contains_idea_decomposition_section(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "## Idea Decomposition" in out

    def test_markdown_contains_core_concept(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "dynamic masking" in out.lower()

    def test_markdown_contains_concept_tree_section(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "### Concept Tree" in out

    def test_markdown_concept_tree_in_code_block(self):
        out = self.gen.generate(self.report, fmt="markdown")
        # Concept tree is wrapped in a ``` code block
        assert "```" in out
        assert "├──" in out or "└──" in out

    def test_markdown_concept_tree_root_label(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "Dynamic Masking Transformer" in out

    def test_markdown_concept_tree_child_nodes(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "Attention Module" in out
        assert "Integration Layer" in out

    def test_markdown_contains_sub_ideas_list(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "- Dynamic attention masking" in out

    def test_markdown_contains_assumptions_list(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "- Uniform tokenisation" in out

    def test_markdown_contains_limitations_list(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "- Evaluated on NLP benchmarks only" in out

    def test_markdown_contains_implementation_roadmap(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "**Implementation Roadmap:**" in out
        assert "Implement dynamic masking module" in out

    def test_markdown_implementation_steps_numbered(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "1. Implement dynamic masking module" in out
        assert "2. Integrate with standard Transformer architecture" in out

    def test_markdown_no_decomposition_when_none(self):
        report = _sample_report()
        out = self.gen.generate(report, fmt="markdown")
        assert "## Idea Decomposition" not in out

    def test_markdown_no_concept_tree_section_when_no_tree(self):
        report = _sample_report()
        report.idea_decomposition = IdeaDecomposition(
            core_concept="Simple.",
            sub_ideas=["A"],
        )
        out = self.gen.generate(report, fmt="markdown")
        assert "### Concept Tree" not in out

    def test_markdown_no_mermaid_mindmap(self):
        """Mermaid mindmap should NOT appear — replaced by ASCII concept tree."""
        out = self.gen.generate(self.report, fmt="markdown")
        assert "mindmap" not in out
        assert "root((" not in out

    def test_markdown_idea_decomposition_before_verdict(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert out.index("## Idea Decomposition") < out.index("**Overall verdict:**")


class TestConceptTreeInMarkdown:
    """Tests for the ASCII concept tree rendered in the Markdown report."""

    def setup_method(self):
        self.gen = ReportGenerator()

    def test_concept_tree_hidden_when_no_decomposition(self):
        report = _sample_report()
        out = self.gen.generate(report, fmt="markdown")
        assert "### Concept Tree" not in out

    def test_concept_tree_hidden_when_concept_tree_is_none(self):
        report = _sample_report()
        report.idea_decomposition = IdeaDecomposition(
            core_concept="Core concept only.",
            sub_ideas=["A"],
        )
        out = self.gen.generate(report, fmt="markdown")
        assert "### Concept Tree" not in out

    def test_concept_tree_shown_when_present(self):
        report = _sample_report()
        report.idea_decomposition = IdeaDecomposition(
            core_concept="Core",
            concept_tree=ConceptNode(
                label="Root",
                children=[ConceptNode(label="Child")],
            ),
        )
        out = self.gen.generate(report, fmt="markdown")
        assert "### Concept Tree" in out

    def test_concept_tree_root_in_output(self):
        report = _sample_report()
        report.idea_decomposition = IdeaDecomposition(
            core_concept="Core",
            concept_tree=ConceptNode(
                label="My Root Node",
                children=[ConceptNode(label="Child")],
            ),
        )
        out = self.gen.generate(report, fmt="markdown")
        assert "My Root Node" in out

    def test_concept_tree_leaf_connector(self):
        report = _sample_report()
        report.idea_decomposition = IdeaDecomposition(
            core_concept="Core",
            concept_tree=ConceptNode(
                label="Root",
                children=[ConceptNode(label="Only Child")],
            ),
        )
        out = self.gen.generate(report, fmt="markdown")
        assert "└── Only Child" in out

    def test_concept_tree_branch_connector(self):
        report = _sample_report()
        report.idea_decomposition = IdeaDecomposition(
            core_concept="Core",
            concept_tree=ConceptNode(
                label="Root",
                children=[
                    ConceptNode(label="First"),
                    ConceptNode(label="Last"),
                ],
            ),
        )
        out = self.gen.generate(report, fmt="markdown")
        assert "├── First" in out
        assert "└── Last" in out


# ---------------------------------------------------------------------------
# _render_concept_tree_ascii unit tests
# ---------------------------------------------------------------------------

class TestRenderConceptTreeAscii:
    def test_root_only_no_connectors(self):
        root = ConceptNode(label="Root")
        result = _render_concept_tree_ascii(root)
        assert result == "Root"

    def test_single_child_uses_last_connector(self):
        root = ConceptNode(label="Root", children=[ConceptNode(label="Child")])
        result = _render_concept_tree_ascii(root)
        assert "└── Child" in result

    def test_two_children_connectors(self):
        root = ConceptNode(
            label="Root",
            children=[ConceptNode(label="A"), ConceptNode(label="B")],
        )
        result = _render_concept_tree_ascii(root)
        assert "├── A" in result
        assert "└── B" in result

    def test_nested_children_continuation_line(self):
        root = ConceptNode(
            label="Root",
            children=[
                ConceptNode(
                    label="A",
                    children=[ConceptNode(label="A1"), ConceptNode(label="A2")],
                ),
                ConceptNode(label="B"),
            ],
        )
        result = _render_concept_tree_ascii(root)
        # A is not the last child → "│   " prefix for its grandchildren
        assert "│   ├── A1" in result
        assert "│   └── A2" in result

    def test_last_child_uses_spaces_not_pipe(self):
        root = ConceptNode(
            label="Root",
            children=[
                ConceptNode(label="A"),
                ConceptNode(
                    label="B",
                    children=[ConceptNode(label="B1")],
                ),
            ],
        )
        result = _render_concept_tree_ascii(root)
        # B is the last child → "    " prefix (spaces, not │)
        assert "    └── B1" in result

    def test_root_label_on_first_line(self):
        root = ConceptNode(
            label="My Root",
            children=[ConceptNode(label="Child")],
        )
        lines = _render_concept_tree_ascii(root).splitlines()
        assert lines[0] == "My Root"

    def test_returns_string(self):
        result = _render_concept_tree_ascii(ConceptNode(label="X"))
        assert isinstance(result, str)

    def test_full_example(self):
        root = ConceptNode(
            label="Dynamic Masking Transformer",
            children=[
                ConceptNode(
                    label="Attention Module",
                    children=[
                        ConceptNode(label="Dynamic masking layer"),
                        ConceptNode(label="Softmax attention"),
                    ],
                ),
                ConceptNode(
                    label="Integration Layer",
                    children=[ConceptNode(label="Standard Transformer blocks")],
                ),
            ],
        )
        result = _render_concept_tree_ascii(root)
        assert result.startswith("Dynamic Masking Transformer")
        assert "├── Attention Module" in result
        assert "│   ├── Dynamic masking layer" in result
        assert "│   └── Softmax attention" in result
        assert "└── Integration Layer" in result
        assert "    └── Standard Transformer blocks" in result


# ---------------------------------------------------------------------------
# _concept_node_to_dict unit tests
# ---------------------------------------------------------------------------

class TestConceptNodeToDict:
    def test_leaf_no_children_key(self):
        result = _concept_node_to_dict(ConceptNode(label="Leaf"))
        assert result == {"label": "Leaf"}
        assert "children" not in result

    def test_node_with_children_has_children_key(self):
        root = ConceptNode(label="Root", children=[ConceptNode(label="Child")])
        result = _concept_node_to_dict(root)
        assert "children" in result
        assert len(result["children"]) == 1
        assert result["children"][0]["label"] == "Child"

    def test_nested_structure(self):
        root = ConceptNode(
            label="Root",
            children=[
                ConceptNode(
                    label="A",
                    children=[ConceptNode(label="A1")],
                ),
            ],
        )
        result = _concept_node_to_dict(root)
        assert result["children"][0]["children"][0]["label"] == "A1"


class TestDomainReferencesInText:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_enriched()

    def test_text_contains_domain_references_section(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "MAIN DOMAIN REFERENCES" in out

    def test_text_contains_reference_titles(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "Attention Is All You Need" in out
        assert "BERT" in out

    def test_text_contains_reference_years(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "2017" in out
        assert "2018" in out

    def test_text_contains_relevance(self):
        out = self.gen.generate(self.report, fmt="text")
        assert "Transformer" in out

    def test_text_no_domain_refs_section_when_empty(self):
        report = _sample_report()
        out = self.gen.generate(report, fmt="text")
        assert "MAIN DOMAIN REFERENCES" not in out


class TestDomainReferencesInMarkdown:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_enriched()

    def test_markdown_contains_domain_references_section(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "## Main Domain References" in out

    def test_markdown_domain_refs_use_numbered_list_format(self):
        """Domain references are rendered as a numbered bold-title list, not a table."""
        out = self.gen.generate(self.report, fmt="markdown")
        # The section should have numbered bold entries (not a | … | table)
        assert "1. **" in out

    def test_markdown_contains_reference_titles(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "Attention Is All You Need" in out
        assert "BERT" in out

    def test_markdown_no_domain_refs_when_empty(self):
        report = _sample_report()
        out = self.gen.generate(report, fmt="markdown")
        assert "## Main Domain References" not in out


class TestEnrichedFieldsInJSON:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_enriched()

    def test_json_contains_idea_decomposition(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "idea_decomposition" in data

    def test_json_idea_decomposition_fields(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        d = data["idea_decomposition"]
        assert "core_concept" in d
        assert "sub_ideas" in d
        assert "assumptions" in d
        assert "limitations" in d

    def test_json_idea_decomposition_sub_ideas_are_list(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert isinstance(data["idea_decomposition"]["sub_ideas"], list)

    def test_json_contains_domain_references(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "domain_references" in data

    def test_json_domain_references_count(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert len(data["domain_references"]) == 2

    def test_json_domain_reference_fields(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        ref = data["domain_references"][0]
        assert "title" in ref
        assert "authors" in ref
        assert "year" in ref
        assert "relevance" in ref

    def test_json_no_idea_decomposition_when_none(self):
        report = _sample_report()
        data = json.loads(self.gen.generate(report, fmt="json"))
        assert "idea_decomposition" not in data

    def test_json_no_domain_references_when_empty(self):
        report = _sample_report()
        data = json.loads(self.gen.generate(report, fmt="json"))
        assert "domain_references" not in data


# ---------------------------------------------------------------------------
# Collapsible analysis sections
# ---------------------------------------------------------------------------

class TestCollapsibleAnalysisSections:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report()

    def test_markdown_dimensions_wrapped_in_details(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "<details>" in out
        assert "</details>" in out

    def test_markdown_summary_shows_risk_level(self):
        out = self.gen.generate(self.report, fmt="markdown")
        # Each dimension should have a <summary> line with "Risk level:"
        assert "<summary>" in out
        assert "Risk level:" in out

    def test_markdown_explanation_inside_details(self):
        out = self.gen.generate(self.report, fmt="markdown")
        # Explanation text must appear between <details> and </details>
        details_start = out.index("<details>")
        details_end = out.index("</details>")
        section = out[details_start:details_end]
        assert "Essentially the same as att2017" in section

    def test_markdown_each_dimension_has_own_details_block(self):
        out = self.gen.generate(self.report, fmt="markdown")
        # 3 dimensions → 3 <details> blocks
        assert out.count("<details>") >= 3
        assert out.count("</details>") >= 3


# ---------------------------------------------------------------------------
# Paper metainfo block
# ---------------------------------------------------------------------------

class TestPaperMetainfoBlock:
    def setup_method(self):
        self.gen = ReportGenerator()

    def test_markdown_shows_source_url_as_link(self):
        """Source URL is no longer shown in a blockquote — it lives in the
        Run Metadata Configuration table under the 'Input' field."""
        report = _sample_report()
        report.metadata = _sample_metadata()
        report.metadata.input_source = "https://arxiv.org/abs/1234.5678"
        out = self.gen.generate(report, fmt="markdown")
        # Source is shown in the Configuration table, not as a blockquote.
        assert "**Source:**" not in out
        assert "https://arxiv.org/abs/1234.5678" in out

    def test_markdown_shows_file_source_as_code(self):
        """File source is surfaced in the Configuration table, not a blockquote."""
        report = _sample_report()
        report.metadata = _sample_metadata()
        report.metadata.input_source = "my_paper.pdf"
        out = self.gen.generate(report, fmt="markdown")
        assert "**Source:**" not in out
        assert "my_paper.pdf" in out

    def test_markdown_no_source_block_when_no_metadata(self):
        report = _sample_report()
        out = self.gen.generate(report, fmt="markdown")
        assert "**Source:**" not in out

    def test_markdown_no_source_block_when_empty_input_source(self):
        report = _sample_report()
        report.metadata = _sample_metadata()
        report.metadata.input_source = ""
        out = self.gen.generate(report, fmt="markdown")
        assert "**Source:**" not in out


# ---------------------------------------------------------------------------
# Pipeline job table grouping by agent
# ---------------------------------------------------------------------------

class TestPipelineJobTableGrouping:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_with_jobs()

    def test_markdown_table_grouped_with_bold_agent_headers(self):
        out = self.gen.generate(self.report, fmt="markdown")
        # Bold section headers for each distinct agent group
        assert "**PaperParser**" in out
        assert "**LLM (gpt-4o)**" in out

    def test_markdown_agent_header_before_its_jobs(self):
        out = self.gen.generate(self.report, fmt="markdown")
        # Bold section headers must appear before their respective sub-tables.
        # We look within the Pipeline Job Log section (after "## Pipeline Job Log").
        log_pos = out.index("## Pipeline Job Log")
        log_section = out[log_pos:]
        parser_pos = log_section.index("**PaperParser**")
        llm_pos = log_section.index("**LLM (gpt-4o)**")
        # PaperParser header must come before LLM header
        assert parser_pos < llm_pos

    def test_markdown_no_agent_column_in_table(self):
        out = self.gen.generate(self.report, fmt="markdown")
        # The job-detail table header should NOT include an Agent column (it's
        # already shown as the bold group header).
        lines = out.splitlines()
        table_header = next(
            (l for l in lines if "| Job |" in l), None
        )
        assert table_header is not None
        assert "Agent" not in table_header


# ---------------------------------------------------------------------------
# JSON enriched fields — concept_tree and implementation_steps
# ---------------------------------------------------------------------------

class TestEnrichedFieldsInJSONV2:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_enriched()

    def test_json_idea_decomposition_has_implementation_steps(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "implementation_steps" in data["idea_decomposition"]

    def test_json_implementation_steps_is_list(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert isinstance(data["idea_decomposition"]["implementation_steps"], list)

    def test_json_implementation_steps_content(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        steps = data["idea_decomposition"]["implementation_steps"]
        assert len(steps) == 3
        assert "dynamic masking" in steps[0].lower()

    def test_json_idea_decomposition_has_concept_tree(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "concept_tree" in data["idea_decomposition"]

    def test_json_concept_tree_has_label(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        tree = data["idea_decomposition"]["concept_tree"]
        assert "label" in tree
        assert tree["label"] == "Dynamic Masking Transformer"

    def test_json_concept_tree_has_children(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        tree = data["idea_decomposition"]["concept_tree"]
        assert "children" in tree
        assert len(tree["children"]) == 2

    def test_json_concept_tree_nested_children(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        tree = data["idea_decomposition"]["concept_tree"]
        first_child = tree["children"][0]
        assert "children" in first_child
        assert len(first_child["children"]) == 2

    def test_json_no_concept_tree_key_when_tree_is_none(self):
        report = _sample_report()
        report.idea_decomposition = IdeaDecomposition(
            core_concept="Core.", sub_ideas=["A"]
        )
        data = json.loads(self.gen.generate(report, fmt="json"))
        assert "concept_tree" not in data["idea_decomposition"]


# ---------------------------------------------------------------------------
# Similarity annotations in Markdown and JSON
# ---------------------------------------------------------------------------

from open_idea_sourcing.novelty_evaluator import SimilarityAnnotation


def _sample_report_with_annotations() -> NoveltyReport:
    """Sample report that has similar papers AND annotations."""
    report = _sample_report()
    # Give the existing similar paper a URL
    report.similar_papers[0].paper.url = "https://arxiv.org/abs/1706.03762"
    report.similar_paper_annotations = [
        SimilarityAnnotation(
            paper_id="att2017",
            overlap="Both use self-attention as core mechanism.",
            differences="Submitted paper adds dynamic masking; original is static.",
            derivation="The multi-head attention design is directly derived from Vaswani et al.",
        )
    ]
    return report


class TestSimilarPaperAnnotationsInMarkdown:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_with_annotations()

    def test_markdown_shows_reference_annotations_section(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "### Reference Annotations" in out

    def test_markdown_annotations_use_comparison_table(self):
        out = self.gen.generate(self.report, fmt="markdown")
        # Annotations now render as inline comparison tables, not <details> blocks.
        ann_pos = out.index("### Reference Annotations")
        section = out[ann_pos:]
        assert "| Dimension | Notes |" in section
        assert "**Overlap**" in section
        assert "**Differences**" in section

    def test_markdown_shows_overlap(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "Both use self-attention" in out

    def test_markdown_shows_differences(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "dynamic masking" in out

    def test_markdown_shows_derivation(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "multi-head attention design" in out

    def test_markdown_similar_paper_has_url_link(self):
        out = self.gen.generate(self.report, fmt="markdown")
        assert "https://arxiv.org/abs/1706.03762" in out

    def test_markdown_no_annotations_section_when_empty(self):
        report = _sample_report()  # no annotations
        out = self.gen.generate(report, fmt="markdown")
        assert "### Reference Annotations" not in out


class TestSimilarPaperAnnotationsInJSON:
    def setup_method(self):
        self.gen = ReportGenerator()
        self.report = _sample_report_with_annotations()

    def test_json_similar_paper_has_url(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert data["similar_papers"][0]["url"] == "https://arxiv.org/abs/1706.03762"

    def test_json_similar_paper_has_overlap(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "overlap" in data["similar_papers"][0]
        assert "self-attention" in data["similar_papers"][0]["overlap"]

    def test_json_similar_paper_has_differences(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "differences" in data["similar_papers"][0]

    def test_json_similar_paper_has_derivation(self):
        data = json.loads(self.gen.generate(self.report, fmt="json"))
        assert "derivation" in data["similar_papers"][0]

    def test_json_similar_paper_no_annotations_when_none(self):
        report = _sample_report()  # no annotations
        data = json.loads(self.gen.generate(report, fmt="json"))
        p = data["similar_papers"][0]
        assert "overlap" not in p
        assert "differences" not in p
        assert "derivation" not in p

