"""Format a :class:`NoveltyReport` into human-readable output.

Two formats are supported:

* ``"text"`` — plain-text report suitable for terminal output.
* ``"markdown"`` — Markdown-formatted report suitable for embedding in
  GitHub issues, wikis, or PDF renderers.
* ``"json"`` — machine-readable JSON representation.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Literal

from .novelty_evaluator import NoveltyReport

OutputFormat = Literal["text", "markdown", "json"]

_VERDICT_EMOJI = {
    "NOVEL": "✅",
    "MARGINAL": "⚠️",
    "NOT_NOVEL": "❌",
    "UNCLEAR": "❓",
}

_DIM_EMOJI = {
    "HIGH": "🔴",
    "MEDIUM": "🟡",
    "LOW": "🟢",
    "UNCLEAR": "❓",
}


class ReportGenerator:
    """Convert a :class:`NoveltyReport` to a formatted string."""

    def generate(
        self, report: NoveltyReport, fmt: OutputFormat = "text"
    ) -> str:
        """Return the report formatted as *fmt*."""
        if fmt == "json":
            return self._to_json(report)
        if fmt == "markdown":
            return self._to_markdown(report)
        return self._to_text(report)

    # ------------------------------------------------------------------
    # Plain text
    # ------------------------------------------------------------------

    def _to_text(self, r: NoveltyReport) -> str:
        lines: list[str] = [
            "=" * 70,
            f"NOVELTY EVALUATION REPORT",
            "=" * 70,
            f"Paper  : {r.paper_title}",
            f"Verdict: {r.overall_verdict}  (confidence: {r.confidence})",
            "",
            "SUMMARY",
            "-" * 70,
            r.summary,
            "",
        ]
        for dim in r.dimensions:
            lines += [
                f"{dim.name.upper()}",
                f"  Risk level : {dim.verdict}",
                f"  Explanation: {dim.explanation}",
            ]
            if dim.references:
                lines.append(f"  References : {', '.join(dim.references)}")
            lines.append("")

        if r.similar_papers:
            lines += ["MOST SIMILAR REFERENCE PAPERS", "-" * 70]
            for res in r.similar_papers:
                p = res.paper
                year = f" ({p.year})" if p.year else ""
                lines.append(f"  [{res.score:.2f}] {p.title}{year}")
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Markdown
    # ------------------------------------------------------------------

    def _to_markdown(self, r: NoveltyReport) -> str:
        ov = _VERDICT_EMOJI.get(r.overall_verdict, "❓")
        lines: list[str] = [
            f"# Novelty Evaluation: {r.paper_title}",
            "",
            f"**Overall verdict:** {ov} **{r.overall_verdict}** "
            f"(confidence: {r.confidence})",
            "",
            "## Summary",
            "",
            r.summary,
            "",
            "## Detailed Analysis",
            "",
        ]
        for dim in r.dimensions:
            icon = _DIM_EMOJI.get(dim.verdict, "❓")
            lines += [
                f"### {dim.name}",
                "",
                f"**Risk level:** {icon} {dim.verdict}",
                "",
                dim.explanation,
                "",
            ]
            if dim.references:
                lines += [
                    "**Cited references:** "
                    + ", ".join(f"`{ref}`" for ref in dim.references),
                    "",
                ]

        if r.similar_papers:
            lines += [
                "## Most Similar Reference Papers",
                "",
                "| Score | Title | Year |",
                "|-------|-------|------|",
            ]
            for res in r.similar_papers:
                p = res.paper
                year = str(p.year) if p.year else "—"
                title = p.title.replace("|", "\\|")
                lines.append(f"| {res.score:.2f} | {title} | {year} |")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    @staticmethod
    def _to_json(r: NoveltyReport) -> str:
        data = {
            "paper_title": r.paper_title,
            "overall_verdict": r.overall_verdict,
            "confidence": r.confidence,
            "summary": r.summary,
            "dimensions": [
                {
                    "name": d.name,
                    "verdict": d.verdict,
                    "explanation": d.explanation,
                    "references": d.references,
                }
                for d in r.dimensions
            ],
            "similar_papers": [
                {
                    "score": res.score,
                    "id": res.paper.id,
                    "title": res.paper.title,
                    "year": res.paper.year,
                }
                for res in r.similar_papers
            ],
        }
        return json.dumps(data, indent=2)
