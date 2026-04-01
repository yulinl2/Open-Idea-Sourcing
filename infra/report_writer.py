"""
infra/report_writer.py

Writes the canonical report.md for an agent-track run.

Every agent track produces exactly one report.md per run. This module enforces
the required structure (YAML front matter + required sections) and provides
helper methods for building each section.

The report is assembled from a ReportContext (the structured data) and rendered
to Markdown. No LLM calls occur here — this is a pure rendering function.

Required report.md structure (§7, §8 of PROJECT_INSTRUCTIONS_AGENT.md):
  - YAML front matter (from RunContext)
  - Table of contents
  - Executive summary
  - Final verdict
  - Technical contribution decomposition
  - Strongest prior-work evidence
  - Derivation map
  - Residual novelty
  - Uncertainties
  - Audit appendix
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from infra.run_context import RunContext


@dataclass
class DerivationEntry:
    """One row in the derivation map: a technical component and its likely source."""
    component: str
    source_paper: str       # paper_id or title
    source_detail: str      # specific section, algorithm, or concept in source
    derivation_type: str    # DUPLICATE | COMBINATION | EQUIVALENT | NOVEL
    confidence: float       # 0.0–1.0


@dataclass
class PriorWorkEntry:
    """One entry in the strongest prior-work evidence section."""
    paper_id: str
    title: str
    year: int
    relevance_note: str     # why this paper is relevant
    derivation_note: str    # what specifically was derived from it


@dataclass
class ReportContent:
    """
    Structured content for a report.md.

    Tracks must populate all required fields before calling ReportWriter.write().
    Optional fields may be left empty — the writer will note their absence.
    """
    context: RunContext

    # --- required sections ---
    executive_summary: str = ""
    decomposition: list[dict[str, Any]] = field(default_factory=list)
    prior_work: list[PriorWorkEntry] = field(default_factory=list)
    derivation_map: list[DerivationEntry] = field(default_factory=list)
    residual_novelty: str = ""
    uncertainties: list[str] = field(default_factory=list)

    # --- audit appendix ---
    tool_call_log: list[dict[str, Any]] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)
    raw_json_blocks: dict[str, Any] = field(default_factory=dict)


class ReportWriter:
    """
    Writes a canonical report.md from a ReportContent.

    Usage:
        writer = ReportWriter(output_path=Path("report.md"))
        writer.write(content)
    """

    VERDICT_LABELS = {
        "NOVEL": "🟢 NOVEL",
        "COMBINATION": "🟡 COMBINATION",
        "EQUIVALENT": "🟠 EQUIVALENT",
        "DUPLICATE": "🔴 DUPLICATE",
    }

    def __init__(self, output_path: Path = Path("report.md")) -> None:
        self.output_path = output_path

    def write(self, content: ReportContent) -> Path:
        """
        Render the report and write it to self.output_path.
        Returns the path of the written file.
        """
        sections = [
            content.context.to_yaml_front_matter(),
            "",
            self._render_title(content),
            self._render_toc(),
            self._render_executive_summary(content),
            self._render_verdict(content),
            self._render_decomposition(content),
            self._render_prior_work(content),
            self._render_derivation_map(content),
            self._render_residual_novelty(content),
            self._render_uncertainties(content),
            self._render_audit_appendix(content),
        ]
        report_text = "\n\n".join(s for s in sections if s)
        self.output_path.write_text(report_text, encoding="utf-8")
        return self.output_path

    # ------------------------------------------------------------------
    # Section renderers
    # ------------------------------------------------------------------

    def _render_title(self, content: ReportContent) -> str:
        ctx = content.context
        return (
            f"# Derivation Audit: {ctx.paper_id}\n\n"
            f"**Track:** {ctx.track}  \n"
            f"**Implementation:** `{ctx.impl_id}`  \n"
            f"**Model:** {ctx.model}  \n"
            f"**Run started:** {ctx.start_time}  \n"
            f"**Run finished:** {ctx.finish_time or '_in progress_'}  \n"
            f"**Git commit:** `{ctx.git_commit}`"
        )

    def _render_toc(self) -> str:
        return (
            "## Table of Contents\n\n"
            "1. [Executive Summary](#executive-summary)\n"
            "2. [Final Verdict](#final-verdict)\n"
            "3. [Technical Contribution Decomposition](#technical-contribution-decomposition)\n"
            "4. [Strongest Prior-Work Evidence](#strongest-prior-work-evidence)\n"
            "5. [Derivation Map](#derivation-map)\n"
            "6. [Residual Novelty](#residual-novelty)\n"
            "7. [Uncertainties](#uncertainties)\n"
            "8. [Audit Appendix](#audit-appendix)"
        )

    def _render_executive_summary(self, content: ReportContent) -> str:
        body = content.executive_summary or "_Not yet populated._"
        return f"## Executive Summary\n\n{body}"

    def _render_verdict(self, content: ReportContent) -> str:
        ctx = content.context
        label = self.VERDICT_LABELS.get(ctx.final_verdict, ctx.final_verdict or "_pending_")
        confidence_pct = f"{ctx.confidence * 100:.0f}%" if ctx.confidence else "_unknown_"
        evidence_lines = ""
        if ctx.main_cited_evidence:
            evidence_lines = "\n\n**Main cited evidence:**\n" + "\n".join(
                f"- {ev}" for ev in ctx.main_cited_evidence
            )
        return (
            f"## Final Verdict\n\n"
            f"**Verdict:** {label}  \n"
            f"**Confidence:** {confidence_pct}"
            f"{evidence_lines}"
        )

    def _render_decomposition(self, content: ReportContent) -> str:
        if not content.decomposition:
            return "## Technical Contribution Decomposition\n\n_Not yet populated._"
        rows = ["| Component | Description |", "|-----------|-------------|"]
        for item in content.decomposition:
            name = item.get("name", "")
            desc = item.get("description", "")
            rows.append(f"| {name} | {desc} |")
        return "## Technical Contribution Decomposition\n\n" + "\n".join(rows)

    def _render_prior_work(self, content: ReportContent) -> str:
        if not content.prior_work:
            return "## Strongest Prior-Work Evidence\n\n_Not yet populated._"
        blocks = []
        for i, pw in enumerate(content.prior_work, 1):
            blocks.append(
                f"### REF-{i}: {pw.title} ({pw.year})\n\n"
                f"**Paper ID:** `{pw.paper_id}`  \n"
                f"**Relevance:** {pw.relevance_note}  \n"
                f"**Derivation note:** {pw.derivation_note}"
            )
        return "## Strongest Prior-Work Evidence\n\n" + "\n\n".join(blocks)

    def _render_derivation_map(self, content: ReportContent) -> str:
        if not content.derivation_map:
            return "## Derivation Map\n\n_Not yet populated._"
        rows = [
            "| Component | Source Paper | Source Detail | Type | Confidence |",
            "|-----------|-------------|---------------|------|------------|",
        ]
        for entry in content.derivation_map:
            conf_pct = f"{entry.confidence * 100:.0f}%"
            rows.append(
                f"| {entry.component} | {entry.source_paper} | "
                f"{entry.source_detail} | {entry.derivation_type} | {conf_pct} |"
            )
        return "## Derivation Map\n\n" + "\n".join(rows)

    def _render_residual_novelty(self, content: ReportContent) -> str:
        body = content.residual_novelty or "_Not yet populated._"
        return f"## Residual Novelty\n\n{body}"

    def _render_uncertainties(self, content: ReportContent) -> str:
        if not content.uncertainties:
            return "## Uncertainties\n\n_None recorded._"
        items = "\n".join(f"- {u}" for u in content.uncertainties)
        return f"## Uncertainties\n\n{items}"

    def _render_audit_appendix(self, content: ReportContent) -> str:
        lines = ["## Audit Appendix"]

        if content.search_queries:
            lines.append("\n### Search Queries\n")
            for q in content.search_queries:
                lines.append(f"- `{q}`")

        if content.tool_call_log:
            lines.append("\n### Tool Calls\n")
            lines.append("| Tool | Summary |")
            lines.append("|------|---------|")
            for call in content.tool_call_log:
                tool = call.get("tool", "")
                summary = call.get("summary", "")
                lines.append(f"| {tool} | {summary} |")

        if content.raw_json_blocks:
            lines.append("\n### Machine-Readable Data\n")
            import json
            for key, data in content.raw_json_blocks.items():
                lines.append(f"**{key}:**\n```json\n{json.dumps(data, indent=2)}\n```")

        return "\n".join(lines)
