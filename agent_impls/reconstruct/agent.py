#!/usr/bin/env python3
"""agent-reconstruct: minimal teacher-student reconstruction track.

Teacher agent: reads paper, extracts domain problem hint (no solution revealed).
Student agent: given hint + allowed refs only, develops methodology independently.
               No external search — reconstruction from first principles.
Comparison pass: compares student methodology against the actual paper.

Implementation guide: AGENT_TRACK_ROADMAP.md section 5
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

AGENT_IMPL_ID = "reconstruct_v1_0_0"

# ---------------------------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------------------------

def _import_openai():
    try:
        import openai
        return openai
    except ImportError:
        print("[agent-reconstruct] ERROR: 'openai' package not installed.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
PROMPTS_DIR = SCRIPT_DIR / "prompts"

# ---------------------------------------------------------------------------
# Infra imports
# ---------------------------------------------------------------------------

# Resolve infra/ whether running from infra-base (agent_impls/reconstruct/agent.py)
# or from an agent branch (agent.py at root alongside infra/).
for _p in [SCRIPT_DIR, SCRIPT_DIR.parent.parent]:
    if (_p / "infra").is_dir():
        sys.path.insert(0, str(_p))
        break
from infra.run_context import RunContext
from infra.report_writer import (
    DerivationEntry,
    PriorWorkEntry,
    ReportContent,
    ReportWriter,
)
from infra.pdf_utils import extract_text_from_pdf


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_paper_id(url: str) -> str:
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+)", url)
    if m:
        return m.group(1)
    slug = url.rstrip("/").split("/")[-1].replace(".pdf", "")
    return slug[:50]


def _resolve_ref(ref: str) -> str:
    """Resolve a reference: either arXiv ID (fetch PDF URL) or local path."""
    # If it looks like an arXiv ID, convert to PDF URL
    if re.match(r"^\d{4}\.\d+", ref):
        return f"https://arxiv.org/pdf/{ref}"
    return ref


def _llm_call(client, model: str, system: str, user: str,
              max_tokens: int = 4096) -> str:
    """Single LLM call without any tools (pure reasoning)."""
    response = client.responses.create(
        model=model,
        instructions=system,
        input=user,
        max_output_tokens=max_tokens,
    )
    for item in response.output:
        if hasattr(item, "type") and item.type == "message":
            for block in item.content:
                if hasattr(block, "type") and block.type == "output_text":
                    return block.text
    if hasattr(response, "output_text"):
        return str(response.output_text)
    return str(response.output)


def _extract_json_block(text: str) -> Any:
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
# Teacher agent
# ---------------------------------------------------------------------------

def run_teacher(client, model: str, paper_text: str) -> dict:
    """Extract a minimal problem-definition hint from the paper."""
    print("[agent-reconstruct] Teacher: extracting problem hint ...")
    prompt = (PROMPTS_DIR / "teacher.txt").read_text()

    response = _llm_call(
        client, model,
        system=prompt,
        user=f"Extract the problem hint from the following paper:\n\n{paper_text[:40_000]}",
        max_tokens=2048,
    )

    hint = _extract_json_block(response)
    if hint is None:
        # Fallback: use a minimal hint
        hint = {
            "domain": "Unknown domain",
            "specific_problem": response[:500] if response else "Unknown problem",
            "evaluation_criteria": "Unknown",
            "constraints": [],
            "non_hints": [],
        }
    print(f"[agent-reconstruct] Teacher hint domain: {hint.get('domain', 'N/A')}")
    return hint


# ---------------------------------------------------------------------------
# Student agent
# ---------------------------------------------------------------------------

def run_student(client, model: str, hint: dict, refs: list[str]) -> str:
    """Reconstruct methodology from hint and allowed references only."""
    print(f"[agent-reconstruct] Student: reconstructing from {len(refs)} reference(s) ...")
    prompt_template = (PROMPTS_DIR / "student.txt").read_text()

    # Fetch reference texts (student is allowed to read them)
    refs_text_parts = []
    for ref in refs:
        ref_url = _resolve_ref(ref)
        print(f"[agent-reconstruct] Student: reading reference {ref} ...")
        ref_text = extract_text_from_pdf(ref_url, max_chars=20_000)
        if ref_text:
            refs_text_parts.append(
                f"--- Reference: {ref} ---\n{ref_text[:20_000]}\n--- End reference ---"
            )
        else:
            refs_text_parts.append(
                f"--- Reference: {ref} ---\n[Text not available]\n--- End reference ---"
            )

    refs_text = "\n\n".join(refs_text_parts) if refs_text_parts else "No references provided."

    filled_prompt = (
        prompt_template
        .replace("{hint_json}", json.dumps(hint, indent=2))
        .replace("{refs_text}", refs_text)
    )

    methodology = _llm_call(
        client, model,
        system=filled_prompt,
        user="Develop your detailed methodology for the stated problem.",
        max_tokens=4096,
    )

    print(f"[agent-reconstruct] Student produced {len(methodology):,} chars.")
    return methodology


# ---------------------------------------------------------------------------
# Comparison pass
# ---------------------------------------------------------------------------

def run_comparison(client, model: str, hint: dict, methodology: str,
                   paper_text: str) -> dict:
    """Compare student reconstruction against the actual paper."""
    print("[agent-reconstruct] Comparison: analysing reconstruction ...")
    prompt_template = (PROMPTS_DIR / "compare.txt").read_text()

    filled_prompt = (
        prompt_template
        .replace("{hint_json}", json.dumps(hint, indent=2))
        .replace("{student_methodology}", methodology[:8_000])
        .replace("{paper_text}", paper_text[:15_000])
    )

    response = _llm_call(
        client, model,
        system="You are a precise comparison agent.",
        user=filled_prompt,
        max_tokens=4096,
    )

    result = _extract_json_block(response)
    if result is None:
        result = {
            "matched_components": [],
            "diverged_components": [],
            "missed_components": [],
            "verdict": "PARTIAL",
            "verdict_rationale": response[:500] if response else "Comparison failed.",
            "reconstruction_difficulty_signal": "",
        }
    return result


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_report(
    paper_id: str,
    hint: dict,
    methodology: str,
    comparison: dict,
    refs: list[str],
    ctx: RunContext,
    output_path: Path,
) -> None:
    """Render the final report.md."""
    verdict_map = {
        "MATCHED": ("EQUIVALENT", 0.8),
        "PARTIAL": ("COMBINATION", 0.6),
        "DIVERGED": ("NOVEL", 0.75),
    }
    recon_verdict = comparison.get("verdict", "PARTIAL")
    standard_verdict, conf = verdict_map.get(recon_verdict, ("COMBINATION", 0.5))

    ctx.final_verdict = standard_verdict
    ctx.confidence = conf
    ctx.main_cited_evidence = refs[:5]
    ctx.mark_finished()

    # Build derivation map from matched components
    derivation_map = [
        DerivationEntry(
            component=mc.get("aspect", ""),
            source_paper="(allowed references)",
            source_detail=mc.get("student_version", "")[:100],
            derivation_type=(
                "EQUIVALENT" if mc.get("match_quality") == "EXACT"
                else "COMBINATION"
            ),
            confidence=0.7 if mc.get("match_quality") == "EXACT" else 0.5,
        )
        for mc in comparison.get("matched_components", [])
    ] + [
        DerivationEntry(
            component=dc.get("aspect", ""),
            source_paper="(paper only)",
            source_detail=dc.get("paper_version", "")[:100],
            derivation_type="NOVEL",
            confidence=0.7,
        )
        for dc in comparison.get("diverged_components", [])
    ]

    # Build executive summary
    verdict_rationale = comparison.get("verdict_rationale", "")
    novelty_signal = comparison.get("reconstruction_difficulty_signal", "")
    exec_summary = (
        f"Teacher-student reconstruction analysis for paper '{paper_id}'. "
        f"The student agent was given the problem hint and {len(refs)} reference(s). "
        f"Reconstruction verdict: **{recon_verdict}**. "
        f"{verdict_rationale} "
        f"{novelty_signal}"
    )

    uncertainties = [
        f"Student used {len(refs)} reference(s); additional references might change the verdict.",
        "Reconstruction quality depends on reference coverage of the problem space.",
    ]
    if not refs:
        uncertainties.insert(0, "No references were provided — student used only its own knowledge.")

    content = ReportContent(
        context=ctx,
        executive_summary=exec_summary,
        decomposition=[
            {"name": "Problem domain", "description": hint.get("domain", "")},
            {"name": "Specific problem", "description": hint.get("specific_problem", "")},
            {"name": "Evaluation criteria", "description": hint.get("evaluation_criteria", "")},
        ],
        prior_work=[
            PriorWorkEntry(
                paper_id=ref,
                title=f"Reference: {ref}",
                year=0,
                relevance_note="Allowed reference for student reconstruction.",
                derivation_note="Student was permitted to read this paper.",
            )
            for ref in refs
        ],
        derivation_map=derivation_map,
        residual_novelty="\n".join([
            dc.get("divergence_reason", "") or mc.get("aspect", "")
            for dc in comparison.get("diverged_components", [])
            for mc in comparison.get("missed_components", [])
        ]) or comparison.get("reconstruction_difficulty_signal", "N/A"),
        uncertainties=uncertainties,
        tool_call_log=[{
            "agent": "teacher",
            "action": "extracted problem hint",
        }, {
            "agent": "student",
            "action": f"reconstructed from {len(refs)} references",
        }, {
            "agent": "comparison",
            "action": "compared reconstruction to paper",
        }],
        search_queries=[],  # Student has no search tools by design
        raw_json_blocks={
            "hint": hint,
            "comparison": comparison,
            "student_methodology_excerpt": methodology[:2000],
        },
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = ReportWriter(output_path=output_path)
    writer.write(content)

    # Save student reconstruction for inspection
    student_path = output_path.parent / "student_reconstruction.md"
    student_path.write_text(f"# Student Reconstruction\n\n{methodology}\n")

    print(f"[agent-reconstruct] Report written to {output_path}")
    print(f"[agent-reconstruct] Reconstruction verdict: {recon_verdict}")
    print(f"[agent-reconstruct] IP verdict: {standard_verdict} (confidence={conf:.2f})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_agent(paper_url: str, refs: list[str], model: str, output_path: Path) -> None:
    openai = _import_openai()
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        print("[agent-reconstruct] ERROR: OPENAI_API_KEY is not set. Add it as a GitHub secret.")
        sys.exit(1)
    client = openai.OpenAI(api_key=api_key)

    paper_id = _extract_paper_id(paper_url)
    ctx = RunContext(
        track="reconstruct",
        impl_id=AGENT_IMPL_ID,
        paper_id=paper_id,
        paper_source=paper_url,
        model=model,
    )
    ctx.record_tool("fetch_paper_text")

    print(f"[agent-reconstruct] impl_id={AGENT_IMPL_ID} paper={paper_id} "
          f"refs={refs} model={model}")

    # Fetch full paper text (teacher reads it; student does NOT)
    print(f"[agent-reconstruct] Fetching paper text ...")
    paper_text = extract_text_from_pdf(paper_url, max_chars=60_000)
    if not paper_text:
        print("[agent-reconstruct] WARNING: Could not extract paper text.")

    # Teacher pass
    hint = run_teacher(client, model, paper_text)

    # Student pass (no paper text; refs only)
    methodology = run_student(client, model, hint, refs)

    # Comparison pass
    comparison = run_comparison(client, model, hint, methodology, paper_text)

    # Render report
    render_report(paper_id, hint, methodology, comparison, refs, ctx, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="agent-reconstruct: teacher-student reconstruction"
    )
    parser.add_argument("--paper-url", required=True,
                        help="arXiv URL or local PDF path of the paper to reconstruct")
    parser.add_argument("--refs", nargs="*", default=[],
                        help="Allowed reference arXiv IDs or PDF paths for the student")
    parser.add_argument("--model", default="gpt-4o",
                        help="LLM model identifier (default: gpt-4o)")
    parser.add_argument("--output", default="reports/report.md",
                        help="Output path for report.md")
    args = parser.parse_args()

    run_agent(
        paper_url=args.paper_url,
        refs=args.refs,
        model=args.model,
        output_path=Path(args.output),
    )


if __name__ == "__main__":
    main()
