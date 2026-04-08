"""Unit tests for the staged-reconstruct pipeline.

No API keys needed — exercises data loading, prompt templating, audit logging,
and output structure.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import asdict

import pytest

ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Data files (cherry-picked from main)
# ---------------------------------------------------------------------------


class TestDataFiles:
    def test_test_papers_ndjson_exists(self):
        path = ROOT / "data" / "test_papers.ndjson"
        assert path.exists()

    def test_test_papers_valid(self):
        path = ROOT / "data" / "test_papers.ndjson"
        papers = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        assert len(papers) >= 1
        for p in papers:
            assert "url" in p
            assert p["url"].startswith("https://")

    def test_references_json_exists(self):
        path = ROOT / "data" / "references.json"
        assert path.exists()

    def test_references_json_valid(self):
        path = ROOT / "data" / "references.json"
        refs = json.loads(path.read_text())
        assert isinstance(refs, list)
        assert len(refs) >= 1
        for ref in refs:
            assert "id" in ref
            assert "title" in ref
            assert "abstract" in ref


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------


class TestPrompts:
    EXPECTED_PROMPTS = [
        "teacher_extract.txt",
        "student_abstract.txt",
        "student_mindmap.txt",
        "student_problem_formulation.txt",
        "student_problem_and_method.txt",
        "student_full_guided.txt",
        "student_full_freestyle.txt",
    ]

    def test_all_prompt_files_exist(self):
        for name in self.EXPECTED_PROMPTS:
            path = ROOT / "prompts" / name
            assert path.exists(), f"Missing prompt: {name}"

    def test_student_prompts_have_placeholders(self):
        for name in self.EXPECTED_PROMPTS:
            if not name.startswith("student_"):
                continue
            text = (ROOT / "prompts" / name).read_text()
            assert "{problem_context}" in text, f"{name} missing {{problem_context}}"
            assert "{evaluation_criteria}" in text, f"{name} missing {{evaluation_criteria}}"
            assert "{refs_text}" in text, f"{name} missing {{refs_text}}"
            assert "{reference_guidance}" in text, f"{name} missing {{reference_guidance}}"

    def test_teacher_prompt_has_no_student_placeholders(self):
        text = (ROOT / "prompts" / "teacher_extract.txt").read_text()
        # Teacher prompt should NOT have student placeholders
        assert "{problem_context}" not in text
        assert "{refs_text}" not in text


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


class TestAuditLog:
    def test_create_and_serialize(self, tmp_path):
        from infra.audit import AuditLog, StepRecord

        log = AuditLog(
            paper_id="2006.06138",
            paper_url="https://arxiv.org/abs/2006.06138",
            reconstruction_type="abstract",
            student_model="gpt-4o",
            teacher_model="gpt-5.4",
        )
        log.add_step(StepRecord(
            step_name="test_step",
            model="gpt-4o",
            system_prompt="You are a test.",
            user_prompt="Test input.",
            response="Test output.",
            input_tokens=100,
            output_tokens=50,
            duration_seconds=1.5,
        ))
        log.mark_finished()

        assert log.total_input_tokens() == 100
        assert log.total_output_tokens() == 50
        assert log.total_duration() == 1.5
        assert log.finish_time != ""

        # Save and reload
        path = tmp_path / "audit.json"
        log.save(path)
        assert path.exists()

        loaded = AuditLog.load(path)
        assert loaded.paper_id == "2006.06138"
        assert len(loaded.steps) == 1
        assert loaded.steps[0].step_name == "test_step"
        assert loaded.total_input_tokens() == 100

    def test_empty_audit(self):
        from infra.audit import AuditLog
        log = AuditLog(
            paper_id="test", paper_url="", reconstruction_type="test",
            student_model="", teacher_model="",
        )
        assert log.total_input_tokens() == 0
        assert log.total_output_tokens() == 0
        assert log.total_duration() == 0.0


# ---------------------------------------------------------------------------
# Agent helpers
# ---------------------------------------------------------------------------


class TestAgentHelpers:
    def test_extract_paper_id_arxiv_abs(self):
        from agent import extract_paper_id
        assert extract_paper_id("https://arxiv.org/abs/2006.06138") == "2006.06138"

    def test_extract_paper_id_arxiv_pdf(self):
        from agent import extract_paper_id
        assert extract_paper_id("https://arxiv.org/pdf/2602.04770") == "2602.04770"

    def test_extract_paper_id_other_url(self):
        from agent import extract_paper_id
        pid = extract_paper_id("https://example.com/papers/my-paper.pdf")
        assert pid == "my-paper"

    def test_load_test_papers(self):
        from agent import load_test_papers
        papers = load_test_papers()
        assert len(papers) >= 1
        assert "url" in papers[0]

    def test_load_references(self):
        from agent import load_references
        refs = load_references()
        assert len(refs) >= 1
        assert "id" in refs[0]

    def test_prepare_refs_text(self):
        from agent import prepare_refs_text
        refs = [
            {"id": "test-1", "title": "Test Paper", "abstract": "An abstract.",
             "authors": ["A. Author"], "year": 2020, "venue": "NeurIPS"},
        ]
        text = prepare_refs_text(refs)
        assert "test-1" in text
        assert "Test Paper" in text
        assert "An abstract." in text
        assert "A. Author" in text

    def test_prepare_refs_text_full_text_from_cache(self):
        """When a .txt file exists in data/pdfs/, it should be loaded as full text."""
        from agent import prepare_refs_text
        refs = [
            {"id": "arxiv-1904.06019", "title": "Conformal Prediction Under Covariate Shift",
             "abstract": "Short abstract.", "authors": ["R. Tibshirani"],
             "year": 2020, "venue": "NeurIPS"},
        ]
        text = prepare_refs_text(refs)
        # Should contain full text, not just the short abstract
        if (ROOT / "data" / "pdfs" / "1904.06019.txt").exists():
            assert len(text) > 1000  # Full text is ~52K chars
            assert "Full text:" in text
            assert "Short abstract." not in text  # Full text replaces abstract

    def test_prepare_refs_text_empty(self):
        from agent import prepare_refs_text
        text = prepare_refs_text([])
        assert "No references" in text

    def test_reconstruction_modes_match_prompt_files(self):
        from agent import RECONSTRUCTION_MODES, PROMPT_FILES
        for mode in RECONSTRUCTION_MODES:
            assert mode in PROMPT_FILES, f"Mode {mode} missing prompt file mapping"
            path = ROOT / "prompts" / PROMPT_FILES[mode]
            assert path.exists(), f"Prompt file missing: {PROMPT_FILES[mode]}"

    def test_max_tokens_defined_for_all_modes(self):
        from agent import RECONSTRUCTION_MODES, MAX_TOKENS
        for mode in RECONSTRUCTION_MODES:
            assert mode in MAX_TOKENS, f"Mode {mode} missing MAX_TOKENS"
            assert MAX_TOKENS[mode] > 0


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------


class TestCLI:
    def test_help(self):
        import subprocess
        result = subprocess.run(
            ["python", str(ROOT / "agent.py"), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "--paper-url" in result.stdout
        assert "--modes" in result.stdout
        assert "--student-model" in result.stdout
        assert "--teacher-model" in result.stdout

    def test_mode_choices_in_help(self):
        import subprocess
        result = subprocess.run(
            ["python", str(ROOT / "agent.py"), "--help"],
            capture_output=True, text=True,
        )
        assert "abstract" in result.stdout
        assert "full_freestyle" in result.stdout


# ---------------------------------------------------------------------------
# Dispatch (mocked LLM)
# ---------------------------------------------------------------------------


class TestDispatchMocked:
    """End-to-end dispatch with mocked LLM calls."""

    def _mock_client(self):
        """Create a mock OpenAI client that returns plausible responses."""
        client = MagicMock()

        def fake_create(**kwargs):
            resp = MagicMock()
            model = kwargs.get("model", "unknown")
            step = kwargs.get("instructions", "")[:50]

            if "Teacher" in step or "teacher" in kwargs.get("instructions", ""):
                resp.output_text = json.dumps({
                    "problem_context": "How to extend conformal prediction under covariate shift.",
                    "reference_guidance": {"arxiv-1904.06019": "Core conformal prediction framework."},
                    "evaluation_criteria": "Valid marginal coverage under distribution shift.",
                    "domain_keywords": ["conformal prediction", "covariate shift"],
                })
            else:
                resp.output_text = (
                    "# Reconstruction\n\n"
                    "We propose a method for conformal prediction under shift.\n\n"
                    "## Approach\n\nUse importance weighting..."
                )

            usage = MagicMock()
            usage.input_tokens = 500
            usage.output_tokens = 200
            resp.usage = usage
            resp.id = "mock-resp-id"
            return resp

        client.responses.create = fake_create
        return client

    def test_single_paper_single_mode(self, tmp_path):
        from agent import dispatch_paper, load_references

        client = self._mock_client()
        refs = load_references()

        with patch("infra.pdf_utils.extract_text_from_pdf", return_value="Mock paper text."):
            result = dispatch_paper(
                client=client,
                paper_url="https://arxiv.org/abs/2006.06138",
                refs=refs,
                student_model="gpt-4o",
                teacher_model="gpt-5.4",
                modes=["abstract"],
                output_dir=tmp_path,
                conditions=["with_refs"],
            )

        assert result["paper_id"] == "2006.06138"
        assert "with_refs" in result["conditions"]
        assert "abstract" in result["conditions"]["with_refs"]
        assert result["conditions"]["with_refs"]["abstract"]["status"] == "success"

        # Check output files exist
        paper_dir = tmp_path / "2006.06138"
        assert (paper_dir / "_teacher" / "hint.json").exists()
        assert (paper_dir / "_teacher" / "audit.json").exists()
        assert (paper_dir / "with_refs" / "abstract" / "output.md").exists()
        assert (paper_dir / "with_refs" / "abstract" / "audit.json").exists()

        # Verify output content
        output = (paper_dir / "with_refs" / "abstract" / "output.md").read_text()
        assert "Reconstruction" in output
        assert "gpt-4o" in output

    def test_both_conditions(self, tmp_path):
        """Both with_refs and no_refs conditions produce output."""
        from agent import dispatch_paper, load_references

        client = self._mock_client()
        refs = load_references()

        with patch("infra.pdf_utils.extract_text_from_pdf", return_value="Mock paper text."):
            result = dispatch_paper(
                client=client,
                paper_url="https://arxiv.org/abs/2006.06138",
                refs=refs,
                student_model="gpt-4o",
                teacher_model="gpt-5.4",
                modes=["abstract"],
                output_dir=tmp_path,
                conditions=["with_refs", "no_refs"],
            )

        for cond in ["with_refs", "no_refs"]:
            assert cond in result["conditions"]
            assert result["conditions"][cond]["abstract"]["status"] == "success"
            assert (tmp_path / "2006.06138" / cond / "abstract" / "output.md").exists()

    def test_all_modes(self, tmp_path):
        from agent import dispatch_paper, load_references, RECONSTRUCTION_MODES

        client = self._mock_client()
        refs = load_references()

        with patch("infra.pdf_utils.extract_text_from_pdf", return_value="Mock paper text."):
            result = dispatch_paper(
                client=client,
                paper_url="https://arxiv.org/abs/2006.06138",
                refs=refs,
                student_model="gpt-4o",
                teacher_model="gpt-5.4",
                modes=RECONSTRUCTION_MODES,
                output_dir=tmp_path,
                conditions=["with_refs"],
            )

        for mode in RECONSTRUCTION_MODES:
            assert mode in result["conditions"]["with_refs"]
            assert result["conditions"]["with_refs"][mode]["status"] == "success"
            assert (tmp_path / "2006.06138" / "with_refs" / mode / "output.md").exists()

    def test_dispatch_summary(self, tmp_path):
        from agent import dispatch_paper, write_dispatch_summary, load_references

        client = self._mock_client()
        refs = load_references()

        with patch("infra.pdf_utils.extract_text_from_pdf", return_value="Mock paper text."):
            result = dispatch_paper(
                client=client,
                paper_url="https://arxiv.org/abs/2006.06138",
                refs=refs,
                student_model="gpt-4o",
                teacher_model="gpt-5.4",
                modes=["abstract", "mindmap"],
                output_dir=tmp_path,
                conditions=["with_refs"],
            )

        write_dispatch_summary([result], tmp_path, "gpt-4o", "gpt-5.4")
        summary_path = tmp_path / "SUMMARY.md"
        assert summary_path.exists()
        text = summary_path.read_text()
        assert "2006.06138" in text
        assert "abstract" in text
        assert "with_refs" in text

    def test_llm_error_handled(self, tmp_path):
        """If the student LLM call fails, the mode records an error without crashing."""
        from agent import dispatch_paper, load_references

        client = self._mock_client()
        # Make student calls fail
        call_count = [0]
        original_create = client.responses.create

        def failing_create(**kwargs):
            call_count[0] += 1
            if call_count[0] > 1:  # Let teacher succeed, student fails
                raise RuntimeError("API quota exceeded")
            return original_create(**kwargs)

        client.responses.create = failing_create
        refs = load_references()

        with patch("infra.pdf_utils.extract_text_from_pdf", return_value="Mock paper text."):
            result = dispatch_paper(
                client=client,
                paper_url="https://arxiv.org/abs/2006.06138",
                refs=refs,
                student_model="gpt-4o",
                teacher_model="gpt-5.4",
                modes=["abstract"],
                output_dir=tmp_path,
                conditions=["with_refs"],
            )

        assert result["conditions"]["with_refs"]["abstract"]["status"] == "error"
        assert (tmp_path / "2006.06138" / "with_refs" / "abstract" / "error.txt").exists()


# ---------------------------------------------------------------------------
# Infra imports smoke test
# ---------------------------------------------------------------------------


class TestEvaluation:
    def test_parse_eval_json(self):
        from infra.evaluate import _parse_eval
        raw = """Here is my evaluation:
```json
{
  "scores": {"problem_understanding": 4, "technical_depth": 3},
  "composite_score": 3.5,
  "novelty_gap": "Missed the key insight.",
  "strongest_aspect": "Good writing.",
  "weakest_aspect": "Wrong method."
}
```"""
        result = _parse_eval(raw)
        assert result["composite_score"] == 3.5
        assert "Missed" in result["novelty_gap"]

    def test_parse_eval_fallback(self):
        from infra.evaluate import _parse_eval
        result = _parse_eval("This is not JSON at all.")
        assert "parse_error" in result

    def test_evaluate_importable(self):
        from infra.evaluate import evaluate_reconstruction  # noqa: F401


class TestPdfUtils:
    def test_local_pdf_cache_lookup(self):
        """PDF cache finds locally stored PDFs by arxiv ID."""
        from infra.pdf_utils import _resolve_source, _PDF_CACHE
        # If the 2006.06138 PDF is in the cache, it should be found
        cached = _PDF_CACHE / "2006.06138.pdf"
        if cached.exists():
            path, tmp = _resolve_source("https://arxiv.org/abs/2006.06138")
            assert path == cached
            assert tmp is None

    def test_extract_arxiv_id(self):
        from infra.pdf_utils import _extract_arxiv_id
        assert _extract_arxiv_id("https://arxiv.org/abs/2006.06138") == "2006.06138"
        assert _extract_arxiv_id("https://arxiv.org/pdf/2602.04770") == "2602.04770"
        assert _extract_arxiv_id("https://example.com/other") is None

    def test_html_to_text(self):
        from infra.pdf_utils import _html_to_text
        html = '<p>We define <math alttext="f(x)">...</math> as follows.</p>'
        text = _html_to_text(html, 1000)
        assert "$f(x)$" in text
        assert "We define" in text


class TestInfraImports:
    def test_all_importable(self):
        from infra import extract_text_from_pdf, AuditLog, StepRecord  # noqa: F401
        from infra import evaluate_reconstruction  # noqa: F401
        from infra.llm import llm_call  # noqa: F401
        from infra.pdf_utils import extract_text_from_pdf  # noqa: F401
