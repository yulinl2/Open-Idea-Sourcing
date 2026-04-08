"""Unit tests for the iterative hint-refinement engine.

Tests cover:
- Data structures (RoundRecord, IterativeResult)
- Convergence detection logic
- Hint refinement parsing
- Full iterative loop with mocked LLM
- Abstract mode end-to-end
- Problem-method mode end-to-end
- Edge cases (LLM failures, parse errors, single round)
"""

from __future__ import annotations

import json
import copy
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import asdict

import pytest

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class TestRoundRecord:
    def test_create_basic(self):
        from infra.iterative import RoundRecord
        r = RoundRecord(
            round_number=1,
            hint={"problem_context": "test problem"},
        )
        assert r.round_number == 1
        assert r.hint["problem_context"] == "test problem"
        assert r.student_output == ""
        assert r.evaluation == {}
        assert r.refined_hint is None

    def test_full_round(self):
        from infra.iterative import RoundRecord
        r = RoundRecord(
            round_number=2,
            hint={"problem_context": "test"},
            student_output="Student wrote this.",
            evaluation={"composite_score": 3.5, "novelty_gap": "Missed X."},
            refined_hint={"problem_context": "refined test"},
            refinement_rationale={
                "additions": [{"what": "added X", "why": "student missed it"}],
                "removals": [],
            },
            convergence_signal={
                "hint_changed_substantially": True,
                "recommendation": "continue",
            },
        )
        assert r.evaluation["composite_score"] == 3.5
        assert len(r.refinement_rationale["additions"]) == 1

    def test_serializable(self):
        from infra.iterative import RoundRecord
        r = RoundRecord(round_number=1, hint={"problem_context": "test"})
        d = asdict(r)
        assert d["round_number"] == 1
        json_str = json.dumps(d)
        assert "round_number" in json_str


class TestIterativeResult:
    def _make_result(self):
        from infra.iterative import IterativeResult, RoundRecord
        result = IterativeResult(
            paper_id="2006.06138",
            mode="abstract",
            condition="with_refs",
            initial_hint={"problem_context": "initial"},
        )
        result.rounds = [
            RoundRecord(
                round_number=1,
                hint={"problem_context": "initial"},
                student_output="Round 1 output.",
                evaluation={"composite_score": 2.5},
            ),
            RoundRecord(
                round_number=2,
                hint={"problem_context": "refined"},
                student_output="Round 2 output.",
                evaluation={"composite_score": 3.8},
            ),
        ]
        result.converged = True
        result.convergence_reason = "score plateau"
        result.final_hint = {"problem_context": "refined"}
        result.total_rounds = 2
        return result

    def test_score_trajectory(self):
        result = self._make_result()
        scores = result.score_trajectory()
        assert scores == [2.5, 3.8]

    def test_score_trajectory_handles_missing(self):
        from infra.iterative import IterativeResult, RoundRecord
        result = IterativeResult(
            paper_id="test", mode="abstract", condition="with_refs",
            initial_hint={},
        )
        result.rounds = [
            RoundRecord(round_number=1, hint={}, evaluation={}),
            RoundRecord(round_number=2, hint={}, evaluation={"composite_score": "bad"}),
        ]
        scores = result.score_trajectory()
        assert scores == [0.0, 0.0]

    def test_hint_trajectory(self):
        result = self._make_result()
        hints = result.hint_trajectory()
        assert len(hints) == 2
        assert hints[0]["problem_context"] == "initial"
        assert hints[1]["problem_context"] == "refined"

    def test_to_dict(self):
        result = self._make_result()
        d = result.to_dict()
        assert d["paper_id"] == "2006.06138"
        assert d["mode"] == "abstract"
        assert d["total_rounds"] == 2
        assert d["score_trajectory"] == [2.5, 3.8]
        assert len(d["rounds"]) == 2
        # Should be JSON-serializable
        json_str = json.dumps(d, default=str)
        assert "2006.06138" in json_str

    def test_save_and_load(self, tmp_path):
        result = self._make_result()
        path = tmp_path / "result.json"
        result.save(path)
        assert path.exists()

        loaded = type(result).load(path)
        assert loaded.paper_id == "2006.06138"
        assert loaded.total_rounds == 2
        assert len(loaded.rounds) == 2
        assert loaded.rounds[0].round_number == 1
        assert loaded.converged is True


# ---------------------------------------------------------------------------
# Convergence detection
# ---------------------------------------------------------------------------


class TestConvergence:
    def _make_rounds(self, scores, signals=None):
        from infra.iterative import RoundRecord
        rounds = []
        for i, score in enumerate(scores):
            sig = (signals[i] if signals and i < len(signals) else {})
            rounds.append(RoundRecord(
                round_number=i + 1,
                hint={"problem_context": f"hint_{i}"},
                evaluation={"composite_score": score},
                convergence_signal=sig,
            ))
        return rounds

    def test_max_rounds_reached(self):
        from infra.iterative import check_convergence
        rounds = self._make_rounds([2.0, 3.0, 3.5, 4.0, 4.2])
        stop, reason = check_convergence(rounds, max_rounds=5)
        assert stop is True
        assert "max rounds" in reason

    def test_min_rounds_enforced(self):
        from infra.iterative import check_convergence, MIN_ROUNDS
        rounds = self._make_rounds([4.5])
        stop, reason = check_convergence(rounds, max_rounds=5)
        assert stop is False
        assert "more rounds" in reason
        # Also check with MIN_ROUNDS-1 rounds
        rounds2 = self._make_rounds([4.0] * (MIN_ROUNDS - 1))
        stop2, reason2 = check_convergence(rounds2, max_rounds=10)
        assert stop2 is False

    def test_teacher_recommends_stop(self):
        from infra.iterative import check_convergence
        signals = [{}, {}, {"recommendation": "stop"}]
        rounds = self._make_rounds([3.0, 3.3, 3.5], signals=signals)
        stop, reason = check_convergence(rounds, max_rounds=5)
        assert stop is True
        assert "teacher recommended" in reason

    def test_score_plateau_with_stable_hint(self):
        from infra.iterative import check_convergence
        signals = [
            {},
            {},
            {"hint_changed_substantially": False},
        ]
        rounds = self._make_rounds([3.0, 3.5, 3.6], signals=signals)
        stop, reason = check_convergence(rounds, max_rounds=5, score_threshold=0.3)
        assert stop is True
        assert "plateau" in reason

    def test_score_plateau_but_hint_changed(self):
        from infra.iterative import check_convergence
        signals = [
            {},
            {},
            {"hint_changed_substantially": True},
        ]
        rounds = self._make_rounds([3.0, 3.5, 3.6], signals=signals)
        stop, reason = check_convergence(rounds, max_rounds=5, score_threshold=0.3)
        # Should NOT stop because hint is still changing
        assert stop is False

    def test_high_residual_captured(self):
        from infra.iterative import check_convergence
        signals = [
            {},
            {},
            {"estimated_residual_captured": 0.9, "hint_changed_substantially": True},
        ]
        rounds = self._make_rounds([3.0, 3.8, 4.5], signals=signals)
        stop, reason = check_convergence(rounds, max_rounds=5)
        assert stop is True
        assert "residual captured" in reason

    def test_not_converged_yet(self):
        from infra.iterative import check_convergence
        signals = [
            {},
            {},
            {"hint_changed_substantially": True, "estimated_residual_captured": 0.4,
             "recommendation": "continue"},
        ]
        rounds = self._make_rounds([2.0, 3.0, 3.5], signals=signals)
        stop, reason = check_convergence(rounds, max_rounds=5)
        assert stop is False

    def test_score_regression_blocks_convergence(self):
        """If latest score dropped below best, don't converge even if teacher says stop."""
        from infra.iterative import check_convergence
        signals = [
            {},
            {},
            {"recommendation": "stop", "estimated_residual_captured": 0.9},
        ]
        # Score dropped from 3.4 to 3.2 — should NOT stop
        rounds = self._make_rounds([3.0, 3.4, 3.2], signals=signals)
        stop, reason = check_convergence(rounds, max_rounds=5)
        assert stop is False
        assert "regressed" in reason


# ---------------------------------------------------------------------------
# Hint refinement parsing
# ---------------------------------------------------------------------------


class TestParseRefinement:
    def test_parse_json_block(self):
        from infra.iterative import _parse_refinement
        text = """Here is my refinement:
```json
{
  "refined_hint": {"problem_context": "refined problem"},
  "refinement_rationale": {"additions": [], "removals": []},
  "convergence_signal": {"recommendation": "continue"}
}
```"""
        result = _parse_refinement(text)
        assert "refined_hint" in result
        assert result["refined_hint"]["problem_context"] == "refined problem"

    def test_parse_bare_json(self):
        from infra.iterative import _parse_refinement
        text = '{"refined_hint": {"problem_context": "bare"}, "refinement_rationale": {}}'
        result = _parse_refinement(text)
        assert result["refined_hint"]["problem_context"] == "bare"

    def test_parse_fallback(self):
        from infra.iterative import _parse_refinement
        result = _parse_refinement("This is not JSON at all.")
        assert "parse_error" in result

    def test_parse_nested_json(self):
        from infra.iterative import _parse_refinement
        text = """
```json
{
  "refined_hint": {
    "problem_context": "How to extend conformal inference to treatment effects.",
    "desirable_properties": ["Coverage guarantee", "Efficiency"],
    "field_context": "Causal inference meets conformal prediction."
  },
  "refinement_rationale": {
    "additions": [
      {"what": "Added emphasis on treatment effect heterogeneity", "why": "Student missed this"}
    ],
    "removals": [
      {"what": "Removed mention of distribution-free methods", "why": "Student already knew this from refs"}
    ],
    "unchanged": "Problem motivation stayed the same"
  },
  "convergence_signal": {
    "hint_changed_substantially": true,
    "estimated_residual_captured": 0.6,
    "teacher_confidence": "medium",
    "recommendation": "continue"
  }
}
```"""
        result = _parse_refinement(text)
        assert result["refined_hint"]["problem_context"].startswith("How to extend")
        assert len(result["refinement_rationale"]["additions"]) == 1
        assert result["convergence_signal"]["estimated_residual_captured"] == 0.6


# ---------------------------------------------------------------------------
# Full iterative loop (mocked LLM)
# ---------------------------------------------------------------------------


class TestIterativeLoopMocked:
    """Test the full iterative loop with mocked LLM calls."""

    def _mock_student_fn(self, round_outputs=None):
        """Create a mock student function that returns different outputs per round."""
        call_count = [0]
        default_outputs = [
            "Round 1: Basic reconstruction focusing on the problem.",
            "Round 2: Improved reconstruction with better insight.",
            "Round 3: Close to the paper's actual contribution.",
            "Round 4: Nearly perfect reconstruction.",
            "Round 5: Perfect match.",
        ]
        outputs = round_outputs or default_outputs

        def mock_fn(client, model, mode, hint, refs_text, audit):
            idx = min(call_count[0], len(outputs) - 1)
            call_count[0] += 1
            return outputs[idx]

        return mock_fn

    def _mock_client(self):
        """Create mock LLM client."""
        client = MagicMock()

        eval_scores = [
            {"composite_score": 2.5, "novelty_gap": "Missed the key mechanism."},
            {"composite_score": 3.2, "novelty_gap": "Getting closer but misses specifics."},
            {"composite_score": 4.0, "novelty_gap": "Minor gaps remain."},
            {"composite_score": 4.3, "novelty_gap": "Very close."},
            {"composite_score": 4.5, "novelty_gap": "Essentially captured."},
        ]

        refine_responses = [
            {
                "refined_hint": {
                    "problem_context": "Refined after round 1.",
                    "desirable_properties": ["prop1"],
                    "field_context": "Context.",
                },
                "refinement_rationale": {
                    "additions": [{"what": "Added insight A", "why": "student missed it"}],
                    "removals": [],
                    "unchanged": "Core problem stayed.",
                },
                "convergence_signal": {
                    "hint_changed_substantially": True,
                    "estimated_residual_captured": 0.4,
                    "teacher_confidence": "medium",
                    "recommendation": "continue",
                },
            },
            {
                "refined_hint": {
                    "problem_context": "Refined after round 2.",
                    "desirable_properties": ["prop1", "prop2"],
                    "field_context": "Context.",
                },
                "refinement_rationale": {
                    "additions": [{"what": "Added insight B", "why": "still missing"}],
                    "removals": [{"what": "Removed prop0", "why": "student got it from refs"}],
                    "unchanged": "Additions from round 1 stayed.",
                },
                "convergence_signal": {
                    "hint_changed_substantially": True,
                    "estimated_residual_captured": 0.65,
                    "teacher_confidence": "medium",
                    "recommendation": "continue",
                },
            },
            {
                "refined_hint": {
                    "problem_context": "Refined after round 3.",
                    "desirable_properties": ["prop1", "prop2"],
                    "field_context": "Context.",
                },
                "refinement_rationale": {
                    "additions": [],
                    "removals": [],
                    "unchanged": "Hint is stable now.",
                },
                "convergence_signal": {
                    "hint_changed_substantially": False,
                    "estimated_residual_captured": 0.9,
                    "teacher_confidence": "high",
                    "recommendation": "stop",
                },
            },
        ]

        call_count = {"eval": 0, "refine": 0}

        def mock_create(**kwargs):
            resp = MagicMock()
            system = kwargs.get("system", "") or kwargs.get("instructions", "")

            if "conceptual residual" in system.lower() or "iterative reconstruction" in system.lower():
                idx = min(call_count["refine"], len(refine_responses) - 1)
                resp_data = refine_responses[idx]
                call_count["refine"] += 1
                text = f"```json\n{json.dumps(resp_data)}\n```"
            elif "evaluate" in system.lower() or "scoring" in system.lower():
                idx = min(call_count["eval"], len(eval_scores) - 1)
                resp_data = eval_scores[idx]
                call_count["eval"] += 1
                text = f"```json\n{json.dumps(resp_data)}\n```"
            else:
                text = "Generic response."

            # Support both OpenAI and Anthropic response formats
            resp.output_text = text
            usage = MagicMock()
            usage.input_tokens = 500
            usage.output_tokens = 200
            resp.usage = usage
            resp.id = "mock-id"

            # Anthropic format
            block = MagicMock()
            block.text = text
            resp.content = [block]

            return resp

        client.responses.create = mock_create
        # Also mock Anthropic-style
        messages = MagicMock()
        messages.create = mock_create
        client.messages = messages

        return client

    def test_basic_iterative_loop(self, tmp_path):
        from infra.iterative import run_iterative_refinement

        client = self._mock_client()
        initial_hint = {
            "problem_context": "How to do conformal inference for treatment effects.",
            "desirable_properties": ["Coverage guarantees"],
            "field_context": "Causal inference.",
        }

        result = run_iterative_refinement(
            client=client,
            student_model="gpt-4o",
            teacher_model="gpt-5.4",
            mode="abstract",
            initial_hint=initial_hint,
            refs_text="Reference paper text here.",
            paper_text="Full paper text here.",
            paper_id="2006.06138",
            condition="with_refs",
            run_student_fn=self._mock_student_fn(),
            max_rounds=5,
            output_dir=tmp_path / "iterative_test",
        )

        # Basic assertions
        assert result.paper_id == "2006.06138"
        assert result.mode == "abstract"
        assert result.total_rounds >= 2
        assert result.total_rounds <= 5
        assert len(result.rounds) == result.total_rounds

        # Score trajectory should show improvement
        scores = result.score_trajectory()
        assert len(scores) == result.total_rounds
        assert all(isinstance(s, float) for s in scores)

        # Should have converged (teacher recommends stop on round 3)
        assert result.converged is True

        # Final hint should differ from initial
        assert result.final_hint != initial_hint

        # Output files should exist
        iter_dir = tmp_path / "iterative_test"
        assert (iter_dir / "iterative_result.json").exists()
        for i in range(1, result.total_rounds + 1):
            round_dir = iter_dir / f"round_{i}"
            assert (round_dir / "hint.json").exists()
            assert (round_dir / "output.md").exists()
            assert (round_dir / "eval.json").exists()

    def test_max_rounds_cap(self, tmp_path):
        """Verify the loop stops at max_rounds even without convergence."""
        from infra.iterative import run_iterative_refinement

        client = self._mock_client()

        # Override mock to never recommend stop
        original_create = client.messages.create

        def never_stop_create(**kwargs):
            resp = original_create(**kwargs)
            system = kwargs.get("system", "") or kwargs.get("instructions", "")
            if "refin" in system.lower() or "conceptual residual" in system.lower():
                data = {
                    "refined_hint": {"problem_context": "still refining", "desirable_properties": [], "field_context": ""},
                    "refinement_rationale": {"additions": [{"what": "a", "why": "b"}], "removals": []},
                    "convergence_signal": {
                        "hint_changed_substantially": True,
                        "estimated_residual_captured": 0.3,
                        "recommendation": "continue",
                    },
                }
                text = f"```json\n{json.dumps(data)}\n```"
                resp.output_text = text
                block = MagicMock()
                block.text = text
                resp.content = [block]
            return resp

        client.messages.create = never_stop_create
        client.responses.create = never_stop_create

        result = run_iterative_refinement(
            client=client,
            student_model="gpt-4o",
            teacher_model="gpt-5.4",
            mode="abstract",
            initial_hint={"problem_context": "test", "desirable_properties": [], "field_context": ""},
            refs_text="refs",
            paper_text="paper",
            paper_id="test",
            condition="with_refs",
            run_student_fn=self._mock_student_fn(),
            max_rounds=3,
            output_dir=tmp_path / "max_rounds_test",
        )

        assert result.total_rounds == 3
        assert "max rounds" in result.convergence_reason

    def test_student_failure_stops_loop(self, tmp_path):
        """If student fails, the loop should stop gracefully."""
        from infra.iterative import run_iterative_refinement

        client = self._mock_client()

        def failing_student(client, model, mode, hint, refs_text, audit):
            raise RuntimeError("API quota exceeded")

        result = run_iterative_refinement(
            client=client,
            student_model="gpt-4o",
            teacher_model="gpt-5.4",
            mode="abstract",
            initial_hint={"problem_context": "test", "desirable_properties": [], "field_context": ""},
            refs_text="refs",
            paper_text="paper",
            paper_id="test",
            condition="with_refs",
            run_student_fn=failing_student,
            max_rounds=5,
        )

        assert result.total_rounds == 1
        assert "ERROR" in result.rounds[0].student_output

    def test_no_output_dir(self):
        """Loop works without output_dir (no file I/O)."""
        from infra.iterative import run_iterative_refinement

        client = self._mock_client()

        result = run_iterative_refinement(
            client=client,
            student_model="gpt-4o",
            teacher_model="gpt-5.4",
            mode="abstract",
            initial_hint={"problem_context": "test", "desirable_properties": [], "field_context": ""},
            refs_text="refs",
            paper_text="paper",
            paper_id="test",
            condition="with_refs",
            run_student_fn=self._mock_student_fn(),
            max_rounds=5,
            output_dir=None,
        )

        assert result.total_rounds >= 2
        assert len(result.rounds) > 0

    def test_hint_evolves_across_rounds(self, tmp_path):
        """Verify the hint actually changes between rounds."""
        from infra.iterative import run_iterative_refinement

        client = self._mock_client()
        initial_hint = {
            "problem_context": "Original problem statement.",
            "desirable_properties": ["prop_a"],
            "field_context": "Original context.",
        }

        result = run_iterative_refinement(
            client=client,
            student_model="gpt-4o",
            teacher_model="gpt-5.4",
            mode="abstract",
            initial_hint=initial_hint,
            refs_text="refs",
            paper_text="paper",
            paper_id="test",
            condition="with_refs",
            run_student_fn=self._mock_student_fn(),
            max_rounds=5,
            output_dir=tmp_path / "evolve_test",
        )

        hints = result.hint_trajectory()
        if len(hints) >= 2:
            # At least one hint should differ from the initial
            assert any(h != initial_hint for h in hints[1:])

    def test_result_serialization_roundtrip(self, tmp_path):
        """IterativeResult survives save/load cycle."""
        from infra.iterative import run_iterative_refinement, IterativeResult

        client = self._mock_client()

        result = run_iterative_refinement(
            client=client,
            student_model="gpt-4o",
            teacher_model="gpt-5.4",
            mode="abstract",
            initial_hint={"problem_context": "test", "desirable_properties": [], "field_context": ""},
            refs_text="refs",
            paper_text="paper",
            paper_id="test",
            condition="with_refs",
            run_student_fn=self._mock_student_fn(),
            max_rounds=5,
            output_dir=tmp_path / "serial_test",
        )

        path = tmp_path / "serial_test" / "iterative_result.json"
        assert path.exists()

        loaded = IterativeResult.load(path)
        assert loaded.paper_id == result.paper_id
        assert loaded.total_rounds == result.total_rounds
        assert loaded.converged == result.converged
        assert len(loaded.rounds) == len(result.rounds)


# ---------------------------------------------------------------------------
# Abstract mode specific tests
# ---------------------------------------------------------------------------


class TestAbstractMode:
    """Tests specifically for abstract mode iterative refinement."""

    def test_abstract_mode_accepted(self):
        from infra.iterative import RoundRecord
        r = RoundRecord(round_number=1, hint={"problem_context": "abstract test"})
        assert r.round_number == 1

    def test_abstract_output_structure(self, tmp_path):
        """Verify output directory structure for abstract mode."""
        from infra.iterative import run_iterative_refinement

        client = MagicMock()
        eval_data = {"composite_score": 3.5, "novelty_gap": "Some gap."}
        refine_data = {
            "refined_hint": {"problem_context": "p", "desirable_properties": [], "field_context": ""},
            "refinement_rationale": {"additions": [], "removals": []},
            "convergence_signal": {
                "hint_changed_substantially": False,
                "estimated_residual_captured": 0.9,
                "recommendation": "stop",
            },
        }

        call_count = [0]

        def mock_create(**kwargs):
            call_count[0] += 1
            resp = MagicMock()
            system = kwargs.get("system", "") or kwargs.get("instructions", "")
            if "evaluate" in system.lower() or "scoring" in system.lower():
                text = f"```json\n{json.dumps(eval_data)}\n```"
            else:
                text = f"```json\n{json.dumps(refine_data)}\n```"
            resp.output_text = text
            block = MagicMock()
            block.text = text
            resp.content = [block]
            usage = MagicMock()
            usage.input_tokens = 100
            usage.output_tokens = 50
            resp.usage = usage
            resp.id = "mock"
            return resp

        client.responses.create = mock_create
        client.messages = MagicMock()
        client.messages.create = mock_create

        def simple_student(client, model, mode, hint, refs_text, audit):
            return "# Abstract\n\nThis paper proposes..."

        out = tmp_path / "abstract_test"
        result = run_iterative_refinement(
            client=client,
            student_model="gpt-4o",
            teacher_model="gpt-5.4",
            mode="abstract",
            initial_hint={"problem_context": "test", "desirable_properties": [], "field_context": ""},
            refs_text="refs",
            paper_text="paper",
            paper_id="test_paper",
            condition="with_refs",
            run_student_fn=simple_student,
            max_rounds=5,
            output_dir=out,
        )

        # Verify directory structure
        assert (out / "iterative_result.json").exists()
        assert (out / "round_1" / "hint.json").exists()
        assert (out / "round_1" / "output.md").exists()
        assert (out / "round_1" / "eval.json").exists()

        # Verify result content
        result_data = json.loads((out / "iterative_result.json").read_text())
        assert result_data["mode"] == "abstract"
        assert "score_trajectory" in result_data


# ---------------------------------------------------------------------------
# Problem-method mode specific tests
# ---------------------------------------------------------------------------


class TestProblemMethodMode:
    """Tests specifically for problem_method mode iterative refinement."""

    def test_problem_method_longer_output(self, tmp_path):
        """problem_method should handle longer student outputs."""
        from infra.iterative import run_iterative_refinement

        client = MagicMock()
        eval_data = {"composite_score": 3.0, "novelty_gap": "Method details missing."}
        refine_data = {
            "refined_hint": {"problem_context": "p", "desirable_properties": [], "field_context": ""},
            "refinement_rationale": {"additions": [{"what": "a", "why": "b"}], "removals": []},
            "convergence_signal": {
                "hint_changed_substantially": False,
                "estimated_residual_captured": 0.85,
                "recommendation": "stop",
            },
        }

        def mock_create(**kwargs):
            resp = MagicMock()
            system = kwargs.get("system", "") or kwargs.get("instructions", "")
            if "evaluate" in system.lower() or "scoring" in system.lower():
                text = f"```json\n{json.dumps(eval_data)}\n```"
            else:
                text = f"```json\n{json.dumps(refine_data)}\n```"
            resp.output_text = text
            block = MagicMock()
            block.text = text
            resp.content = [block]
            usage = MagicMock()
            usage.input_tokens = 300
            usage.output_tokens = 150
            resp.usage = usage
            resp.id = "mock"
            return resp

        client.responses.create = mock_create
        client.messages = MagicMock()
        client.messages.create = mock_create

        long_output = (
            "# Problem Formulation\n\n"
            "Let $X \\in \\mathcal{X}$ denote the feature space...\n\n"
            "## Notation\n\n$Y(0), Y(1)$ are potential outcomes...\n\n"
            "# Methodology\n\n"
            "## Algorithm 1: Conformal Treatment Effect Bounds\n\n"
            "```\nInput: calibration data...\nStep 1: Compute weights...\n```\n\n"
            "## Theoretical Properties\n\n"
            "**Theorem 1.** Under Assumptions 1-3, the intervals achieve...\n\n"
        ) * 3  # Make it long

        def long_student(client, model, mode, hint, refs_text, audit):
            return long_output

        out = tmp_path / "pm_test"
        result = run_iterative_refinement(
            client=client,
            student_model="gpt-4o",
            teacher_model="gpt-5.4",
            mode="problem_method",
            initial_hint={"problem_context": "test", "desirable_properties": [], "field_context": ""},
            refs_text="refs",
            paper_text="paper" * 1000,  # Longer paper text
            paper_id="test_pm",
            condition="with_refs",
            run_student_fn=long_student,
            max_rounds=5,
            output_dir=out,
        )

        assert result.mode == "problem_method"
        assert result.total_rounds >= 2
        # Verify long output was saved
        saved_output = (out / "round_1" / "output.md").read_text()
        assert "Problem Formulation" in saved_output
        assert "Methodology" in saved_output


# ---------------------------------------------------------------------------
# Prompt file tests
# ---------------------------------------------------------------------------


class TestRefinePrompt:
    def test_refine_prompt_exists(self):
        path = ROOT / "prompts" / "teacher_refine_hint.txt"
        assert path.exists(), "Missing prompt: teacher_refine_hint.txt"

    def test_refine_prompt_content(self):
        text = (ROOT / "prompts" / "teacher_refine_hint.txt").read_text()
        # Should contain key concepts
        assert "conceptual residual" in text.lower()
        assert "refined_hint" in text
        assert "refinement_rationale" in text
        assert "convergence_signal" in text
        assert "anti-leakage" in text.lower()

    def test_refine_prompt_no_student_placeholders(self):
        text = (ROOT / "prompts" / "teacher_refine_hint.txt").read_text()
        # Should NOT have student template placeholders
        assert "{problem_context}" not in text
        assert "{refs_text}" not in text


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_single_round_min(self, tmp_path):
        """With max_rounds=1, should do exactly 1 round."""
        from infra.iterative import run_iterative_refinement

        client = MagicMock()
        eval_data = {"composite_score": 4.0}

        def mock_create(**kwargs):
            resp = MagicMock()
            text = f"```json\n{json.dumps(eval_data)}\n```"
            resp.output_text = text
            block = MagicMock()
            block.text = text
            resp.content = [block]
            usage = MagicMock()
            usage.input_tokens = 100
            usage.output_tokens = 50
            resp.usage = usage
            resp.id = "mock"
            return resp

        client.responses.create = mock_create
        client.messages = MagicMock()
        client.messages.create = mock_create

        result = run_iterative_refinement(
            client=client,
            student_model="m",
            teacher_model="m",
            mode="abstract",
            initial_hint={"problem_context": "t", "desirable_properties": [], "field_context": ""},
            refs_text="r",
            paper_text="p",
            paper_id="t",
            condition="with_refs",
            run_student_fn=lambda *a, **kw: "output",
            max_rounds=1,
        )

        assert result.total_rounds == 1
        assert "max rounds" in result.convergence_reason

    def test_empty_initial_hint(self, tmp_path):
        """Handles empty initial hint gracefully."""
        from infra.iterative import run_iterative_refinement

        client = MagicMock()
        eval_data = {"composite_score": 1.0}
        refine_data = {
            "refined_hint": {"problem_context": "now with content", "desirable_properties": [], "field_context": ""},
            "refinement_rationale": {"additions": [{"what": "everything", "why": "hint was empty"}], "removals": []},
            "convergence_signal": {"hint_changed_substantially": True, "recommendation": "stop"},
        }

        call_count = [0]

        def mock_create(**kwargs):
            resp = MagicMock()
            system = kwargs.get("system", "") or kwargs.get("instructions", "")
            if "evaluate" in system.lower() or "scoring" in system.lower():
                text = f"```json\n{json.dumps(eval_data)}\n```"
            else:
                text = f"```json\n{json.dumps(refine_data)}\n```"
            resp.output_text = text
            block = MagicMock()
            block.text = text
            resp.content = [block]
            usage = MagicMock()
            usage.input_tokens = 100
            usage.output_tokens = 50
            resp.usage = usage
            resp.id = "mock"
            return resp

        client.responses.create = mock_create
        client.messages = MagicMock()
        client.messages.create = mock_create

        result = run_iterative_refinement(
            client=client,
            student_model="m",
            teacher_model="m",
            mode="abstract",
            initial_hint={},
            refs_text="r",
            paper_text="p",
            paper_id="t",
            condition="with_refs",
            run_student_fn=lambda *a, **kw: "output",
            max_rounds=3,
        )

        assert result.total_rounds >= 2

    def test_initial_hint_not_mutated(self):
        """The original initial_hint dict must not be mutated."""
        from infra.iterative import run_iterative_refinement

        client = MagicMock()
        eval_data = {"composite_score": 4.0}
        refine_data = {
            "refined_hint": {"problem_context": "changed!", "desirable_properties": ["new"], "field_context": ""},
            "refinement_rationale": {"additions": [], "removals": []},
            "convergence_signal": {"hint_changed_substantially": False, "recommendation": "stop"},
        }

        def mock_create(**kwargs):
            resp = MagicMock()
            system = kwargs.get("system", "") or kwargs.get("instructions", "")
            if "evaluate" in system.lower() or "scoring" in system.lower():
                text = f"```json\n{json.dumps(eval_data)}\n```"
            else:
                text = f"```json\n{json.dumps(refine_data)}\n```"
            resp.output_text = text
            block = MagicMock()
            block.text = text
            resp.content = [block]
            usage = MagicMock()
            usage.input_tokens = 100
            usage.output_tokens = 50
            resp.usage = usage
            resp.id = "mock"
            return resp

        client.responses.create = mock_create
        client.messages = MagicMock()
        client.messages.create = mock_create

        original = {"problem_context": "original", "desirable_properties": ["orig"], "field_context": "ctx"}
        frozen_copy = copy.deepcopy(original)

        run_iterative_refinement(
            client=client,
            student_model="m",
            teacher_model="m",
            mode="abstract",
            initial_hint=original,
            refs_text="r",
            paper_text="p",
            paper_id="t",
            condition="with_refs",
            run_student_fn=lambda *a, **kw: "output",
            max_rounds=3,
        )

        # Original must not have been mutated
        assert original == frozen_copy


# ---------------------------------------------------------------------------
# Import smoke test
# ---------------------------------------------------------------------------


class TestIterativeImports:
    def test_all_importable(self):
        from infra.iterative import (  # noqa: F401
            RoundRecord,
            IterativeResult,
            run_iterative_refinement,
            refine_hint,
            check_convergence,
        )

    def test_infra_init_exports(self):
        from infra import run_iterative_refinement, IterativeResult  # noqa: F401
        from infra import create_context_seed  # noqa: F401


# ---------------------------------------------------------------------------
# Integration: dispatch_paper with --iterative
# ---------------------------------------------------------------------------


class TestDispatchIterative:
    """Test iterative mode wired through agent.dispatch_paper."""

    def _mock_client(self):
        """Create a mock client that handles teacher, student, eval, and refine calls."""
        client = MagicMock()

        teacher_hint = {
            "problem_context": "How to extend conformal prediction.",
            "desirable_properties": ["Coverage guarantees"],
            "field_context": "Conformal inference.",
        }
        eval_data = {"composite_score": 3.5, "novelty_gap": "Missed weighting."}
        refine_data = {
            "refined_hint": {
                "problem_context": "How to handle distribution shift in conformal inference.",
                "desirable_properties": ["Coverage under shift"],
                "field_context": "Conformal inference + causal.",
            },
            "refinement_rationale": {
                "additions": [{"what": "distribution shift", "why": "student missed it"}],
                "removals": [],
            },
            "convergence_signal": {
                "hint_changed_substantially": False,
                "estimated_residual_captured": 0.9,
                "recommendation": "stop",
            },
        }

        def mock_create(**kwargs):
            resp = MagicMock()
            system = kwargs.get("system", "") or kwargs.get("instructions", "")

            if "conceptual residual" in system.lower() or "iterative reconstruction" in system.lower():
                text = f"```json\n{json.dumps(refine_data)}\n```"
            elif "evaluate" in system.lower() or "scoring" in system.lower():
                text = f"```json\n{json.dumps(eval_data)}\n```"
            elif "teacher" in system.lower() and "extract" in system.lower():
                text = f"```json\n{json.dumps(teacher_hint)}\n```"
            else:
                text = "# Reconstruction\n\nWe propose conformal prediction under shift."

            resp.output_text = text
            block = MagicMock()
            block.text = text
            resp.content = [block]
            usage = MagicMock()
            usage.input_tokens = 500
            usage.output_tokens = 200
            resp.usage = usage
            resp.id = "mock-id"
            return resp

        client.responses.create = mock_create
        client.messages = MagicMock()
        client.messages.create = mock_create
        return client

    def test_dispatch_iterative_abstract(self, tmp_path):
        """dispatch_paper with iterative=True produces iterative output."""
        from agent import dispatch_paper, load_references

        client = self._mock_client()
        refs = load_references()

        with patch("infra.pdf_utils.extract_text_from_pdf", return_value="Mock paper text." * 100):
            result = dispatch_paper(
                client=client,
                paper_url="https://arxiv.org/abs/2006.06138",
                refs=refs,
                student_model="gpt-4o",
                teacher_model="gpt-5.4",
                modes=["abstract"],
                output_dir=tmp_path,
                conditions=["with_refs"],
                iterative=True,
                max_rounds=3,
            )

        wr = result["conditions"]["with_refs"]["abstract"]
        assert wr["status"] == "success"
        assert wr["iterative"] is True
        assert wr["total_rounds"] >= 2
        assert "score_trajectory" in wr
        assert "final_hint" in wr

        # Output file should mention iterative
        output_path = tmp_path / "2006.06138" / "with_refs" / "abstract" / "output.md"
        assert output_path.exists()
        text = output_path.read_text()
        assert "iterative" in text.lower()

        # Iterative artifacts should exist
        iter_dir = tmp_path / "2006.06138" / "with_refs" / "abstract" / "_iterative"
        assert (iter_dir / "iterative_result.json").exists()

    def test_dispatch_iterative_problem_method(self, tmp_path):
        """dispatch_paper with iterative=True works for problem_method mode."""
        from agent import dispatch_paper, load_references

        client = self._mock_client()
        refs = load_references()

        with patch("infra.pdf_utils.extract_text_from_pdf", return_value="Mock paper text." * 100):
            result = dispatch_paper(
                client=client,
                paper_url="https://arxiv.org/abs/2006.06138",
                refs=refs,
                student_model="gpt-4o",
                teacher_model="gpt-5.4",
                modes=["problem_method"],
                output_dir=tmp_path,
                conditions=["with_refs"],
                iterative=True,
                max_rounds=3,
            )

        pm = result["conditions"]["with_refs"]["problem_method"]
        assert pm["status"] == "success"
        assert pm["iterative"] is True

    def test_dispatch_iterative_both_conditions(self, tmp_path):
        """Both conditions work with iterative mode."""
        from agent import dispatch_paper, load_references

        client = self._mock_client()
        refs = load_references()

        with patch("infra.pdf_utils.extract_text_from_pdf", return_value="Mock paper text." * 100):
            result = dispatch_paper(
                client=client,
                paper_url="https://arxiv.org/abs/2006.06138",
                refs=refs,
                student_model="gpt-4o",
                teacher_model="gpt-5.4",
                modes=["abstract"],
                output_dir=tmp_path,
                conditions=["with_refs", "no_refs"],
                iterative=True,
                max_rounds=3,
            )

        for cond in ["with_refs", "no_refs"]:
            assert cond in result["conditions"]
            info = result["conditions"][cond]["abstract"]
            assert info["status"] == "success"
            assert info["iterative"] is True

    def test_dispatch_iterative_summary(self, tmp_path):
        """Summary writer handles iterative results."""
        from agent import dispatch_paper, write_dispatch_summary, load_references

        client = self._mock_client()
        refs = load_references()

        with patch("infra.pdf_utils.extract_text_from_pdf", return_value="Mock paper text." * 100):
            result = dispatch_paper(
                client=client,
                paper_url="https://arxiv.org/abs/2006.06138",
                refs=refs,
                student_model="gpt-4o",
                teacher_model="gpt-5.4",
                modes=["abstract"],
                output_dir=tmp_path,
                conditions=["with_refs"],
                iterative=True,
                max_rounds=3,
            )

        write_dispatch_summary([result], tmp_path, "gpt-4o", "gpt-5.4")
        summary_path = tmp_path / "SUMMARY.md"
        assert summary_path.exists()
        text = summary_path.read_text()
        assert "Iterative" in text
        assert "2006.06138" in text

    def test_dispatch_non_iterative_unchanged(self, tmp_path):
        """Non-iterative dispatch still works as before."""
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
                iterative=False,
            )

        wr = result["conditions"]["with_refs"]["abstract"]
        assert wr["status"] == "success"
        assert "iterative" not in wr


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


class TestEvalModelParam:
    """Test the eval_model parameter for cheaper evaluation scoring."""

    def _mock_client(self):
        """Create mock client that tracks which model is used per call."""
        client = MagicMock()

        teacher_hint = {
            "problem_context": "Test problem.",
            "desirable_properties": ["Coverage"],
            "field_context": "Test field.",
        }
        eval_data = {
            "composite_score": 3.5,
            "novelty_gap": "Test gap.",
            "scores": {"problem_understanding": 3, "technical_depth": 3,
                       "novelty_alignment": 4, "writing_quality": 4, "completeness": 3},
        }
        refine_data = {
            "refined_hint": teacher_hint,
            "refinement_rationale": {"additions": [], "removals": []},
            "convergence_signal": {
                "hint_changed_substantially": False,
                "estimated_residual_captured": 0.9,
                "recommendation": "stop",
            },
        }

        call_log = []

        def mock_create(**kwargs):
            resp = MagicMock()
            model = kwargs.get("model", "unknown")
            system = kwargs.get("system", "") or kwargs.get("instructions", "")

            if "conceptual residual" in system.lower() or "iterative reconstruction" in system.lower():
                call_log.append(("refine", model))
                text = f"```json\n{json.dumps(refine_data)}\n```"
            elif "evaluate" in system.lower() or "scoring" in system.lower():
                call_log.append(("evaluate", model))
                text = f"```json\n{json.dumps(eval_data)}\n```"
            else:
                call_log.append(("student", model))
                text = "# Reconstruction\n\nTest output."

            resp.output_text = text
            block = MagicMock()
            block.text = text
            resp.content = [block]
            usage = MagicMock()
            usage.input_tokens = 100
            usage.output_tokens = 50
            resp.usage = usage
            resp.id = "mock-resp-id"
            return resp

        client.responses.create = mock_create
        client.messages = MagicMock()
        client.messages.create = mock_create
        client.call_log = call_log
        return client

    def test_eval_model_used_in_iterative(self, tmp_path):
        """Verify eval_model is passed to evaluate_reconstruction, not teacher_model."""
        from infra.iterative import run_iterative_refinement

        client = self._mock_client()

        def mock_student(cl, model, mode, hint, refs, audit):
            return "Test student output."

        result = run_iterative_refinement(
            client=client,
            student_model="test-student",
            teacher_model="test-teacher-opus",
            mode="abstract",
            initial_hint={"problem_context": "Test.", "desirable_properties": [], "field_context": ""},
            refs_text="Refs.",
            paper_text="Paper text.",
            paper_id="test",
            condition="with_refs",
            run_student_fn=mock_student,
            max_rounds=3,
            output_dir=tmp_path,
            eval_model="test-eval-sonnet",
        )

        assert result.total_rounds >= 2
        # All evaluate calls should use the eval model, not the teacher model
        eval_calls = [(t, m) for t, m in client.call_log if t == "evaluate"]
        refine_calls = [(t, m) for t, m in client.call_log if t == "refine"]
        assert len(eval_calls) > 0
        for call_type, model in eval_calls:
            assert model == "test-eval-sonnet", f"Eval used {model}, expected test-eval-sonnet"
        for call_type, model in refine_calls:
            assert model == "test-teacher-opus", f"Refine used {model}, expected test-teacher-opus"

    def test_eval_model_defaults_to_teacher(self, tmp_path):
        """When eval_model is None, evaluate uses teacher_model."""
        from infra.iterative import run_iterative_refinement

        client = self._mock_client()

        def mock_student(cl, model, mode, hint, refs, audit):
            return "Test student output."

        result = run_iterative_refinement(
            client=client,
            student_model="test-student",
            teacher_model="test-teacher",
            mode="abstract",
            initial_hint={"problem_context": "Test.", "desirable_properties": [], "field_context": ""},
            refs_text="Refs.",
            paper_text="Paper text.",
            paper_id="test",
            condition="with_refs",
            run_student_fn=mock_student,
            max_rounds=3,
            output_dir=tmp_path,
            # eval_model omitted — should default to teacher_model
        )

        eval_calls = [(t, m) for t, m in client.call_log if t == "evaluate"]
        assert len(eval_calls) > 0
        for call_type, model in eval_calls:
            assert model == "test-teacher"


class TestPaperContextSeed:
    """Test paper_context_seed_id parameter for cross-mode context sharing."""

    def test_seed_id_passed_to_eval_calls(self, tmp_path):
        """Verify seed ID is used as previous_response_id for eval calls."""
        from infra.iterative import run_iterative_refinement

        client = MagicMock()
        prev_ids_seen = []

        eval_data = {"composite_score": 3.5, "novelty_gap": "gap"}
        refine_data = {
            "refined_hint": {"problem_context": "p", "desirable_properties": [], "field_context": ""},
            "refinement_rationale": {"additions": [], "removals": []},
            "convergence_signal": {"hint_changed_substantially": False,
                                   "estimated_residual_captured": 0.9,
                                   "recommendation": "stop"},
        }

        def mock_create(**kwargs):
            resp = MagicMock()
            system = kwargs.get("system", "") or kwargs.get("instructions", "")
            prev_id = kwargs.get("previous_response_id")
            if prev_id is not None:
                prev_ids_seen.append(prev_id)

            if "conceptual residual" in system.lower() or "iterative reconstruction" in system.lower():
                text = f"```json\n{json.dumps(refine_data)}\n```"
            elif "evaluate" in system.lower() or "scoring" in system.lower():
                text = f"```json\n{json.dumps(eval_data)}\n```"
            else:
                text = "Reconstruction output."

            resp.output_text = text
            block = MagicMock()
            block.text = text
            resp.content = [block]
            usage = MagicMock()
            usage.input_tokens = 100
            usage.output_tokens = 50
            resp.usage = usage
            resp.id = f"resp-{len(prev_ids_seen)}"
            return resp

        client.responses.create = mock_create
        client.messages = MagicMock()
        client.messages.create = mock_create

        def mock_student(cl, model, mode, hint, refs, audit):
            return "Student output."

        result = run_iterative_refinement(
            client=client,
            student_model="s",
            teacher_model="t",
            mode="abstract",
            initial_hint={"problem_context": "p", "desirable_properties": [], "field_context": ""},
            refs_text="refs",
            paper_text="paper",
            paper_id="test",
            condition="with_refs",
            run_student_fn=mock_student,
            max_rounds=3,
            output_dir=tmp_path,
            paper_context_seed_id="seed-abc-123",
        )

        assert result.total_rounds >= 2
        # The seed ID should appear in prev_ids_seen (passed to eval and refine calls)
        assert "seed-abc-123" in prev_ids_seen

    def test_no_seed_works(self, tmp_path):
        """Without seed, prev_response_id is None (backward compat)."""
        from infra.iterative import run_iterative_refinement

        client = MagicMock()

        eval_data = {"composite_score": 3.5, "novelty_gap": "gap"}
        refine_data = {
            "refined_hint": {"problem_context": "p", "desirable_properties": [], "field_context": ""},
            "refinement_rationale": {"additions": [], "removals": []},
            "convergence_signal": {"hint_changed_substantially": False,
                                   "estimated_residual_captured": 0.9,
                                   "recommendation": "stop"},
        }

        def mock_create(**kwargs):
            resp = MagicMock()
            system = kwargs.get("system", "") or kwargs.get("instructions", "")
            if "conceptual residual" in system.lower() or "iterative reconstruction" in system.lower():
                text = f"```json\n{json.dumps(refine_data)}\n```"
            elif "evaluate" in system.lower() or "scoring" in system.lower():
                text = f"```json\n{json.dumps(eval_data)}\n```"
            else:
                text = "Output."
            resp.output_text = text
            block = MagicMock()
            block.text = text
            resp.content = [block]
            usage = MagicMock()
            usage.input_tokens = 100
            usage.output_tokens = 50
            resp.usage = usage
            resp.id = "resp-1"
            return resp

        client.responses.create = mock_create
        client.messages = MagicMock()
        client.messages.create = mock_create

        def mock_student(cl, model, mode, hint, refs, audit):
            return "Student output."

        # No seed, no eval_model — pure backward compat
        result = run_iterative_refinement(
            client=client,
            student_model="s",
            teacher_model="t",
            mode="abstract",
            initial_hint={"problem_context": "p", "desirable_properties": [], "field_context": ""},
            refs_text="refs",
            paper_text="paper",
            paper_id="test",
            condition="with_refs",
            run_student_fn=mock_student,
            max_rounds=3,
            output_dir=tmp_path,
        )
        assert result.total_rounds >= 2


class TestParallelModes:
    """Test --parallel-modes execution path in dispatch_paper."""

    def _mock_client(self):
        client = MagicMock()
        teacher_hint = {
            "problem_context": "Test.", "desirable_properties": [], "field_context": "",
        }
        eval_data = {"composite_score": 3.5, "novelty_gap": "Gap."}
        refine_data = {
            "refined_hint": teacher_hint,
            "refinement_rationale": {"additions": [], "removals": []},
            "convergence_signal": {"hint_changed_substantially": False,
                                   "estimated_residual_captured": 0.9,
                                   "recommendation": "stop"},
        }

        def mock_create(**kwargs):
            resp = MagicMock()
            system = kwargs.get("system", "") or kwargs.get("instructions", "")
            if "conceptual residual" in system.lower() or "iterative reconstruction" in system.lower():
                text = f"```json\n{json.dumps(refine_data)}\n```"
            elif "evaluate" in system.lower() or "scoring" in system.lower():
                text = f"```json\n{json.dumps(eval_data)}\n```"
            elif "teacher" in system.lower() and "extract" in system.lower():
                text = f"```json\n{json.dumps(teacher_hint)}\n```"
            else:
                text = "# Reconstruction\nTest."
            resp.output_text = text
            block = MagicMock()
            block.text = text
            resp.content = [block]
            usage = MagicMock()
            usage.input_tokens = 100
            usage.output_tokens = 50
            resp.usage = usage
            resp.id = "mock-id"
            return resp

        client.responses.create = mock_create
        client.messages = MagicMock()
        client.messages.create = mock_create
        return client

    def test_parallel_modes_produces_same_results(self, tmp_path):
        """parallel_modes=True should produce the same mode results as sequential."""
        from agent import dispatch_paper, load_references

        client = self._mock_client()
        refs = load_references()
        modes = ["abstract", "problem"]

        with patch("infra.pdf_utils.extract_text_from_pdf", return_value="Mock paper." * 100):
            result = dispatch_paper(
                client=client,
                paper_url="https://arxiv.org/abs/2006.06138",
                refs=refs,
                student_model="gpt-4o",
                teacher_model="gpt-5.4",
                modes=modes,
                output_dir=tmp_path,
                conditions=["with_refs"],
                iterative=True,
                max_rounds=3,
                parallel_modes=True,
            )

        wr = result["conditions"]["with_refs"]
        # Both modes should have completed successfully
        for mode in modes:
            assert mode in wr, f"Mode {mode} missing from results"
            assert wr[mode]["status"] == "success"
            assert wr[mode]["iterative"] is True


class TestCreateContextSeed:
    """Test create_context_seed function."""

    def test_anthropic_returns_none(self):
        """Anthropic backend should return None (cache_control handles it)."""
        from infra.llm import create_context_seed
        from infra.audit import AuditLog

        # Mock Anthropic client
        client = MagicMock()
        client.__class__.__module__ = "anthropic._client"

        audit = AuditLog(paper_id="test", paper_url="", reconstruction_type="seed",
                         student_model="s", teacher_model="t", config={})

        result = create_context_seed(client, "opus", "Paper text.", audit, "test")
        assert result is None

    def test_openai_returns_response_id(self):
        """OpenAI backend should return a response ID."""
        from infra.llm import create_context_seed
        from infra.audit import AuditLog

        client = MagicMock()
        client.__class__.__module__ = "openai._client"

        resp = MagicMock()
        resp.id = "resp_seed_12345"
        usage = MagicMock()
        usage.input_tokens = 8000
        usage.output_tokens = 5
        resp.usage = usage
        client.responses.create.return_value = resp

        audit = AuditLog(paper_id="test", paper_url="", reconstruction_type="seed",
                         student_model="s", teacher_model="t", config={})

        result = create_context_seed(client, "gpt-5.4", "Paper text." * 1000, audit, "test")
        assert result == "resp_seed_12345"
        assert len(audit.steps) == 1
        assert audit.steps[0].step_name == "create_context_seed"


class TestCLIIterative:
    def test_iterative_flag_in_help(self):
        import subprocess
        result = subprocess.run(
            ["python", str(ROOT / "agent.py"), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "--iterative" in result.stdout
        assert "--max-rounds" in result.stdout
        assert "--eval-model" in result.stdout
        assert "--parallel-modes" in result.stdout
