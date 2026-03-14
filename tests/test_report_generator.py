"""Tests for open_idea_sourcing.report_generator."""

import json
import pytest

from open_idea_sourcing.novelty_evaluator import NoveltyDimension, NoveltyReport
from open_idea_sourcing.reference_store import ReferencePaper
from open_idea_sourcing.report_generator import ReportGenerator
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
