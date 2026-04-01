#!/usr/bin/env python3
"""agent-e2e: single autonomous tool loop.

End-to-end autonomous baseline: the agent drives its own tool loop using the
model's native web_search, decides what to search and when it has enough
evidence, and produces one report.md.

Implementation guide: AGENT_TRACK_ROADMAP.md section 3
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

AGENT_IMPL_ID = "e2e_v1_0_0"

# ---------------------------------------------------------------------------
# Lazy imports (require openai package at runtime, not import time)
# ---------------------------------------------------------------------------

def _import_openai():
    try:
        import openai
        return openai
    except ImportError:
        print("[agent-e2e] ERROR: 'openai' package not installed. Run: pip install openai")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
PROMPTS_DIR = SCRIPT_DIR / "prompts"
SYSTEM_PROMPT = (PROMPTS_DIR / "system.txt").read_text()
VERDICT_PROMPT = (PROMPTS_DIR / "verdict.txt").read_text()


# ---------------------------------------------------------------------------
# Infra imports
# ---------------------------------------------------------------------------

# Resolve infra/ whether running from infra-base (agent_impls/e2e/agent.py)
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
    """Extract a filesystem-safe paper ID from a URL."""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+)", url)
    if m:
        return m.group(1)
    slug = url.rstrip("/").split("/")[-1].replace(".pdf", "")
    return slug[:50]


def _fetch_paper_text(source: str) -> str:
    """Fetch paper text from URL or local path."""
    return extract_text_from_pdf(source, max_chars=60_000)


def _build_initial_message(paper_url: str, paper_text: str) -> str:
    """Build the initial user message for the agent."""
    if paper_text:
        text_section = f"""
## Paper Text (first 60,000 characters)

```
{paper_text[:60_000]}
```
"""
    else:
        text_section = f"""
## Paper URL

{paper_url}

Note: Full text could not be extracted. Use web_search to find information about
this paper using its arXiv ID or title.
"""

    return f"""Please perform a complete derivation audit of the following paper.

{text_section}

Instructions:
1. Identify the paper's actual technical contribution.
2. Decompose it into meaningful technical units.
3. Use web_search extensively to find prior work for each unit.
4. Build a derivation map: component → likely source paper.
5. Judge: NOVEL / COMBINATION / EQUIVALENT / DUPLICATE.
6. When you have gathered sufficient evidence, produce the final report.

Search strategy: search for the specific technical mechanisms (not just the title).
Look for the building-block papers, competing approaches, and theoretical foundations.
"""


def _parse_derivation_entries(report_text: str) -> list[DerivationEntry]:
    """Parse derivation map table from report Markdown."""
    entries = []
    in_table = False
    for line in report_text.splitlines():
        if "Derivation Map" in line:
            in_table = True
            continue
        if in_table and line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 5 and cells[0].lower() not in ("component", "#"):
                try:
                    conf = float(cells[4]) if cells[4] else 0.5
                except ValueError:
                    conf = 0.5
                entries.append(DerivationEntry(
                    component=cells[0],
                    source_paper=cells[1],
                    source_detail=cells[2],
                    derivation_type=cells[3].upper() if cells[3] else "UNKNOWN",
                    confidence=min(1.0, max(0.0, conf)),
                ))
        elif in_table and line.startswith("##"):
            break
    return entries


def _parse_prior_work(report_text: str) -> list[PriorWorkEntry]:
    """Parse prior-work entries from report Markdown."""
    entries = []
    in_section = False
    current: dict = {}

    for line in report_text.splitlines():
        if "Strongest Prior-Work Evidence" in line:
            in_section = True
            continue
        if in_section and line.startswith("## ") and "Strongest" not in line:
            break
        if in_section and line.startswith("### "):
            if current:
                entries.append(PriorWorkEntry(
                    paper_id=current.get("id", "unknown"),
                    title=current.get("title", "Unknown"),
                    year=current.get("year", 0),
                    relevance_note=current.get("relevance", ""),
                    derivation_note=current.get("derivation", ""),
                ))
            # Parse "### Title (Year)"
            m = re.match(r"### (.+?)\s*\((\d{4})\)", line)
            if m:
                current = {"title": m.group(1), "year": int(m.group(2))}
            else:
                current = {"title": line[4:].strip(), "year": 0}
        elif in_section and current:
            if line.startswith("**arXiv/DOI:**"):
                current["id"] = line.split(":", 1)[1].strip()
            elif line.startswith("**Relevance:**"):
                current["relevance"] = line.split(":", 1)[1].strip()
            elif line.startswith("**Derivation note:**"):
                current["derivation"] = line.split(":", 1)[1].strip()

    if current:
        entries.append(PriorWorkEntry(
            paper_id=current.get("id", "unknown"),
            title=current.get("title", "Unknown"),
            year=current.get("year", 0),
            relevance_note=current.get("relevance", ""),
            derivation_note=current.get("derivation", ""),
        ))
    return entries


def _parse_verdict(report_text: str) -> tuple[str, float]:
    """Parse verdict and confidence from report text."""
    verdict = "NOVEL"
    confidence = 0.5

    for line in report_text.splitlines():
        if line.startswith("**Verdict:**"):
            for v in ("NOVEL", "COMBINATION", "EQUIVALENT", "DUPLICATE"):
                if v in line:
                    verdict = v
                    break
        elif line.startswith("**Confidence:**"):
            m = re.search(r"([01]?\.\d+|\d+\.?\d*)", line)
            if m:
                confidence = min(1.0, max(0.0, float(m.group(1))))

    return verdict, confidence


def _parse_search_queries(messages: list[dict]) -> list[str]:
    """Extract web_search queries from message history."""
    queries = []
    for msg in messages:
        if isinstance(msg.get("content"), list):
            for block in msg["content"]:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    if block.get("name") == "web_search":
                        q = (block.get("input") or {}).get("query", "")
                        if q:
                            queries.append(q)
    return queries


# ---------------------------------------------------------------------------
# Main agent loop using OpenAI Responses API
# ---------------------------------------------------------------------------

def run_agent(paper_url: str, model: str, output_path: Path) -> None:
    openai = _import_openai()
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    paper_id = _extract_paper_id(paper_url)
    ctx = RunContext(
        track="e2e",
        impl_id=AGENT_IMPL_ID,
        paper_id=paper_id,
        paper_source=paper_url,
        model=model,
    )
    ctx.record_tool("web_search")
    ctx.record_tool("fetch_paper_text")

    print(f"[agent-e2e] impl_id={AGENT_IMPL_ID} paper={paper_id} model={model}")
    print(f"[agent-e2e] Fetching paper text from {paper_url} ...")
    paper_text = _fetch_paper_text(paper_url)
    if paper_text:
        print(f"[agent-e2e] Extracted {len(paper_text):,} characters from PDF.")
    else:
        print("[agent-e2e] PDF extraction failed — agent will search web for paper info.")

    initial_message = _build_initial_message(paper_url, paper_text)

    print(f"[agent-e2e] Starting autonomous tool loop with model={model} ...")

    # Use OpenAI Responses API with built-in web_search tool
    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=initial_message,
        tools=[{"type": "web_search_preview"}],
        max_output_tokens=8192,
    )

    # Extract the response text
    report_body = ""
    response_id = getattr(response, "id", "")
    ctx.response_id = response_id

    for item in response.output:
        if hasattr(item, "type") and item.type == "message":
            for block in item.content:
                if hasattr(block, "type") and block.type == "output_text":
                    report_body = block.text
                    break

    if not report_body:
        # Fallback: try to get text directly
        report_body = str(response.output_text) if hasattr(response, "output_text") else ""

    print(f"[agent-e2e] Agent produced {len(report_body):,} characters.")

    # Now ask for the final structured report
    print("[agent-e2e] Requesting final structured report ...")
    final_response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=[
            {"role": "user", "content": initial_message},
            {"role": "assistant", "content": report_body},
            {"role": "user", "content": VERDICT_PROMPT},
        ],
        max_output_tokens=4096,
    )

    final_text = ""
    for item in final_response.output:
        if hasattr(item, "type") and item.type == "message":
            for block in item.content:
                if hasattr(block, "type") and block.type == "output_text":
                    final_text = block.text
                    break

    if not final_text:
        final_text = report_body  # fallback to initial response

    # Parse results
    verdict, confidence = _parse_verdict(final_text)
    derivation_map = _parse_derivation_entries(final_text)
    prior_work = _parse_prior_work(final_text)

    # Parse search queries from annotations if available
    search_queries = []
    for item in response.output:
        if hasattr(item, "type") and item.type == "web_search_call":
            q = getattr(item, "query", "") or getattr(getattr(item, "action", None), "query", "")
            if q:
                search_queries.append(q)

    ctx.final_verdict = verdict
    ctx.confidence = confidence
    ctx.main_cited_evidence = [pw.paper_id for pw in prior_work[:5]]
    ctx.mark_finished()

    # Build report content
    content = ReportContent(
        context=ctx,
        executive_summary=_extract_section(final_text, "Executive Summary"),
        decomposition=_extract_decomposition(final_text),
        prior_work=prior_work,
        derivation_map=derivation_map,
        residual_novelty=_extract_section(final_text, "Residual Novelty"),
        uncertainties=_extract_bullet_list(final_text, "Uncertainties"),
        tool_call_log=[{"tool": "web_search", "queries": search_queries}],
        search_queries=search_queries,
        raw_json_blocks={"response_id": response_id},
    )

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = ReportWriter(output_path=output_path)
    writer.write(content)

    # Also write the raw agent output alongside the structured report for debugging
    raw_path = output_path.parent / "agent_raw_output.md"
    raw_path.write_text(f"# Agent Raw Output\n\n{final_text}\n")

    print(f"[agent-e2e] Report written to {output_path}")
    print(f"[agent-e2e] Verdict: {verdict} (confidence={confidence:.2f})")


def _extract_section(text: str, heading: str) -> str:
    """Extract the body of a Markdown section by heading."""
    pattern = rf"##+ {re.escape(heading)}\s*\n(.*?)(?=\n##+ |\Z)"
    m = re.search(pattern, text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


def _extract_decomposition(text: str) -> list[dict]:
    """Extract the technical contribution decomposition table."""
    decomp = []
    in_table = False
    for line in text.splitlines():
        if "Technical Contribution Decomposition" in line:
            in_table = True
            continue
        if in_table and line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3 and cells[0].lower() not in ("#", ""):
                try:
                    int(cells[0])  # skip header row with "#"
                    decomp.append({"name": cells[1], "description": cells[2]})
                except ValueError:
                    pass
        elif in_table and line.startswith("##"):
            break
    return decomp


def _extract_bullet_list(text: str, heading: str) -> list[str]:
    """Extract a bullet-point list from a section."""
    section = _extract_section(text, heading)
    items = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            items.append(line[2:].strip())
    return items


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="agent-e2e: autonomous review loop")
    parser.add_argument("--paper-url", required=True,
                        help="arXiv URL or local PDF path")
    parser.add_argument("--model", default="gpt-4o",
                        help="LLM model identifier (default: gpt-4o)")
    parser.add_argument("--output", default="reports/report.md",
                        help="Output path for report.md")
    args = parser.parse_args()

    output_path = Path(args.output)
    run_agent(
        paper_url=args.paper_url,
        model=args.model,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()
