"""
tests/test_infra.py

Unit tests for the agent-track shared infra package.

Run with:
    pytest tests/test_infra.py -v

These tests require no API keys — they exercise the pure-Python infra layer only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from infra.run_context import RunContext
from infra.report_writer import (
    DerivationEntry,
    PriorWorkEntry,
    ReportContent,
    ReportWriter,
)
from infra.tool_registry import ToolRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent


def _make_context(**kwargs) -> RunContext:
    defaults = dict(
        track="e2e",
        impl_id="e2e_v1_0_0",
        paper_id="2006.06138",
        paper_source="https://arxiv.org/abs/2006.06138",
        model="gpt-4o",
    )
    defaults.update(kwargs)
    return RunContext(**defaults)


def _make_content(ctx: RunContext | None = None) -> ReportContent:
    if ctx is None:
        ctx = _make_context()
    ctx.final_verdict = "COMBINATION"
    ctx.confidence = 0.75
    ctx.main_cited_evidence = ["arxiv-2001.00001", "arxiv-2001.00002"]
    ctx.mark_finished()
    return ReportContent(
        context=ctx,
        executive_summary="The paper combines two known methods.",
        decomposition=[
            {"unit": "attention mechanism", "source": "prior work"},
        ],
        prior_work=[
            PriorWorkEntry(
                paper_id="arxiv-1706.03762",
                title="Attention Is All You Need",
                year=2017,
                relevance_note="Core attention formulation.",
                derivation_note="Paper uses scaled dot-product attention directly.",
            )
        ],
        derivation_map=[
            DerivationEntry(
                component="scaled dot-product attention",
                source_paper="arxiv-1706.03762",
                source_detail="Section 3.2",
                derivation_type="DUPLICATE",
                confidence=0.9,
            )
        ],
        residual_novelty="The integration of covariate-shift weighting is new.",
        uncertainties=["Section 4 of the target paper was unavailable."],
        tool_call_log=[{"tool": "web_search", "query": "attention mechanism prior work"}],
        search_queries=["attention mechanism prior work"],
    )


# ---------------------------------------------------------------------------
# RunContext
# ---------------------------------------------------------------------------


class TestRunContext:
    def test_fields_default_populated(self):
        ctx = _make_context()
        assert ctx.track == "e2e"
        assert ctx.impl_id == "e2e_v1_0_0"
        assert ctx.paper_id == "2006.06138"
        assert ctx.start_time  # non-empty
        assert ctx.git_commit  # non-empty

    def test_mark_finished_sets_finish_time(self):
        ctx = _make_context()
        assert ctx.finish_time == ""
        ctx.mark_finished()
        assert ctx.finish_time != ""

    def test_record_tool_deduplicates(self):
        ctx = _make_context()
        ctx.record_tool("web_search")
        ctx.record_tool("web_search")
        ctx.record_tool("fetch_paper_text")
        assert ctx.tool_list == ["web_search", "fetch_paper_text"]

    def test_yaml_front_matter_contains_required_fields(self):
        ctx = _make_context()
        ctx.final_verdict = "NOVEL"
        ctx.confidence = 0.8
        ctx.main_cited_evidence = ["ev1"]
        ctx.mark_finished()
        ctx.record_tool("web_search")
        fm = ctx.to_yaml_front_matter()
        for field in (
            "track:", "impl_id:", "paper_id:", "paper_source:", "model:",
            "tool_list:", "start_time:", "finish_time:", "git_commit:",
            "final_verdict:", "confidence:", "main_cited_evidence:",
        ):
            assert field in fm, f"Missing field {field!r} in YAML front matter"

    def test_yaml_front_matter_valid_delimiters(self):
        ctx = _make_context()
        ctx.mark_finished()
        fm = ctx.to_yaml_front_matter()
        assert fm.startswith("---\n")
        assert fm.endswith("\n---")

    def test_yaml_front_matter_single_quotes_strings(self):
        ctx = _make_context(paper_source="https://arxiv.org/abs/2006.06138")
        ctx.mark_finished()
        fm = ctx.to_yaml_front_matter()
        assert "'https://arxiv.org/abs/2006.06138'" in fm

    def test_from_dict_roundtrip(self):
        ctx = _make_context()
        ctx.final_verdict = "COMBINATION"
        ctx.confidence = 0.72
        ctx.main_cited_evidence = ["arxiv-1706.03762"]
        ctx.mark_finished()
        ctx.record_tool("web_search")
        # Build a dict from the YAML-like fields (simulate deserialization)
        data = {
            "track": ctx.track,
            "impl_id": ctx.impl_id,
            "paper_id": ctx.paper_id,
            "paper_source": ctx.paper_source,
            "model": ctx.model,
            "response_id": ctx.response_id,
            "tool_list": ctx.tool_list,
            "start_time": ctx.start_time,
            "finish_time": ctx.finish_time,
            "git_commit": ctx.git_commit,
            "final_verdict": ctx.final_verdict,
            "confidence": ctx.confidence,
            "main_cited_evidence": ctx.main_cited_evidence,
        }
        restored = RunContext.from_dict(data)
        assert restored.track == ctx.track
        assert restored.impl_id == ctx.impl_id
        assert restored.final_verdict == ctx.final_verdict
        assert abs(restored.confidence - ctx.confidence) < 1e-9
        assert restored.tool_list == ctx.tool_list

    def test_confidence_clamped(self):
        ctx = RunContext.from_dict({"track": "e2e", "impl_id": "x", "paper_id": "1",
                                    "paper_source": "", "model": "gpt-4o",
                                    "confidence": 1.5})
        assert ctx.confidence == 1.0
        ctx2 = RunContext.from_dict({"track": "e2e", "impl_id": "x", "paper_id": "1",
                                     "paper_source": "", "model": "gpt-4o",
                                     "confidence": -0.1})
        assert ctx2.confidence == 0.0


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------


class TestToolRegistry:
    def _make_reg(self) -> ToolRegistry:
        ctx = _make_context()
        return ToolRegistry(ctx)

    def test_register_and_call(self):
        reg = self._make_reg()
        reg.register("double", lambda x: x * 2)
        result = reg.call("double", x=5)
        assert result == 10

    def test_call_logs_tool(self):
        reg = self._make_reg()
        reg.register("noop", lambda: None)
        reg.call("noop")
        log = reg.tool_call_log()
        assert len(log) == 1
        assert log[0]["tool"] == "noop"

    def test_empty_log(self):
        reg = self._make_reg()
        assert reg.tool_call_log() == []

    def test_call_unknown_tool_raises(self):
        reg = self._make_reg()
        with pytest.raises(KeyError):
            reg.call("unknown_tool")

    def test_registered_names(self):
        reg = self._make_reg()
        reg.register("alpha", lambda: None)
        reg.register("beta", lambda: None)
        assert set(reg.registered_names()) == {"alpha", "beta"}


# ---------------------------------------------------------------------------
# ReportWriter
# ---------------------------------------------------------------------------


class TestReportWriter:
    def test_write_creates_file(self, tmp_path):
        content = _make_content()
        out = tmp_path / "report.md"
        writer = ReportWriter(output_path=out)
        result = writer.write(content)
        assert result == out
        assert out.exists()

    def test_report_contains_required_sections(self, tmp_path):
        content = _make_content()
        out = tmp_path / "report.md"
        writer = ReportWriter(output_path=out)
        writer.write(content)
        text = out.read_text()
        required_sections = [
            "Executive Summary",
            "Final Verdict",
            "Technical Contribution Decomposition",
            "Strongest Prior-Work Evidence",
            "Derivation Map",
            "Residual Novelty",
            "Uncertainties",
            "Audit Appendix",
        ]
        for section in required_sections:
            assert section in text, f"Missing section: {section!r}"

    def test_report_has_yaml_front_matter(self, tmp_path):
        content = _make_content()
        out = tmp_path / "report.md"
        ReportWriter(output_path=out).write(content)
        text = out.read_text()
        assert text.startswith("---\n")
        # Second '---' terminates the front matter
        assert "\n---\n" in text

    def test_report_has_table_of_contents(self, tmp_path):
        content = _make_content()
        out = tmp_path / "report.md"
        ReportWriter(output_path=out).write(content)
        text = out.read_text()
        assert "Table of Contents" in text or "Contents" in text

    def test_derivation_map_in_report(self, tmp_path):
        content = _make_content()
        out = tmp_path / "report.md"
        ReportWriter(output_path=out).write(content)
        text = out.read_text()
        assert "scaled dot-product attention" in text

    def test_prior_work_in_report(self, tmp_path):
        content = _make_content()
        out = tmp_path / "report.md"
        ReportWriter(output_path=out).write(content)
        text = out.read_text()
        assert "Attention Is All You Need" in text

    def test_verdict_emoji_in_report(self, tmp_path):
        content = _make_content()
        out = tmp_path / "report.md"
        ReportWriter(output_path=out).write(content)
        text = out.read_text()
        # COMBINATION verdict should appear with emoji
        assert "COMBINATION" in text


# ---------------------------------------------------------------------------
# Data files (ported from main)
# ---------------------------------------------------------------------------


class TestDataFiles:
    def test_test_papers_ndjson_exists(self):
        path = ROOT / "data" / "test_papers.ndjson"
        assert path.exists(), "data/test_papers.ndjson missing"

    def test_test_papers_ndjson_valid(self):
        path = ROOT / "data" / "test_papers.ndjson"
        papers = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        assert len(papers) >= 1, "test_papers.ndjson must contain at least one paper"
        for paper in papers:
            assert "url" in paper, f"Paper entry missing 'url': {paper}"
            assert paper["url"].startswith("https://"), f"Paper URL must be https: {paper['url']}"

    def test_references_json_exists(self):
        path = ROOT / "data" / "references.json"
        assert path.exists(), "data/references.json missing"

    def test_references_json_valid(self):
        path = ROOT / "data" / "references.json"
        refs = json.loads(path.read_text())
        assert isinstance(refs, list), "references.json must be a JSON array"
        for ref in refs:
            assert "id" in ref, f"Reference entry missing 'id': {ref}"
            assert "title" in ref, f"Reference entry missing 'title': {ref}"

    def test_arxiv_id_in_test_papers(self):
        path = ROOT / "data" / "test_papers.ndjson"
        papers = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        arxiv_pattern = re.compile(r"arxiv\.org/(abs|pdf)/\d{4}\.\d+")
        assert any(arxiv_pattern.search(p["url"]) for p in papers), \
            "At least one test paper should be an arXiv paper"


# ---------------------------------------------------------------------------
# Smoke test: full infra import
# ---------------------------------------------------------------------------


class TestInfraImports:
    def test_all_public_symbols_importable(self):
        from infra import (  # noqa: F401
            RunContext,
            ReportContent,
            ReportWriter,
            DerivationEntry,
            PriorWorkEntry,
            ToolRegistry,
            search_semantic_scholar,
            fetch_s2_citations,
            fetch_s2_paper,
            search_arxiv,
            extract_text_from_pdf,
        )

    def test_smoke_run(self):
        ctx = RunContext(
            track="smoke",
            impl_id="smoke_v0",
            paper_id="test",
            paper_source="local",
            model="stub",
        )
        ctx.record_tool("smoke_tool")
        ctx.mark_finished()
        fm = ctx.to_yaml_front_matter()
        assert "track:" in fm
        assert "smoke_tool" in fm


# ---------------------------------------------------------------------------
# Agent CLI smoke tests (no API key; just verify imports and arg-parsing)
# ---------------------------------------------------------------------------


class TestAgentCliSmoke:
    """Smoke tests for agent implementations — exercised by CI test-infra job.

    These tests verify that each track's agent module imports correctly and
    accepts --help without errors. No API key is required.
    """

    def _agent_path(self, track: str) -> Path:
        # Works whether running from infra-base or an agent branch
        candidates = [
            ROOT / "agent_impls" / track / "agent.py",  # infra-base layout
            ROOT / "agent.py",  # agent branch layout
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def test_agent_e2e_help(self):
        path = self._agent_path("e2e")
        if path is None:
            pytest.skip("agent-e2e agent.py not found")
        import subprocess
        result = subprocess.run(
            ["python", str(path), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"--help failed:\n{result.stderr}"
        assert "--paper-url" in result.stdout

    def test_agent_linear_help(self):
        path = self._agent_path("linear")
        if path is None:
            pytest.skip("agent-linear agent.py not found")
        import subprocess
        result = subprocess.run(
            ["python", str(path), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"--help failed:\n{result.stderr}"
        assert "--paper-url" in result.stdout
        assert "--from-stage" in result.stdout

    def test_agent_reconstruct_help(self):
        path = self._agent_path("reconstruct")
        if path is None:
            pytest.skip("agent-reconstruct agent.py not found")
        import subprocess
        result = subprocess.run(
            ["python", str(path), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"--help failed:\n{result.stderr}"
        assert "--paper-url" in result.stdout
        assert "--refs" in result.stdout

    def test_infra_smoke_from_agent_branch(self):
        """Replicate the inline CI smoke test to ensure it passes."""
        from infra import RunContext, ReportContent, ReportWriter, ToolRegistry
        from infra.run_context import RunContext as RC
        ctx = RC(track="smoke", impl_id="smoke_v0", paper_id="test",
                 paper_source="local", model="stub")
        ctx.record_tool("smoke_tool")
        ctx.mark_finished()
        fm = ctx.to_yaml_front_matter()
        assert "track:" in fm, "YAML front matter missing track"
        assert "smoke_tool" in fm, "YAML front matter missing tool"
