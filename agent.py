#!/usr/bin/env python3
"""agent-staged-reconstruct: multi-mode teacher-student paper reconstruction.

Dispatches 6 parallel reconstruction experiments per test paper:
  1. abstract          — reconstruct the paper's abstract
  2. mindmap           — generate an idea mindmap for the paper
  3. problem           — reconstruct the problem formulation section
  4. problem_method    — reconstruct problem formulation + methodology
  5. full_guided       — reconstruct full paper using a provided skeleton
  6. full_freestyle    — reconstruct full paper with free structure

Teacher model (gpt-5.4): reads the full paper, extracts a problem-context hint
  (no solution leakage). Has web search available for reference enrichment.
Student model (gpt-4o): receives only the hint + provided reference texts.
  NO web search, NO tools — pure reasoning from given context.

Output: timestamped dispatch folder with per-paper, per-mode subfolders,
each containing the student output (.md) and full audit trail (.json).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IMPL_ID = "staged_reconstruct_v0_6_0"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RECONSTRUCTION_MODES = [
    "abstract",
    "mindmap",
    "problem",
    "problem_method",
    "full_guided",
    "full_freestyle",
]

PROMPT_FILES = {
    "abstract": "student_abstract.txt",
    "mindmap": "student_mindmap.txt",
    "problem": "student_problem_formulation.txt",
    "problem_method": "student_problem_and_method.txt",
    "full_guided": "student_full_guided.txt",
    "full_freestyle": "student_full_freestyle.txt",
}

# Token limits scale with reconstruction complexity
MAX_TOKENS = {
    "abstract": 1024,
    "mindmap": 2048,
    "problem": 3072,
    "problem_method": 6144,
    "full_guided": 8192,
    "full_freestyle": 8192,
}

SCRIPT_DIR = Path(__file__).parent
PROMPTS_DIR = SCRIPT_DIR / "prompts"
DATA_DIR = SCRIPT_DIR / "data"

# Reference guidance modes — controls how the student engages with references.
# "directive" (single-shot): forces substantive engagement, as in v0.5.
# "neutral" (iterative): lets the student decide naturally; the teacher's
# iterative hint refinement handles reference utilization organically.
REFERENCE_GUIDANCE_DIRECTIVE = """\
## IMPORTANT: How to use references

If reference papers are provided above, you MUST engage with them substantively:
- Identify specific techniques, theorems, or frameworks from the references
  that could be adapted or extended to address the problem
- Build your approach ON TOP of what the references provide — don't just
  cite them in passing
- If a reference provides a framework (e.g., conformal prediction, kernel methods),
  use that framework as your starting point and extend it for this problem
- If no references are provided, rely on your own knowledge of the field"""

REFERENCE_GUIDANCE_NEUTRAL = """\
## References note

Reference papers are provided above for context. Use them if and as you see \
fit — they may or may not be directly relevant to the core problem. Your \
reconstruction should reflect your own best judgment about how to address \
the problem, drawing on whatever knowledge (from references or otherwise) \
you find most useful."""

DEFAULT_STUDENT_MODEL = "gpt-4o"
DEFAULT_TEACHER_MODEL = "gpt-5.4"

# Claude model aliases for when using Anthropic backend
CLAUDE_MODELS = {
    "student": "claude-sonnet-4-20250514",
    "teacher": "claude-opus-4-20250514",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(backend: str = "auto"):
    """Create an LLM client based on the backend selection.

    'auto' tries OpenAI first, then Anthropic.
    """
    if backend in ("openai", "auto"):
        try:
            import openai
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                return openai.OpenAI(api_key=api_key), "openai"
            if backend == "openai":
                print("ERROR: OPENAI_API_KEY not set.", file=sys.stderr)
                sys.exit(1)
        except ImportError:
            if backend == "openai":
                print("ERROR: 'openai' package not installed.", file=sys.stderr)
                sys.exit(1)

    if backend in ("anthropic", "auto"):
        try:
            import anthropic
            # Prefer explicit API key (billed to user's API account, separate
            # rate limits from Claude.ai session token).
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                return anthropic.Anthropic(api_key=api_key), "anthropic"
            # Fallback: session token (Claude Code remote environment)
            token_candidates = [
                Path.home() / ".claude" / "remote" / ".session_ingress_token",
                Path("/home/claude/.claude/remote/.session_ingress_token"),
            ]
            token_path = next((p for p in token_candidates if p.exists()), None)
            if token_path is not None:
                auth_token = token_path.read_text().strip()
                return anthropic.Anthropic(auth_token=auth_token), "anthropic"
            if backend == "anthropic":
                print("ERROR: No Anthropic auth found.", file=sys.stderr)
                sys.exit(1)
        except ImportError:
            if backend == "anthropic":
                print("ERROR: 'anthropic' package not installed.", file=sys.stderr)
                sys.exit(1)

    print("ERROR: No LLM backend available. Install openai or anthropic.", file=sys.stderr)
    sys.exit(1)


def extract_paper_id(url: str) -> str:
    """Extract a filesystem-safe paper ID from a URL."""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+)", url)
    if m:
        return m.group(1)
    return url.rstrip("/").split("/")[-1].replace(".pdf", "")[:50]


def load_test_papers() -> list[dict]:
    """Load test papers from data/test_papers.ndjson."""
    path = DATA_DIR / "test_papers.ndjson"
    papers = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            papers.append(json.loads(line))
    return papers


def load_references() -> list[dict]:
    """Load user-provided references from data/references.json."""
    path = DATA_DIR / "references.json"
    return json.loads(path.read_text())


def _extract_json_block(text: str) -> Any:
    """Try to extract a JSON object from LLM output."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


# ---------------------------------------------------------------------------
# Teacher: extract problem context (full paper access, no solution leakage)
# ---------------------------------------------------------------------------

def run_teacher(client, model: str, paper_text: str, refs: list[dict],
                audit) -> dict:
    """Teacher reads the full paper and produces a problem-context hint.

    The teacher has access to the paper and references. It extracts a
    problem description that does NOT leak the solution approach.
    """
    from infra.llm import llm_call

    prompt = (PROMPTS_DIR / "teacher_extract.txt").read_text()

    # Build reference summary for teacher's awareness
    ref_summary = "\n".join(
        f"- {r.get('id', 'unknown')}: {r.get('title', 'untitled')} ({r.get('year', '?')})"
        for r in refs
    )

    user_msg = (
        f"## Paper full text (first 40k chars)\n\n"
        f"{paper_text[:40_000]}\n\n"
        f"## References the student will have access to\n\n{ref_summary}"
    )

    print(f"  [teacher] Extracting problem context with {model}...")
    response = llm_call(
        client, model,
        system=prompt,
        user=user_msg,
        audit=audit,
        step_name="teacher_extract",
        max_tokens=2048,
        temperature=0.3,  # Low temp for faithful extraction
    )

    hint = _extract_json_block(response)
    if hint is None:
        hint = {
            "problem_context": response[:2000],
            "desirable_properties": [],
            "field_context": "",
        }

    # Migrate legacy hint format (evaluation_criteria → desirable_properties)
    if "evaluation_criteria" in hint and "desirable_properties" not in hint:
        hint["desirable_properties"] = [hint.pop("evaluation_criteria")]
    # Drop legacy fields that leak info
    hint.pop("reference_guidance", None)
    hint.pop("domain_keywords", None)
    hint.pop("evaluation_criteria", None)

    print(f"  [teacher] Problem context extracted ({hint.get('problem_context', '')[:80]}...)")
    return hint


# ---------------------------------------------------------------------------
# Student: reconstruct from hint + references only (NO web search, NO tools)
# ---------------------------------------------------------------------------

def run_student(client, model: str, mode: str, hint: dict,
                refs_text: str, audit,
                reference_guidance: str | None = None) -> str:
    """Student reconstructs a specific artifact from hint + references.

    Student has NO access to the paper, NO web search, NO tools.
    Pure reasoning from the provided context.

    Args:
        reference_guidance: Controls how the student engages with references.
            None defaults to REFERENCE_GUIDANCE_DIRECTIVE (forced engagement).
            In iterative mode, REFERENCE_GUIDANCE_NEUTRAL is passed so the
            teacher's hint refinement handles reference utilization organically.
    """
    from infra.llm import llm_call

    if reference_guidance is None:
        reference_guidance = REFERENCE_GUIDANCE_DIRECTIVE

    prompt_file = PROMPT_FILES[mode]
    prompt_template = (PROMPTS_DIR / prompt_file).read_text()

    # Fill template — new format uses desirable_properties + field_context
    props = hint.get("desirable_properties", [])
    if isinstance(props, list):
        props_text = "\n".join(f"- {p}" for p in props) if props else "Not specified."
    else:
        props_text = str(props)

    field_ctx = hint.get("field_context", "")
    problem_ctx = hint.get("problem_context", "")
    if field_ctx:
        problem_ctx = f"{problem_ctx}\n\n**Field context:** {field_ctx}"

    # Support both old and new template placeholders
    filled = (
        prompt_template
        .replace("{problem_context}", problem_ctx)
        .replace("{evaluation_criteria}", props_text)
        .replace("{refs_text}", refs_text)
        .replace("{reference_guidance}", reference_guidance)
    )

    print(f"  [student/{mode}] Generating with {model} (max {MAX_TOKENS[mode]} tokens)...")
    response = llm_call(
        client, model,
        system=filled,
        user="Begin your reconstruction now.",
        audit=audit,
        step_name=f"student_{mode}",
        max_tokens=MAX_TOKENS[mode],
        temperature=0.7,  # Creative but grounded
    )

    print(f"  [student/{mode}] Generated {len(response):,} chars")
    return response


# ---------------------------------------------------------------------------
# Reference text preparation
# ---------------------------------------------------------------------------

def prepare_refs_text(refs: list[dict], max_chars_per_ref: int = 20_000) -> str:
    """Prepare reference texts for the student.

    Uses full text from data/pdfs/<id>.txt when available, falling back to
    abstracts from references.json. Full reference text is the student's
    legitimate knowledge — it's what they'd read before tackling the problem.
    """
    pdf_cache = DATA_DIR / "pdfs"
    parts = []
    for ref in refs:
        ref_id = ref.get("id", "unknown")
        title = ref.get("title", "untitled")
        abstract = ref.get("abstract", "")
        authors = ", ".join(ref.get("authors", []))
        year = ref.get("year", "?")
        venue = ref.get("venue", "")

        # Try to load full text from cache
        full_text = ""
        # Extract arxiv ID from ref id like "arxiv-1904.06019"
        arxiv_id = ref_id.replace("arxiv-", "") if ref_id.startswith("arxiv-") else ref_id
        txt_path = pdf_cache / f"{arxiv_id}.txt"
        if txt_path.exists():
            full_text = txt_path.read_text(encoding="utf-8")[:max_chars_per_ref]

        if full_text:
            block = (
                f"--- Reference: {ref_id} ---\n"
                f"Title: {title}\n"
                f"Authors: {authors}\n"
                f"Year: {year}\n"
                f"Venue: {venue}\n\n"
                f"Full text:\n{full_text}\n"
                f"--- End reference ---"
            )
        else:
            block = (
                f"--- Reference: {ref_id} ---\n"
                f"Title: {title}\n"
                f"Authors: {authors}\n"
                f"Year: {year}\n"
                f"Venue: {venue}\n"
                f"Abstract: {abstract}\n"
                f"--- End reference ---"
            )
        parts.append(block)

    return "\n\n".join(parts) if parts else "No references provided."


# ---------------------------------------------------------------------------
# Single paper dispatch
# ---------------------------------------------------------------------------

def dispatch_paper(
    client,
    paper_url: str,
    refs: list[dict],
    student_model: str,
    teacher_model: str,
    modes: list[str],
    output_dir: Path,
    paper_metadata: dict | None = None,
    conditions: list[str] | None = None,
    evaluate: bool = False,
    iterative: bool = False,
    max_rounds: int = 5,
) -> dict:
    """Run all reconstruction modes for a single paper under each condition.

    Args:
        paper_metadata: Optional dict with pre-loaded metadata (title, abstract,
            authors, etc.) from test_papers.ndjson. Used as fallback when PDF
            download fails.
        conditions: List of experimental conditions to run. Defaults to
            ["with_refs", "no_refs"]. Each condition gets its own subfolder.
            - "with_refs": student receives hint + reference texts
            - "no_refs":   student receives hint only (baseline)
        evaluate: If True, teacher evaluates each student output after generation.
        iterative: If True, run iterative hint-refinement loop per mode.
            Implies evaluate=True.
        max_rounds: Maximum iterative refinement rounds (default 5).

    Returns a summary dict with paths to all outputs.
    """
    if iterative:
        evaluate = True  # iterative implies evaluation
    from infra.audit import AuditLog
    from infra.pdf_utils import extract_text_from_pdf

    if conditions is None:
        conditions = ["with_refs", "no_refs"]

    # Resolve paper_id from URL or metadata
    if paper_metadata and paper_metadata.get("paper_id"):
        paper_id = paper_metadata["paper_id"]
    elif paper_url:
        paper_id = extract_paper_id(paper_url)
    else:
        paper_id = "unknown"

    paper_dir = output_dir / paper_id
    paper_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Paper: {paper_id} ({paper_url or 'no URL'})")
    print(f"Conditions: {', '.join(conditions)}")
    print(f"Evaluate: {evaluate}")
    print(f"{'='*60}")

    # Fetch paper text for teacher — try PDF first, fall back to embedded abstract
    print(f"  Fetching paper text...")
    paper_text = ""
    if paper_url:
        paper_text = extract_text_from_pdf(paper_url, max_chars=60_000)
    text_source = "pdf"
    if not paper_text and paper_metadata:
        title = paper_metadata.get("title", "")
        abstract = paper_metadata.get("abstract", "")
        authors = ", ".join(paper_metadata.get("authors", []))
        year = paper_metadata.get("year", "")
        paper_text = (
            f"Title: {title}\n"
            f"Authors: {authors}\n"
            f"Year: {year}\n\n"
            f"Abstract:\n{abstract}\n\n"
            f"[Note: Full text unavailable — teacher is working from abstract only.]"
        )
        text_source = "abstract_fallback"
        print(f"  Using embedded abstract ({len(abstract)} chars) as fallback.")
    elif not paper_text:
        text_source = "none"
        print(f"  WARNING: No paper text available for {paper_url}")
        print(f"  Teacher will work with limited context.")
    else:
        print(f"  Loaded {len(paper_text):,} chars from PDF.")

    # Teacher pass (shared across all conditions and modes for this paper)
    teacher_dir = paper_dir / "_teacher"
    teacher_dir.mkdir(exist_ok=True)
    cached_hint_path = teacher_dir / "hint.json"

    if cached_hint_path.exists():
        # Reuse cached teacher hint (avoids redundant Opus call)
        hint = json.loads(cached_hint_path.read_text(encoding="utf-8"))
        print(f"  [teacher] Reusing cached hint from {cached_hint_path}")
    else:
        teacher_audit = AuditLog(
            paper_id=paper_id,
            paper_url=paper_url,
            reconstruction_type="teacher_extract",
            student_model=student_model,
            teacher_model=teacher_model,
            config={"modes": modes, "conditions": conditions,
                    "text_source": text_source},
        )
        hint = run_teacher(client, teacher_model, paper_text, refs, teacher_audit)
        teacher_audit.mark_finished()

        (cached_hint_path).write_text(
            json.dumps(hint, indent=2, default=str), encoding="utf-8"
        )
        teacher_audit.save(teacher_dir / "audit.json")

    # Prepare reference texts
    refs_text_with = prepare_refs_text(refs)
    refs_text_none = "No references provided. Rely on your own knowledge of the field."

    results = {"paper_id": paper_id, "paper_url": paper_url,
               "text_source": text_source, "conditions": {}}

    for condition in conditions:
        refs_text = refs_text_with if condition == "with_refs" else refs_text_none
        cond_dir = paper_dir / condition
        cond_dir.mkdir(exist_ok=True)
        cond_results = {}

        print(f"\n  === Condition: {condition} ===")

        for mode in modes:
            print(f"\n  --- {condition}/{mode} ---")
            mode_dir = cond_dir / mode
            mode_dir.mkdir(exist_ok=True)

            # --- Iterative refinement path ---
            if iterative and paper_text:
                from infra.iterative import run_iterative_refinement
                from functools import partial

                # In iterative mode, use neutral reference guidance —
                # the teacher's hint refinement handles ref utilization.
                iterative_student = partial(
                    run_student, reference_guidance=REFERENCE_GUIDANCE_NEUTRAL,
                )

                try:
                    iter_dir = mode_dir / "_iterative"
                    iter_result = run_iterative_refinement(
                        client=client,
                        student_model=student_model,
                        teacher_model=teacher_model,
                        mode=mode,
                        initial_hint=hint,
                        refs_text=refs_text,
                        paper_text=paper_text,
                        paper_id=paper_id,
                        condition=condition,
                        run_student_fn=iterative_student,
                        max_rounds=max_rounds,
                        output_dir=iter_dir,
                    )

                    # Use the BEST round's output (not just last — memoryless
                    # students have variance, so pick the peak).
                    best_round = iter_result.best_round()
                    last_round = iter_result.rounds[-1] if iter_result.rounds else None
                    use_round = best_round or last_round
                    output = use_round.student_output if use_round else ""
                    scores = iter_result.score_trajectory()
                    best_score = max(scores) if scores else 0
                    best_rn = use_round.round_number if use_round else 0

                    # Save final output
                    (mode_dir / "output.md").write_text(
                        f"# Reconstruction: {mode} (iterative, {iter_result.total_rounds} rounds)\n"
                        f"**Paper:** {paper_id}  \n"
                        f"**Condition:** {condition}  \n"
                        f"**Student model:** {student_model}  \n"
                        f"**Teacher model:** {teacher_model}  \n"
                        f"**Rounds:** {iter_result.total_rounds}  \n"
                        f"**Best round:** {best_rn} (score {best_score:.1f})  \n"
                        f"**Converged:** {iter_result.converged} ({iter_result.convergence_reason})  \n"
                        f"**Score trajectory:** {' -> '.join(f'{s:.1f}' for s in scores)}  \n\n"
                        f"---\n\n"
                        f"{output}\n",
                        encoding="utf-8",
                    )

                    # Use best round's eval as the mode eval
                    eval_result = use_round.evaluation if use_round else {}
                    if eval_result:
                        (mode_dir / "eval.json").write_text(
                            json.dumps(eval_result, indent=2, default=str),
                            encoding="utf-8",
                        )

                    cond_results[mode] = {
                        "status": "success",
                        "output_chars": len(output),
                        "output_path": str(mode_dir / "output.md"),
                        "iterative": True,
                        "total_rounds": iter_result.total_rounds,
                        "converged": iter_result.converged,
                        "convergence_reason": iter_result.convergence_reason,
                        "score_trajectory": iter_result.score_trajectory(),
                        "eval": eval_result,
                        "final_hint": iter_result.final_hint,
                    }
                    scores = iter_result.score_trajectory()
                    print(f"  [iterative] Final score: {scores[-1] if scores else '?'}")

                except Exception as exc:
                    error_msg = f"ERROR in iterative {condition}/{mode}: {exc}"
                    print(f"  {error_msg}")
                    (mode_dir / "error.txt").write_text(error_msg, encoding="utf-8")
                    cond_results[mode] = {"status": "error", "error": str(exc)}

                continue  # skip the single-shot path below

            # --- Single-shot path (original behavior) ---
            student_audit = AuditLog(
                paper_id=paper_id,
                paper_url=paper_url,
                reconstruction_type=f"{condition}/{mode}",
                student_model=student_model,
                teacher_model=teacher_model,
                config={"condition": condition},
            )

            try:
                output = run_student(
                    client, student_model, mode, hint, refs_text, student_audit
                )
                student_audit.mark_finished()

                # Save student output
                (mode_dir / "output.md").write_text(
                    f"# Reconstruction: {mode}\n"
                    f"**Paper:** {paper_id}  \n"
                    f"**Condition:** {condition}  \n"
                    f"**Student model:** {student_model}  \n"
                    f"**Teacher model:** {teacher_model}  \n\n"
                    f"---\n\n"
                    f"{output}\n",
                    encoding="utf-8",
                )
                student_audit.save(mode_dir / "audit.json")

                mode_result = {
                    "status": "success",
                    "output_chars": len(output),
                    "output_path": str(mode_dir / "output.md"),
                    "input_tokens": student_audit.total_input_tokens(),
                    "output_tokens": student_audit.total_output_tokens(),
                    "duration_s": student_audit.total_duration(),
                }

                # Teacher evaluation
                if evaluate and paper_text:
                    from infra.evaluate import evaluate_reconstruction
                    eval_audit = AuditLog(
                        paper_id=paper_id,
                        paper_url=paper_url,
                        reconstruction_type=f"eval/{condition}/{mode}",
                        student_model=student_model,
                        teacher_model=teacher_model,
                        config={"condition": condition},
                    )
                    print(f"  [eval] Scoring {condition}/{mode}...")
                    eval_result = evaluate_reconstruction(
                        client, teacher_model, paper_text, output,
                        mode, condition, eval_audit,
                    )
                    eval_audit.mark_finished()
                    eval_audit.save(mode_dir / "eval_audit.json")
                    (mode_dir / "eval.json").write_text(
                        json.dumps(eval_result, indent=2, default=str),
                        encoding="utf-8",
                    )
                    mode_result["eval"] = eval_result
                    score = eval_result.get("composite_score", "?")
                    print(f"  [eval] Score: {score}")

                cond_results[mode] = mode_result

            except Exception as exc:
                student_audit.mark_finished()
                student_audit.save(mode_dir / "audit.json")

                error_msg = f"ERROR in {condition}/{mode}: {exc}"
                print(f"  {error_msg}")
                (mode_dir / "error.txt").write_text(error_msg, encoding="utf-8")

                cond_results[mode] = {
                    "status": "error",
                    "error": str(exc),
                }

        results["conditions"][condition] = cond_results

    # Pairwise comparison (if both conditions ran and evaluate is enabled)
    if evaluate and paper_text and "with_refs" in results["conditions"] and "no_refs" in results["conditions"]:
        from infra.evaluate import evaluate_pairwise
        pairwise_dir = paper_dir / "_pairwise"
        pairwise_dir.mkdir(exist_ok=True)
        pairwise_results = {}

        print(f"\n  === Pairwise comparison (with_refs vs no_refs) ===")

        for mode in modes:
            wr = results["conditions"]["with_refs"].get(mode, {})
            nr = results["conditions"]["no_refs"].get(mode, {})
            if wr.get("status") != "success" or nr.get("status") != "success":
                continue

            wr_path = Path(wr["output_path"])
            nr_path = Path(nr["output_path"])
            if not wr_path.exists() or not nr_path.exists():
                continue

            wr_text = wr_path.read_text(encoding="utf-8")
            nr_text = nr_path.read_text(encoding="utf-8")

            pw_audit = AuditLog(
                paper_id=paper_id,
                paper_url=paper_url,
                reconstruction_type=f"pairwise/{mode}",
                student_model=student_model,
                teacher_model=teacher_model,
                config={"mode": mode},
            )

            try:
                print(f"  [pairwise] Comparing {mode}...")
                pw_result = evaluate_pairwise(
                    client, teacher_model, paper_text,
                    wr_text, nr_text, mode, pw_audit,
                )
                pw_audit.mark_finished()
                pw_audit.save(pairwise_dir / f"{mode}_audit.json")
                (pairwise_dir / f"{mode}.json").write_text(
                    json.dumps(pw_result, indent=2, default=str),
                    encoding="utf-8",
                )
                score = pw_result.get("reference_impact_score", "?")
                closer = pw_result.get("which_is_closer_to_original", "?")
                print(f"  [pairwise] Impact: {score}/7 | Closer: {closer}")
                pairwise_results[mode] = pw_result
            except Exception as exc:
                pw_audit.mark_finished()
                pw_audit.save(pairwise_dir / f"{mode}_audit.json")
                print(f"  [pairwise] ERROR in {mode}: {exc}")
                pairwise_results[mode] = {"error": str(exc)}

        results["pairwise"] = pairwise_results

    return results


# ---------------------------------------------------------------------------
# Dispatch summary
# ---------------------------------------------------------------------------

def write_dispatch_summary(results: list[dict], output_dir: Path,
                           student_model: str, teacher_model: str) -> None:
    """Write a human-readable dispatch summary with evaluation scores and comparison."""
    lines = [
        f"# Reconstruction Dispatch Summary",
        f"",
        f"**Timestamp:** {output_dir.name}  ",
        f"**Student model:** {student_model}  ",
        f"**Teacher model:** {teacher_model}  ",
        f"**Papers:** {len(results)}  ",
        f"**Version:** {IMPL_ID}  ",
        f"",
    ]

    has_eval = any(
        info.get("eval") is not None
        for r in results
        for cond in r.get("conditions", {}).values()
        for info in cond.values()
    )

    for r in results:
        lines.append(f"## Paper: {r['paper_id']}")
        lines.append(f"URL: {r['paper_url']}  ")
        lines.append(f"Text source: {r.get('text_source', 'unknown')}")
        lines.append("")

        for condition, modes in r.get("conditions", {}).items():
            lines.append(f"### Condition: `{condition}`")
            lines.append("")
            if has_eval:
                lines.append("| Mode | Status | Chars | Tokens (in/out) | Time | Score |")
                lines.append("|------|--------|-------|-----------------|------|-------|")
            else:
                lines.append("| Mode | Status | Chars | Tokens (in/out) | Time |")
                lines.append("|------|--------|-------|-----------------|------|")
            for mode, info in modes.items():
                if info["status"] == "success":
                    score_str = ""
                    if has_eval:
                        ev = info.get("eval", {})
                        score = ev.get("composite_score", "—")
                        score_str = f" {score} |"
                    if info.get("iterative"):
                        traj = info.get("score_trajectory", [])
                        traj_str = "->".join(f"{s:.1f}" for s in traj)
                        rounds = info.get("total_rounds", "?")
                        lines.append(
                            f"| {mode} | OK ({rounds}R) | {info['output_chars']:,} | "
                            f"— | — |{score_str}"
                        )
                    else:
                        lines.append(
                            f"| {mode} | OK | {info['output_chars']:,} | "
                            f"{info['input_tokens']:,}/{info['output_tokens']:,} | "
                            f"{info['duration_s']:.1f}s |{score_str}"
                        )
                else:
                    err_cols = " — |" if has_eval else ""
                    lines.append(f"| {mode} | ERROR | — | — | — |{err_cols}")
            lines.append("")

        # Cross-condition comparison
        conds = list(r.get("conditions", {}).keys())
        if len(conds) == 2 and has_eval:
            c1, c2 = conds
            lines.append(f"### Comparison: `{c1}` vs `{c2}`")
            lines.append("")
            lines.append("| Mode | Score ({}) | Score ({}) | Delta | Ref Impact |".format(c1, c2))
            lines.append("|------|-----------|-----------|-------|------------|")
            for mode in r["conditions"][c1]:
                e1 = r["conditions"][c1].get(mode, {}).get("eval", {})
                e2 = r["conditions"][c2].get(mode, {}).get("eval", {})
                s1 = e1.get("composite_score", 0)
                s2 = e2.get("composite_score", 0)
                try:
                    delta = float(s1) - float(s2)
                    impact = "+" if delta > 0.3 else ("−" if delta < -0.3 else "≈")
                    lines.append(f"| {mode} | {s1} | {s2} | {delta:+.1f} | {impact} |")
                except (TypeError, ValueError):
                    lines.append(f"| {mode} | {s1} | {s2} | ? | ? |")
            lines.append("")

            # Novelty gap summary
            lines.append(f"### Novelty Gap Analysis")
            lines.append("")
            for mode in r["conditions"][c1]:
                ev = r["conditions"][c1].get(mode, {}).get("eval", {})
                gap = ev.get("novelty_gap", "")
                if gap:
                    lines.append(f"**{mode}:** {gap}")
                    lines.append("")

        # Iterative refinement trajectory
        has_iterative = any(
            info.get("iterative")
            for cond in r.get("conditions", {}).values()
            for info in cond.values()
        )
        if has_iterative:
            lines.append(f"### Iterative Refinement Trajectories")
            lines.append("")
            for condition, modes_data in r.get("conditions", {}).items():
                for mode, info in modes_data.items():
                    if info.get("iterative") and info.get("status") == "success":
                        traj = info.get("score_trajectory", [])
                        traj_str = " -> ".join(f"{s:.1f}" for s in traj)
                        conv = info.get("convergence_reason", "?")
                        rounds = info.get("total_rounds", "?")
                        lines.append(
                            f"**{condition}/{mode}** ({rounds} rounds): "
                            f"{traj_str} | {conv}"
                        )
                        lines.append("")

    (output_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSummary written to {output_dir / 'SUMMARY.md'}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="agent-staged-reconstruct: multi-mode paper reconstruction"
    )
    parser.add_argument(
        "--paper-url",
        help="Single paper URL to reconstruct (overrides test_papers.ndjson)",
    )
    parser.add_argument(
        "--modes", nargs="*", default=None,
        choices=RECONSTRUCTION_MODES,
        help=f"Reconstruction modes to run (default: all). Choices: {RECONSTRUCTION_MODES}",
    )
    parser.add_argument(
        "--student-model", default=None,
        help="Student LLM model (default: auto-selected per backend)",
    )
    parser.add_argument(
        "--teacher-model", default=None,
        help="Teacher LLM model (default: auto-selected per backend)",
    )
    parser.add_argument(
        "--conditions", nargs="*", default=None,
        choices=["with_refs", "no_refs"],
        help="Experimental conditions (default: both). "
             "with_refs = student gets references, no_refs = baseline without references",
    )
    parser.add_argument(
        "--backend", default="auto", choices=["auto", "openai", "anthropic"],
        help="LLM backend (default: auto — tries OpenAI, falls back to Anthropic)",
    )
    parser.add_argument(
        "--evaluate", action="store_true",
        help="Run teacher evaluation scoring on each student output",
    )
    parser.add_argument(
        "--iterative", action="store_true",
        help="Run iterative hint-refinement loop to extract conceptual residual. "
             "Implies --evaluate. Each round: student generates -> teacher evaluates "
             "-> teacher refines hint -> fresh student regenerates.",
    )
    parser.add_argument(
        "--max-rounds", type=int, default=5,
        help="Maximum number of iterative refinement rounds (default: 5). "
             "Only used with --iterative.",
    )
    parser.add_argument(
        "--output-dir", default="reports",
        help="Base output directory (default: reports/)",
    )
    parser.add_argument(
        "--timestamp",
        help="Override timestamp for output folder (ISO format). "
             "Default: current UTC time.",
    )
    args = parser.parse_args()

    modes = args.modes or RECONSTRUCTION_MODES
    conditions = args.conditions or ["with_refs", "no_refs"]
    iterative = args.iterative
    max_rounds = args.max_rounds

    # Initialize LLM client
    client, backend = _make_client(args.backend)

    # Resolve model names based on backend
    if backend == "anthropic":
        student_model = args.student_model or CLAUDE_MODELS["student"]
        teacher_model = args.teacher_model or CLAUDE_MODELS["teacher"]
    else:
        student_model = args.student_model or DEFAULT_STUDENT_MODEL
        teacher_model = args.teacher_model or DEFAULT_TEACHER_MODEL

    # Timestamp for this dispatch
    if args.timestamp:
        ts = args.timestamp
    else:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

    output_dir = Path(args.output_dir) / ts
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    refs = load_references()
    all_known_papers = load_test_papers()
    if args.paper_url:
        # Try to find enriched metadata from test_papers.ndjson
        match = next(
            (p for p in all_known_papers
             if p["url"] == args.paper_url
             or p.get("paper_id") == extract_paper_id(args.paper_url)),
            None,
        )
        papers = [match if match else {"url": args.paper_url}]
    else:
        papers = all_known_papers

    print(f"Dispatch: {len(papers)} paper(s), {len(modes)} mode(s), {len(conditions)} condition(s)")
    print(f"Backend: {backend}")
    print(f"Student: {student_model} | Teacher: {teacher_model}")
    print(f"Output:  {output_dir}")
    print(f"Modes:   {', '.join(modes)}")
    print(f"Conditions: {', '.join(conditions)}")
    print(f"Evaluate:   {args.evaluate}")
    print(f"Iterative:  {iterative} (max {max_rounds} rounds)")

    # Dispatch each paper
    all_results = []
    for paper in papers:
        result = dispatch_paper(
            client=client,
            paper_url=paper["url"],
            refs=refs,
            student_model=student_model,
            teacher_model=teacher_model,
            modes=modes,
            output_dir=output_dir,
            paper_metadata=paper,
            conditions=conditions,
            evaluate=args.evaluate,
            iterative=iterative,
            max_rounds=max_rounds,
        )
        all_results.append(result)

    # Write dispatch summary
    write_dispatch_summary(all_results, output_dir, student_model, teacher_model)

    # Save machine-readable results
    (output_dir / "results.json").write_text(
        json.dumps(all_results, indent=2, default=str), encoding="utf-8"
    )

    print(f"\nDone. All outputs in {output_dir}/")


if __name__ == "__main__":
    main()
