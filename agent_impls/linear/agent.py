#!/usr/bin/env python3
"""agent-linear: 6-stage checkpointed pipeline.

Staged, auditable baseline: explicit ordered checkpoints, each serialised so
any stage can be re-run independently.

Implementation guide: AGENT_TRACK_ROADMAP.md section 4
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

AGENT_IMPL_ID = "linear_v1_0_0"

# Stage constants
STAGE_INGEST = 1
STAGE_DECOMPOSE = 2
STAGE_RETRIEVE = 3
STAGE_COMPARE = 4
STAGE_JUDGE = 5
STAGE_SYNTHESISE = 6

# ---------------------------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------------------------

def _import_openai():
    try:
        import openai
        return openai
    except ImportError:
        print("[agent-linear] ERROR: 'openai' package not installed. Run: pip install openai")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
PROMPTS_DIR = SCRIPT_DIR / "prompts"
CHECKPOINTS_DIR = Path("checkpoints")

# ---------------------------------------------------------------------------
# Infra imports
# ---------------------------------------------------------------------------

sys.path.insert(0, str(SCRIPT_DIR.parent.parent))
from infra.run_context import RunContext
from infra.report_writer import (
    DerivationEntry,
    PriorWorkEntry,
    ReportContent,
    ReportWriter,
)
from infra.pdf_utils import extract_text_from_pdf


# ---------------------------------------------------------------------------
# Checkpoint I/O
# ---------------------------------------------------------------------------

def save_checkpoint(name: str, data: Any) -> None:
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    path = CHECKPOINTS_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2))
    print(f"[agent-linear] Checkpoint saved: {path}")


def load_checkpoint(name: str) -> Any:
    path = CHECKPOINTS_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def checkpoint_exists(name: str) -> bool:
    return (CHECKPOINTS_DIR / f"{name}.json").exists()


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

def _llm_call(client, model: str, system: str, user: str,
               tools: list | None = None, max_tokens: int = 4096) -> str:
    """Single LLM call; returns the text of the first message output."""
    kwargs: dict[str, Any] = {
        "model": model,
        "instructions": system,
        "input": user,
        "max_output_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools

    response = client.responses.create(**kwargs)

    # Extract text from response
    for item in response.output:
        if hasattr(item, "type") and item.type == "message":
            for block in item.content:
                if hasattr(block, "type") and block.type == "output_text":
                    return block.text
    # Fallback
    if hasattr(response, "output_text"):
        return str(response.output_text)
    return str(response.output)


def _extract_json_block(text: str) -> Any:
    """Extract the first JSON block from a text response."""
    # Try to find ```json ... ``` blocks
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Try bare JSON object
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _extract_paper_id(url: str) -> str:
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+)", url)
    if m:
        return m.group(1)
    slug = url.rstrip("/").split("/")[-1].replace(".pdf", "")
    return slug[:50]


# ---------------------------------------------------------------------------
# Stage 1: Ingest
# ---------------------------------------------------------------------------

def stage_ingest(paper_url: str) -> dict:
    print("[agent-linear] Stage 1: Ingest")
    paper_id = _extract_paper_id(paper_url)
    full_text = extract_text_from_pdf(paper_url, max_chars=80_000)

    # Try to extract title/abstract from text
    title = ""
    abstract = ""
    if full_text:
        lines = full_text.splitlines()
        # Simple heuristic: first non-empty line as title
        for line in lines[:20]:
            if line.strip() and len(line.strip()) > 5:
                title = line.strip()
                break
        # Find abstract section
        abs_start = full_text.lower().find("abstract")
        if abs_start >= 0:
            abs_text = full_text[abs_start:abs_start + 2000]
            abstract = abs_text.split("\n\n")[0].replace("Abstract", "").strip()

    checkpoint = {
        "paper_id": paper_id,
        "source_url": paper_url,
        "title": title,
        "abstract": abstract,
        "full_text": full_text,
    }
    save_checkpoint("stage_1_paper", checkpoint)
    return checkpoint


# ---------------------------------------------------------------------------
# Stage 2: Decompose
# ---------------------------------------------------------------------------

def stage_decompose(client, model: str, paper_ck: dict) -> dict:
    print("[agent-linear] Stage 2: Decompose")
    prompt_template = (PROMPTS_DIR / "decompose.txt").read_text()

    paper_excerpt = f"""Title: {paper_ck['title']}

Abstract: {paper_ck['abstract']}

Full text (first 15,000 chars):
{paper_ck['full_text'][:15_000]}
"""
    response = _llm_call(
        client, model,
        system=prompt_template,
        user=f"Decompose the following paper:\n\n{paper_excerpt}",
        max_tokens=2048,
    )
    data = _extract_json_block(response)
    if data is None:
        # Fallback minimal decomposition
        data = {
            "core_concept": paper_ck["title"] or "Unknown",
            "technical_units": [{"id": 1, "name": "Core method",
                                  "description": paper_ck["abstract"][:500],
                                  "mechanism": "see paper",
                                  "load_bearing_assumptions": []}],
            "bottleneck": "see paper",
            "search_queries": [paper_ck["title"] or paper_ck["paper_id"]],
        }

    save_checkpoint("stage_2_decomp", data)
    return data


# ---------------------------------------------------------------------------
# Stage 3: Retrieve
# ---------------------------------------------------------------------------

def stage_retrieve(client, model: str, decomp: dict) -> dict:
    print("[agent-linear] Stage 3: Retrieve (web_search)")
    queries = decomp.get("search_queries", [])
    if not queries:
        queries = [decomp.get("core_concept", "research paper")]

    candidates = []
    seen_ids = set()

    for query in queries[:6]:  # cap at 6 queries
        print(f"[agent-linear]   Searching: {query!r}")
        response = client.responses.create(
            model=model,
            instructions=(
                "You are a research assistant. Search for papers related to the given query. "
                "For each result, extract: title, year, arXiv ID or DOI if available, "
                "and a one-sentence snippet about what the paper does. "
                "Return a JSON array of objects: "
                '[{"paper_id": "...", "title": "...", "year": 2020, "source": "web_search", "snippet": "..."}]'
            ),
            input=f"Find academic papers related to: {query}",
            tools=[{"type": "web_search_preview"}],
            max_output_tokens=2048,
        )
        result_text = ""
        for item in response.output:
            if hasattr(item, "type") and item.type == "message":
                for block in item.content:
                    if hasattr(block, "type") and block.type == "output_text":
                        result_text = block.text
                        break

        # Parse the JSON array from the response
        arr_m = re.search(r"\[.*?\]", result_text, re.DOTALL)
        if arr_m:
            try:
                papers = json.loads(arr_m.group(0))
                for p in papers:
                    pid = p.get("paper_id", "") or p.get("title", "")[:40]
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        candidates.append({
                            "paper_id": pid,
                            "title": p.get("title", ""),
                            "year": p.get("year", 0),
                            "source": "web_search",
                            "snippet": p.get("snippet", ""),
                        })
            except json.JSONDecodeError:
                pass

    result = {"candidates": candidates, "queries_used": queries}
    save_checkpoint("stage_3_refs", result)
    return result


# ---------------------------------------------------------------------------
# Stage 4: Compare
# ---------------------------------------------------------------------------

def stage_compare(client, model: str, decomp: dict, refs: dict) -> dict:
    print("[agent-linear] Stage 4: Compare")
    prompt_template = (PROMPTS_DIR / "compare.txt").read_text()
    decomp_json = json.dumps(decomp, indent=2)
    comparisons = []

    # Take top-K candidates
    top_k = refs.get("candidates", [])[:8]

    for ref in top_k:
        filled_prompt = (
            prompt_template
            .replace("{decomp_json}", decomp_json)
            .replace("{ref_title}", ref.get("title", ""))
            .replace("{ref_id}", ref.get("paper_id", ""))
            .replace("{ref_year}", str(ref.get("year", "")))
            .replace("{ref_snippet}", ref.get("snippet", ""))
        )
        response_text = _llm_call(
            client, model,
            system="You are a precise research-IP analyst.",
            user=filled_prompt,
            max_tokens=2048,
        )
        data = _extract_json_block(response_text)
        if data:
            comparisons.append(data)

    result = {"comparisons": comparisons}
    save_checkpoint("stage_4_comparisons", result)
    return result


# ---------------------------------------------------------------------------
# Stage 5: Judge
# ---------------------------------------------------------------------------

def stage_judge(client, model: str, comparisons: dict) -> dict:
    print("[agent-linear] Stage 5: Judge")
    comps_json = json.dumps(comparisons, indent=2)

    def _judge(prompt_file: str) -> dict:
        template = (PROMPTS_DIR / prompt_file).read_text()
        text = _llm_call(
            client, model,
            system="You are a precise research-IP judge.",
            user=template.replace("{comparisons_json}", comps_json),
            max_tokens=2048,
        )
        data = _extract_json_block(text)
        return data or {}

    dup = _judge("judge_dup.txt")
    combo = _judge("judge_combo.txt")
    equiv = _judge("judge_equiv.txt")

    result = {"duplication": dup, "combination": combo, "equivalence": equiv}
    save_checkpoint("stage_5_judgment", result)
    return result


# ---------------------------------------------------------------------------
# Stage 6: Synthesise
# ---------------------------------------------------------------------------

def stage_synthesise(client, model: str, decomp: dict, judgment: dict) -> dict:
    print("[agent-linear] Stage 6: Synthesise")
    template = (PROMPTS_DIR / "synthesise.txt").read_text()
    user = (
        template
        .replace("{decomp_json}", json.dumps(decomp, indent=2))
        .replace("{dup_json}", json.dumps(judgment.get("duplication", {}), indent=2))
        .replace("{combo_json}", json.dumps(judgment.get("combination", {}), indent=2))
        .replace("{equiv_json}", json.dumps(judgment.get("equivalence", {}), indent=2))
    )
    text = _llm_call(
        client, model,
        system="You are a research-IP judge synthesising a final verdict.",
        user=user,
        max_tokens=4096,
    )
    data = _extract_json_block(text)
    if data is None:
        data = {
            "verdict": "NOVEL",
            "confidence": 0.3,
            "primary_reason": "Synthesis failed; defaulting to NOVEL with low confidence.",
            "derivation_map": [],
            "cited_evidence": [],
            "residual_novelty": "Unknown.",
            "uncertainties": ["Synthesis stage failed."],
        }
    save_checkpoint("stage_6_synthesis", data)
    return data


# ---------------------------------------------------------------------------
# Stage R: Render
# ---------------------------------------------------------------------------

def stage_render(paper_ck: dict, synthesis: dict, refs: dict,
                 ctx: RunContext, output_path: Path) -> None:
    print("[agent-linear] Stage R: Render")

    derivation_map = [
        DerivationEntry(
            component=entry.get("component", ""),
            source_paper=entry.get("source_paper", ""),
            source_detail=entry.get("source_detail", ""),
            derivation_type=entry.get("derivation_type", "UNKNOWN"),
            confidence=float(entry.get("confidence", 0.5)),
        )
        for entry in synthesis.get("derivation_map", [])
    ]

    # Build prior work entries from the refs + synthesis
    cited_ids = set(synthesis.get("cited_evidence", []))
    prior_work = []
    for cand in refs.get("candidates", []):
        if cand.get("paper_id", "") in cited_ids:
            prior_work.append(PriorWorkEntry(
                paper_id=cand["paper_id"],
                title=cand.get("title", ""),
                year=int(cand.get("year", 0)),
                relevance_note=cand.get("snippet", ""),
                derivation_note="See derivation map.",
            ))

    # Load all checkpoints for appendix
    all_checkpoints = {}
    for cp_name in ["stage_2_decomp", "stage_3_refs", "stage_4_comparisons",
                    "stage_5_judgment", "stage_6_synthesis"]:
        cp = load_checkpoint(cp_name)
        if cp:
            all_checkpoints[cp_name] = cp

    content = ReportContent(
        context=ctx,
        executive_summary=(
            f"Paper '{paper_ck.get('title', ctx.paper_id)}' was analysed through a "
            f"6-stage pipeline. "
            f"Verdict: {synthesis.get('verdict', 'UNKNOWN')}. "
            f"{synthesis.get('primary_reason', '')}"
        ),
        decomposition=[
            {"unit": u.get("name", ""), "description": u.get("description", "")}
            for u in (load_checkpoint("stage_2_decomp") or {}).get("technical_units", [])
        ],
        prior_work=prior_work,
        derivation_map=derivation_map,
        residual_novelty=synthesis.get("residual_novelty", ""),
        uncertainties=synthesis.get("uncertainties", []),
        tool_call_log=[{"stage": "retrieve", "queries": refs.get("queries_used", [])}],
        search_queries=refs.get("queries_used", []),
        raw_json_blocks=all_checkpoints,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = ReportWriter(output_path=output_path)
    writer.write(content)
    print(f"[agent-linear] Report written to {output_path}")


# ---------------------------------------------------------------------------
# Main pipeline orchestration
# ---------------------------------------------------------------------------

def run_pipeline(paper_url: str, model: str, from_stage: int, output_path: Path) -> None:
    openai = _import_openai()
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    paper_id = _extract_paper_id(paper_url)
    print(f"[agent-linear] impl_id={AGENT_IMPL_ID} paper={paper_id} model={model} "
          f"from_stage={from_stage}")

    ctx = RunContext(
        track="linear",
        impl_id=AGENT_IMPL_ID,
        paper_id=paper_id,
        paper_source=paper_url,
        model=model,
    )
    ctx.record_tool("web_search")
    ctx.record_tool("fetch_paper_text")

    # --- Stage 1: Ingest ---
    if from_stage <= STAGE_INGEST:
        paper_ck = stage_ingest(paper_url)
    else:
        paper_ck = load_checkpoint("stage_1_paper")
        if paper_ck is None:
            print("[agent-linear] ERROR: No stage_1_paper checkpoint. Run from stage 1.")
            sys.exit(1)

    # --- Stage 2: Decompose ---
    if from_stage <= STAGE_DECOMPOSE:
        decomp = stage_decompose(client, model, paper_ck)
    else:
        decomp = load_checkpoint("stage_2_decomp")
        if decomp is None:
            print("[agent-linear] ERROR: No stage_2_decomp checkpoint.")
            sys.exit(1)

    # --- Stage 3: Retrieve ---
    if from_stage <= STAGE_RETRIEVE:
        refs = stage_retrieve(client, model, decomp)
    else:
        refs = load_checkpoint("stage_3_refs")
        if refs is None:
            print("[agent-linear] ERROR: No stage_3_refs checkpoint.")
            sys.exit(1)

    # --- Stage 4: Compare ---
    if from_stage <= STAGE_COMPARE:
        comparisons = stage_compare(client, model, decomp, refs)
    else:
        comparisons = load_checkpoint("stage_4_comparisons")
        if comparisons is None:
            print("[agent-linear] ERROR: No stage_4_comparisons checkpoint.")
            sys.exit(1)

    # --- Stage 5: Judge ---
    if from_stage <= STAGE_JUDGE:
        judgment = stage_judge(client, model, comparisons)
    else:
        judgment = load_checkpoint("stage_5_judgment")
        if judgment is None:
            print("[agent-linear] ERROR: No stage_5_judgment checkpoint.")
            sys.exit(1)

    # --- Stage 6: Synthesise ---
    if from_stage <= STAGE_SYNTHESISE:
        synthesis = stage_synthesise(client, model, decomp, judgment)
    else:
        synthesis = load_checkpoint("stage_6_synthesis")
        if synthesis is None:
            print("[agent-linear] ERROR: No stage_6_synthesis checkpoint.")
            sys.exit(1)

    # Update context with final verdict
    ctx.final_verdict = synthesis.get("verdict", "NOVEL")
    ctx.confidence = float(synthesis.get("confidence", 0.5))
    ctx.main_cited_evidence = synthesis.get("cited_evidence", [])[:5]
    ctx.mark_finished()

    # --- Stage R: Render ---
    stage_render(paper_ck, synthesis, refs, ctx, output_path)

    print(f"[agent-linear] Verdict: {ctx.final_verdict} (confidence={ctx.confidence:.2f})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="agent-linear: staged pipeline")
    parser.add_argument("--paper-url", required=True,
                        help="arXiv URL or local PDF path")
    parser.add_argument("--model", default="gpt-4o",
                        help="LLM model identifier (default: gpt-4o)")
    parser.add_argument("--output", default="reports/report.md",
                        help="Output path for report.md")
    parser.add_argument("--from-stage", type=int, default=1,
                        help="Resume from stage N (1–6)")
    args = parser.parse_args()

    run_pipeline(
        paper_url=args.paper_url,
        model=args.model,
        from_stage=args.from_stage,
        output_path=Path(args.output),
    )


if __name__ == "__main__":
    main()
