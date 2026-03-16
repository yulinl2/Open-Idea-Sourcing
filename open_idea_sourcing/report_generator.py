"""Format a :class:`NoveltyReport` into human-readable output.

Three formats are supported:

* ``"text"`` — plain-text report suitable for terminal output.
* ``"markdown"`` — Markdown-formatted report suitable for embedding in
  GitHub issues, wikis, or PDF renderers.
* ``"json"`` — machine-readable JSON representation.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Literal

from .novelty_evaluator import NoveltyReport, RunMetadata

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


def suggest_filename(paper_title: str, fmt: OutputFormat) -> str:
    """Return a filename derived from *paper_title* (no ``report`` prefix).

    The title is slugified (lowercase, non-alphanumeric characters replaced
    with hyphens, runs of hyphens collapsed, result truncated to 80 chars)
    and given the extension that matches *fmt*.

    Examples
    --------
    >>> suggest_filename("Attention Is All You Need", "markdown")
    'attention-is-all-you-need.md'
    >>> suggest_filename("BERT: Pre-training of Deep Bidirectional Transformers", "json")
    'bert-pre-training-of-deep-bidirectional-transformers.json'
    """
    slug = paper_title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if len(slug) > 80:
        slug = slug[:80].rstrip("-")
    if not slug:
        slug = "novelty-report"
    ext = {"json": "json", "text": "txt", "markdown": "md"}.get(fmt, "md")
    return f"{slug}.{ext}"


def _fmt_datetime(dt: datetime) -> str:
    """Format *dt* for display in reports.

    If *dt* is timezone-aware it is converted to UTC and the string is
    labelled ``UTC``.  Naive datetimes are formatted as-is without a
    timezone label.
    """
    if dt.tzinfo is not None:
        utc = dt.astimezone(timezone.utc)
        return utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


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
        ]

        if r.metadata is not None:
            m = r.metadata
            lines += [
                "RUN METADATA",
                "-" * 70,
                f"  Paper source : {m.paper_source}",
                f"  Model        : {m.model_name}",
                f"  Started      : {_fmt_datetime(m.started_at)}",
            ]
            if m.finished_at is not None:
                total = (m.finished_at - m.started_at).total_seconds()
                lines.append(f"  Total time   : {total:.1f}s")
            lines.append("")

        lines += [
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

        if r.metadata is not None and r.metadata.jobs:
            lines += ["PIPELINE JOB LOG", "-" * 70]
            run_start = r.metadata.started_at
            for i, job in enumerate(r.metadata.jobs, 1):
                offset = (job.started_at - run_start).total_seconds()
                lines.append(
                    f"  {i:2d}. {job.name:<25s}  agent={job.agent}"
                    f"  t+{offset:.1f}s  dur={job.duration_s:.1f}s"
                )
                lines.append(f"       in : {job.input_summary}")
                lines.append(f"       out: {job.output_summary}")
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
        ]

        if r.metadata is not None:
            m = r.metadata
            lines += [
                "## Run Metadata",
                "",
                "| Field | Value |",
                "|-------|-------|",
                f"| Paper source | `{m.paper_source}` |",
                f"| Model | `{m.model_name}` |",
                f"| Started | {_fmt_datetime(m.started_at)} |",
            ]
            if m.finished_at is not None:
                total = (m.finished_at - m.started_at).total_seconds()
                lines.append(f"| Total time | {total:.1f}s |")
            lines.append("")

        lines += [
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

        if r.metadata is not None and r.metadata.jobs:
            lines += [
                "## Pipeline Job Log",
                "",
                _build_gantt(r.metadata, r.paper_title),
                "",
                "| # | Job | Agent | Start (s) | Duration (s) | Input | Output |",
                "|---|-----|-------|----------:|-------------:|-------|--------|",
            ]
            run_start = r.metadata.started_at
            for i, job in enumerate(r.metadata.jobs, 1):
                offset = (job.started_at - run_start).total_seconds()
                lines.append(
                    f"| {i} | {job.name} | {job.agent} "
                    f"| {offset:.2f} | {job.duration_s:.2f} "
                    f"| {job.input_summary} | {job.output_summary} |"
                )
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    @staticmethod
    def _to_json(r: NoveltyReport) -> str:
        data: dict = {
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
        if r.metadata is not None:
            m = r.metadata
            data["metadata"] = {
                "paper_source": m.paper_source,
                "model_name": m.model_name,
                "started_at": m.started_at.isoformat(),
                "finished_at": m.finished_at.isoformat() if m.finished_at else None,
                "total_duration_s": (
                    (m.finished_at - m.started_at).total_seconds()
                    if m.finished_at else None
                ),
                "jobs": [
                    {
                        "name": j.name,
                        "agent": j.agent,
                        "started_at": j.started_at.isoformat(),
                        "finished_at": j.finished_at.isoformat(),
                        "duration_s": j.duration_s,
                        "input_summary": j.input_summary,
                        "output_summary": j.output_summary,
                    }
                    for j in m.jobs
                ],
            }
        return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Pipeline Gantt chart (Mermaid)
# ---------------------------------------------------------------------------

def _build_gantt(metadata: RunMetadata, paper_title: str = "") -> str:
    """Return a Mermaid ``gantt`` diagram string for *metadata*.

    Timestamps are expressed as millisecond offsets from the run start so
    that the chart renders correctly regardless of wall-clock date.
    """
    run_start = metadata.started_at
    chart_title = paper_title or "Novelty Evaluation"
    lines = [
        "```mermaid",
        "gantt",
        f"    title Pipeline Run — {chart_title}",
        "    dateFormat x",
        "    axisFormat %S.%Ls",
    ]

    # Group jobs by section (agent type)
    section: str | None = None
    for job in metadata.jobs:
        agent_section = job.agent
        if agent_section != section:
            section = agent_section
            lines.append(f"    section {section}")
        start_ms = int((job.started_at - run_start).total_seconds() * 1000)
        dur_ms = max(1, int(job.duration_s * 1000))
        # Sanitise job name for Mermaid (colons cause parse errors)
        safe_name = job.name.replace(":", " -")
        lines.append(f"    {safe_name} :done, {start_ms}, {dur_ms}ms")

    lines.append("```")
    return "\n".join(lines)
