"""Iterative hint-refinement engine for conceptual residual extraction.

Implements the iterative teacher-student workflow:
  1. Teacher gives initial hint -> Student generates -> Teacher evaluates
  2. Teacher refines hint based on evaluation -> Fresh student regenerates
  3. Repeat until the hint converges (= conceptual residual)

Key design principle: the iteration modifies the TEACHER'S HINT, not the
student's output.  Each round the student is MEMORYLESS (regenerates from
scratch).  The teacher retains memory of the entire adjustment history.
"""

from __future__ import annotations

import json
import copy
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from infra.audit import AuditLog
from infra.llm import llm_call
from infra.evaluate import evaluate_reconstruction, _parse_eval

SCRIPT_DIR = Path(__file__).parent.parent
PROMPTS_DIR = SCRIPT_DIR / "prompts"

# Default configuration
DEFAULT_MAX_ROUNDS = 5
CONVERGENCE_SCORE_THRESHOLD = 0.3   # stop if composite score delta < this
MIN_ROUNDS = 3                       # always run at least 3 rounds

# Publication-quality configuration
PUB_QUALITY_SCORE = 4.0             # must reach this score to converge
PUB_QUALITY_STABLE_ROUNDS = 2      # must be stable at this level for N rounds


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RoundRecord:
    """One iteration round of the teacher-student-evaluate-refine cycle."""
    round_number: int
    hint: dict                        # hint given to student this round
    student_output: str = ""
    evaluation: dict = field(default_factory=dict)
    refined_hint: dict | None = None  # hint after refinement (None for last round)
    refinement_rationale: dict = field(default_factory=dict)
    convergence_signal: dict = field(default_factory=dict)


@dataclass
class IterativeResult:
    """Complete result of an iterative refinement run."""
    paper_id: str
    mode: str
    condition: str
    initial_hint: dict
    rounds: list[RoundRecord] = field(default_factory=list)
    converged: bool = False
    convergence_reason: str = ""
    final_hint: dict = field(default_factory=dict)
    total_rounds: int = 0

    def score_trajectory(self) -> list[float]:
        """Return composite scores across rounds."""
        scores = []
        for r in self.rounds:
            s = r.evaluation.get("composite_score", 0)
            try:
                scores.append(float(s))
            except (TypeError, ValueError):
                scores.append(0.0)
        return scores

    def best_round(self) -> RoundRecord | None:
        """Return the round with the highest composite score."""
        if not self.rounds:
            return None
        scores = self.score_trajectory()
        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        return self.rounds[best_idx]

    def hint_trajectory(self) -> list[dict]:
        """Return the sequence of hints across rounds."""
        return [r.hint for r in self.rounds]

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict."""
        best = self.best_round()
        scores = self.score_trajectory()
        return {
            "paper_id": self.paper_id,
            "mode": self.mode,
            "condition": self.condition,
            "initial_hint": self.initial_hint,
            "rounds": [asdict(r) for r in self.rounds],
            "converged": self.converged,
            "convergence_reason": self.convergence_reason,
            "final_hint": self.final_hint,
            "total_rounds": self.total_rounds,
            "score_trajectory": scores,
            "best_score": max(scores) if scores else 0,
            "best_round_number": best.round_number if best else 0,
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, default=str),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "IterativeResult":
        data = json.loads(path.read_text(encoding="utf-8"))
        rounds = [
            RoundRecord(**{k: v for k, v in r.items()})
            for r in data.pop("rounds", [])
        ]
        # Remove computed fields that are not constructor args
        for key in ("score_trajectory", "best_score", "best_round_number"):
            data.pop(key, None)
        result = cls(**{k: v for k, v in data.items() if k != "rounds"})
        result.rounds = rounds
        return result


# ---------------------------------------------------------------------------
# Teacher hint refinement
# ---------------------------------------------------------------------------

def refine_hint(
    client,
    teacher_model: str,
    paper_text: str,
    current_hint: dict,
    student_output: str,
    evaluation: dict,
    round_history: list[RoundRecord],
    audit: AuditLog,
    previous_response_id: str | None = None,
) -> tuple[dict, dict, dict, str]:
    """Teacher refines the hint based on student performance.

    Returns (refined_hint, refinement_rationale, convergence_signal).
    """
    prompt = (PROMPTS_DIR / "teacher_refine_hint.txt").read_text()

    # Build history summary for teacher memory
    history_parts = []
    for r in round_history:
        score = r.evaluation.get("composite_score", "?")
        gap = r.evaluation.get("novelty_gap", "N/A")
        rationale = r.refinement_rationale
        additions = rationale.get("additions", []) if rationale else []
        removals = rationale.get("removals", []) if rationale else []
        history_parts.append(
            f"### Round {r.round_number}\n"
            f"- Composite score: {score}\n"
            f"- Novelty gap: {gap}\n"
            f"- Hint additions: {json.dumps(additions, default=str)}\n"
            f"- Hint removals: {json.dumps(removals, default=str)}\n"
        )
    history_text = "\n".join(history_parts) if history_parts else "This is the first refinement round."

    # Paper text is stable across all rounds — cache it as prefix
    paper_prefix = f"## Original paper (first 30k chars)\n\n{paper_text[:30_000]}"
    user_msg = (
        f"## Current hint given to student\n\n"
        f"```json\n{json.dumps(current_hint, indent=2)}\n```\n\n"
        f"## Student's reconstruction output\n\n"
        f"{student_output[:15_000]}\n\n"
        f"## Teacher's evaluation of student output\n\n"
        f"```json\n{json.dumps(evaluation, indent=2, default=str)}\n```\n\n"
        f"## Refinement history\n\n"
        f"{history_text}\n"
    )

    round_num = len(round_history) + 1
    print(f"  [refine] Round {round_num}: refining hint with {teacher_model}...")

    response, resp_id = llm_call(
        client, teacher_model,
        system=prompt,
        user=user_msg,
        audit=audit,
        step_name=f"refine_hint_round_{round_num}",
        max_tokens=2048,
        temperature=0.3,
        cache_user_prefix=paper_prefix,
        previous_response_id=previous_response_id,
    )

    parsed = _parse_refinement(response)
    refined_hint = parsed.get("refined_hint", current_hint)
    rationale = parsed.get("refinement_rationale", {})
    convergence = parsed.get("convergence_signal", {})

    return refined_hint, rationale, convergence, resp_id


def _parse_refinement(text: str) -> dict:
    """Parse teacher refinement response into structured dict."""
    import re
    # Try ```json block first
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Try outermost { ... }
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    # Fallback
    return {"parse_error": True, "raw": text[:1000]}


# ---------------------------------------------------------------------------
# Convergence detection
# ---------------------------------------------------------------------------

def check_convergence(
    rounds: list[RoundRecord],
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    score_threshold: float = CONVERGENCE_SCORE_THRESHOLD,
    pub_quality: bool = False,
) -> tuple[bool, str]:
    """Check whether the iterative process should stop.

    Returns (should_stop, reason).

    When pub_quality=True, enforces stricter convergence:
    - Score must reach PUB_QUALITY_SCORE (4.0)
    - Score must be stable at that level for PUB_QUALITY_STABLE_ROUNDS
    - Teacher "stop" recommendations are downgraded to suggestions
      unless the score is already at publication level

    Guards against premature convergence:
    - Never stops before MIN_ROUNDS
    - Never stops when the latest score regressed below the best score
      (regression = noise from memoryless student, not a convergence signal)
    """
    n = len(rounds)

    # Hard cap (always respected, even in pub-quality mode)
    if n >= max_rounds:
        return True, f"reached max rounds ({max_rounds})"

    # Need at least MIN_ROUNDS
    if n < MIN_ROUNDS:
        return False, "need more rounds"

    # Compute score trajectory
    scores = []
    for r in rounds:
        try:
            scores.append(float(r.evaluation.get("composite_score", 0)))
        except (TypeError, ValueError):
            scores.append(0.0)

    # Score regression guard: if the latest score is below the best,
    # do NOT converge — the student may have had a bad roll. The hint
    # refinement should continue to give the student another chance.
    if len(scores) >= 2:
        best_score = max(scores[:-1])
        if scores[-1] < best_score - 0.1:
            return False, f"score regressed ({scores[-1]:.1f} < best {best_score:.1f})"

    latest = rounds[-1]
    signal = latest.convergence_signal

    # --- Publication-quality gate ---
    if pub_quality:
        recent_scores = scores[-PUB_QUALITY_STABLE_ROUNDS:] if len(scores) >= PUB_QUALITY_STABLE_ROUNDS else scores
        all_at_pub_level = all(s >= PUB_QUALITY_SCORE for s in recent_scores)
        stable = (
            len(recent_scores) >= PUB_QUALITY_STABLE_ROUNDS
            and max(recent_scores) - min(recent_scores) < score_threshold
        )

        if all_at_pub_level and stable:
            return True, (
                f"publication quality reached "
                f"(scores {' -> '.join(f'{s:.1f}' for s in recent_scores)} "
                f"all >= {PUB_QUALITY_SCORE})"
            )

        # In pub-quality mode, don't stop early just because teacher says so
        # or because scores plateaued below the target
        if not all_at_pub_level:
            return False, (
                f"below publication quality "
                f"(latest={scores[-1]:.1f}, need>={PUB_QUALITY_SCORE})"
            )

    # Check teacher's own convergence signal
    if signal.get("recommendation") == "stop":
        return True, "teacher recommended stop"

    # Check score plateau
    if len(scores) >= 2:
        delta = abs(scores[-1] - scores[-2])
        if delta < score_threshold:
            # Also check if hint barely changed
            if not signal.get("hint_changed_substantially", True):
                return True, f"score plateau (delta={delta:.2f}) and hint stable"

    # Check if teacher says residual is well-captured
    est = signal.get("estimated_residual_captured", 0)
    try:
        if float(est) >= 0.85:
            return True, f"teacher estimates {est:.0%} residual captured"
    except (TypeError, ValueError):
        pass

    return False, "not yet converged"


# ---------------------------------------------------------------------------
# Main iterative loop
# ---------------------------------------------------------------------------

def run_iterative_refinement(
    client,
    student_model: str,
    teacher_model: str,
    mode: str,
    initial_hint: dict,
    refs_text: str,
    paper_text: str,
    paper_id: str,
    condition: str,
    run_student_fn,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    output_dir: Path | None = None,
    paper_context_seed_id: str | None = None,
    eval_model: str | None = None,
    resume_from: "IterativeResult | None" = None,
    pub_quality: bool = False,
) -> IterativeResult:
    """Run the full iterative hint-refinement loop.

    Args:
        run_student_fn: callable(client, model, mode, hint, refs_text, audit) -> str
            The student generation function (injected for testability).
        output_dir: If provided, save per-round artifacts here.
        paper_context_seed_id: (OpenAI) Response ID from create_context_seed().
            When provided, evaluate calls branch from this seed independently
            (each eval sees paper context but NOT other evals' outputs).
            Refine calls chain sequentially from each other (correct — the
            teacher needs history of prior refinements).
            For Anthropic, pass None — cache_control handles context sharing.
        resume_from: If provided, resume from an existing IterativeResult.
            Existing rounds are preserved, and refinement continues from the
            final hint. Saves cost by not re-running converged rounds.
        pub_quality: If True, use stricter publication-quality convergence
            criteria (score >= 4.0, stable for 2+ rounds).

    Returns an IterativeResult with the full trajectory.
    """
    # Resolve eval model — default to teacher (Opus).
    # Using a cheaper model (Sonnet) for eval reduces cost ~41%.
    eval_model = eval_model or teacher_model

    # Resume from existing result or start fresh
    if resume_from is not None:
        result = copy.deepcopy(resume_from)
        result.converged = False
        result.convergence_reason = ""
        current_hint = copy.deepcopy(resume_from.final_hint)
        start_round = resume_from.total_rounds + 1
        print(f"\n  [resume] Continuing from round {start_round} "
              f"(previous: {resume_from.total_rounds} rounds, "
              f"scores: {' -> '.join(f'{s:.1f}' for s in resume_from.score_trajectory())})")
    else:
        result = IterativeResult(
            paper_id=paper_id,
            mode=mode,
            condition=condition,
            initial_hint=copy.deepcopy(initial_hint),
        )
        current_hint = copy.deepcopy(initial_hint)
        start_round = 1

    # Response IDs for stateful chaining (OpenAI Responses API).
    #
    # IMPORTANT correctness constraint:
    # - Evaluate calls BRANCH from the paper_context_seed (independent).
    #   Each eval sees the paper but NOT other rounds' eval outputs.
    #   This prevents the evaluator from being biased by prior scores.
    # - Refine calls CHAIN sequentially (refine_round_2 from refine_round_1).
    #   The teacher needs full history of prior refinements.
    eval_seed_id: str | None = paper_context_seed_id
    refine_chain_id: str | None = paper_context_seed_id

    for round_num in range(start_round, max_rounds + 1):
        print(f"\n  {'~'*40}")
        print(f"  Iterative round {round_num}/{max_rounds} [{mode}]")
        print(f"  {'~'*40}")

        record = RoundRecord(
            round_number=round_num,
            hint=copy.deepcopy(current_hint),
        )

        # 1. Student generates (memoryless — fresh each round)
        student_audit = AuditLog(
            paper_id=paper_id,
            paper_url="",
            reconstruction_type=f"iterative/{condition}/{mode}/round_{round_num}/student",
            student_model=student_model,
            teacher_model=teacher_model,
            config={"round": round_num, "condition": condition},
        )

        try:
            student_output = run_student_fn(
                client, student_model, mode, current_hint, refs_text, student_audit,
            )
            student_audit.mark_finished()
        except Exception as exc:
            student_audit.mark_finished()
            print(f"  [round {round_num}] Student failed: {exc}")
            record.student_output = f"ERROR: {exc}"
            record.evaluation = {"composite_score": 0, "error": str(exc)}
            result.rounds.append(record)
            break

        record.student_output = student_output

        # 2. Teacher evaluates
        eval_audit = AuditLog(
            paper_id=paper_id,
            paper_url="",
            reconstruction_type=f"iterative/{condition}/{mode}/round_{round_num}/eval",
            student_model=student_model,
            teacher_model=teacher_model,
            config={"round": round_num, "condition": condition},
        )

        try:
            evaluation, _eval_resp_id = evaluate_reconstruction(
                client, eval_model, paper_text, student_output,
                mode, condition, eval_audit,
                previous_response_id=eval_seed_id,
            )
            # NOTE: we do NOT chain eval calls (eval_seed_id stays constant).
            # Each eval branches independently from the paper-context seed.
            # This prevents the evaluator from seeing prior rounds' scores.
            eval_audit.mark_finished()
        except Exception as exc:
            eval_audit.mark_finished()
            print(f"  [round {round_num}] Evaluation failed: {exc}")
            evaluation = {"composite_score": 0, "error": str(exc)}

        record.evaluation = evaluation
        score = evaluation.get("composite_score", "?")
        gap = evaluation.get("novelty_gap", "N/A")
        print(f"  [round {round_num}] Score: {score} | Gap: {gap[:80] if isinstance(gap, str) else gap}")

        # Save round artifacts if output_dir provided
        if output_dir:
            round_dir = output_dir / f"round_{round_num}"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "hint.json").write_text(
                json.dumps(current_hint, indent=2, default=str), encoding="utf-8")
            (round_dir / "output.md").write_text(student_output, encoding="utf-8")
            (round_dir / "eval.json").write_text(
                json.dumps(evaluation, indent=2, default=str), encoding="utf-8")
            student_audit.save(round_dir / "student_audit.json")
            eval_audit.save(round_dir / "eval_audit.json")

        # 3. Check convergence before refining (saves an LLM call on last round)
        result.rounds.append(record)
        should_stop, reason = check_convergence(
            result.rounds, max_rounds=max_rounds, pub_quality=pub_quality,
        )

        if should_stop and round_num >= MIN_ROUNDS:
            result.converged = True
            result.convergence_reason = reason
            print(f"  [converged] {reason}")
            break

        # 4. Teacher refines hint (teacher retains full history)
        refine_audit = AuditLog(
            paper_id=paper_id,
            paper_url="",
            reconstruction_type=f"iterative/{condition}/{mode}/round_{round_num}/refine",
            student_model=student_model,
            teacher_model=teacher_model,
            config={"round": round_num, "condition": condition},
        )

        try:
            refined_hint, rationale, convergence, refine_resp_id = refine_hint(
                client, teacher_model, paper_text,
                current_hint, student_output, evaluation,
                result.rounds, refine_audit,
                previous_response_id=refine_chain_id,
            )
            refine_chain_id = refine_resp_id  # chain next round's refine
            refine_audit.mark_finished()

            record.refined_hint = refined_hint
            record.refinement_rationale = rationale
            record.convergence_signal = convergence

            if output_dir:
                round_dir = output_dir / f"round_{round_num}"
                (round_dir / "refined_hint.json").write_text(
                    json.dumps(refined_hint, indent=2, default=str), encoding="utf-8")
                (round_dir / "refinement.json").write_text(
                    json.dumps({"rationale": rationale, "convergence": convergence},
                               indent=2, default=str), encoding="utf-8")
                refine_audit.save(round_dir / "refine_audit.json")

            # Re-check convergence with teacher signal
            should_stop, reason = check_convergence(
                result.rounds, max_rounds=max_rounds, pub_quality=pub_quality,
            )
            if should_stop and round_num >= MIN_ROUNDS:
                result.converged = True
                result.convergence_reason = reason
                print(f"  [converged] {reason}")
                break

            # Advance to refined hint for next round
            current_hint = refined_hint
            additions = rationale.get("additions", [])
            removals = rationale.get("removals", [])
            print(f"  [refine] +{len(additions)} additions, -{len(removals)} removals")

        except Exception as exc:
            refine_audit.mark_finished()
            print(f"  [round {round_num}] Refinement failed: {exc}")
            record.refinement_rationale = {"error": str(exc)}
            # Continue with same hint
    else:
        # Loop completed without break
        if not result.converged:
            result.convergence_reason = f"reached max rounds ({max_rounds})"

    # Set final state
    result.total_rounds = len(result.rounds)
    result.final_hint = copy.deepcopy(current_hint)

    # Save summary if output_dir provided
    if output_dir:
        result.save(output_dir / "iterative_result.json")

    scores = result.score_trajectory()
    best = result.best_round()
    print(f"\n  Iterative refinement complete: {result.total_rounds} rounds")
    print(f"  Score trajectory: {' -> '.join(f'{s:.1f}' for s in scores)}")
    if best:
        print(f"  Best score: {max(scores):.1f} (round {best.round_number})")
    print(f"  Converged: {result.converged} ({result.convergence_reason})")

    return result
