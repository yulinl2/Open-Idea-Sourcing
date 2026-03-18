"""Format a :class:`NoveltyReport` into human-readable output.

Four formats are supported:

* ``"text"`` — plain-text report suitable for terminal output.
* ``"markdown"`` — Markdown-formatted report suitable for embedding in
  GitHub issues, wikis, or PDF renderers.
* ``"json"`` — machine-readable JSON representation.
* ``"pdf"`` — PDF document rendered from Markdown (requires the
  ``markdown`` and ``weasyprint`` packages).

A :func:`suggest_filename` helper builds an informative output filename
from the report content and run metadata.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from .novelty_evaluator import NoveltyReport, RunMetadata

OutputFormat = Literal["text", "markdown", "json", "pdf"]

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

# Minimal CSS for the PDF HTML template — intentionally simple so there are
# no external resource fetches and the output is self-contained.
_PDF_CSS = """
body { font-family: sans-serif; max-width: 800px; margin: 40px auto; font-size: 14px; }
h1 { font-size: 1.6em; border-bottom: 2px solid #333; padding-bottom: 6px; }
h2 { font-size: 1.25em; margin-top: 1.4em; }
h3 { font-size: 1.05em; margin-top: 1.2em; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
th { background: #f5f5f5; }
blockquote { border-left: 4px solid #aaa; margin: 0; padding: 6px 16px; color: #555; }
code { background: #f0f0f0; padding: 1px 4px; border-radius: 3px; }
pre code { display: block; padding: 10px; }
"""


_NY_TZ = ZoneInfo("America/New_York")


def _fmt_datetime_ny(ts: str) -> str:
    """Format an ISO 8601 UTC timestamp as a human-readable New York time string.

    Converts *ts* to America/New_York (EDT or EST, auto-selected by date) and
    formats the result as ``YYYY-MM-DD HH:MM:SS EDT/EST`` for human readability.
    Returns *ts* unchanged if it cannot be parsed.
    """
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone(_NY_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    except ValueError:
        return ts


def suggest_filename(report: NoveltyReport, fmt: str = "markdown") -> str:
    """Return an informative filename for *report* in output format *fmt*.

    The filename encodes the paper title (truncated and sanitised) and the
    run timestamp (when available) so that reports are easy to distinguish
    and sort chronologically.

    Examples
    --------
    >>> # report with title "Attention Is All You Need" run at 2024-06-01T12:00:00Z
    >>> suggest_filename(report, "markdown")
    'Attention_Is_All_You_Need_2024-06-01T120000.md'
    """
    ext_map = {"text": "txt", "markdown": "md", "json": "json", "pdf": "pdf"}
    ext = ext_map.get(fmt, "txt")

    # Sanitise the paper title: keep letters, digits, spaces and hyphens.
    safe_title = re.sub(r"[^\w\s-]", "", report.paper_title or "untitled")
    safe_title = re.sub(r"\s+", "_", safe_title.strip())[:60]

    timestamp = ""
    if report.metadata and report.metadata.timestamp:
        ts = report.metadata.timestamp
        try:
            # Parse the ISO 8601 timestamp and format as YYYY-MM-DDTHHMMSS so
            # that same-day re-runs produce distinct filenames.  Colons are
            # stripped to keep the name filesystem-safe on all platforms.
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            timestamp = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
        except ValueError:
            # Malformed timestamp: fall back to whatever prefix looks like a date.
            timestamp = ts[:10]

    parts = [p for p in (safe_title, timestamp) if p]
    return "_".join(parts) + f".{ext}"


class ReportGenerator:
    """Convert a :class:`NoveltyReport` to a formatted string or PDF file."""

    def generate(
        self, report: NoveltyReport, fmt: OutputFormat = "text"
    ) -> str:
        """Return the report as a formatted *string* for *fmt*.

        For the ``"pdf"`` format use :meth:`generate_pdf` instead; calling
        ``generate`` with ``fmt="pdf"`` returns the underlying Markdown string
        so that the output can still be inspected without PDF tooling.
        """
        if fmt == "json":
            return self._to_json(report)
        if fmt == "markdown" or fmt == "pdf":
            return self._to_markdown(report)
        return self._to_text(report)

    def generate_pdf(self, report: NoveltyReport, output_path: Path) -> None:
        """Render *report* as a PDF and write it to *output_path*.

        The report is first converted to Markdown, then to HTML, and finally
        to PDF using ``weasyprint``.  Both the ``markdown`` and ``weasyprint``
        packages must be installed; a clear :class:`RuntimeError` is raised if
        either is missing.

        Parameters
        ----------
        report:
            The :class:`~novelty_evaluator.NoveltyReport` to render.
        output_path:
            Destination file path (typically ending in ``.pdf``).
        """
        try:
            import markdown as md_lib  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "The 'markdown' package is required for PDF output.\n"
                "Install it with:  pip install markdown"
            ) from exc

        try:
            import weasyprint  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "The 'weasyprint' package is required for PDF output.\n"
                "Install it with:  pip install weasyprint"
            ) from exc

        markdown_text = self._to_markdown(report)
        html_body = md_lib.markdown(
            markdown_text,
            extensions=["tables", "fenced_code"],
        )
        html = (
            "<!DOCTYPE html>\n"
            "<html><head><meta charset='utf-8'>"
            f"<style>{_PDF_CSS}</style></head>"
            f"<body>{html_body}</body></html>"
        )
        weasyprint.HTML(string=html).write_pdf(str(output_path))

    # ------------------------------------------------------------------
    # Plain text
    # ------------------------------------------------------------------

    def _to_text(self, r: NoveltyReport) -> str:
        lines: list[str] = [
            "=" * 70,
            "NOVELTY EVALUATION REPORT",
            "=" * 70,
        ]

        if r.metadata:
            m = r.metadata
            lines += ["RUN METADATA", "-" * 70]

            lines.append("  [Run Context]")
            if m.timestamp:
                lines.append(f"    Timestamp   : {_fmt_datetime_ny(m.timestamp)}")
            if m.git_branch:
                lines.append(f"    Branch      : {m.git_branch}")
            if m.git_commit:
                lines.append(f"    Commit      : {m.git_commit}")
            if m.ci_run_url:
                lines.append(f"    CI Run      : {m.ci_run_url}")
            if m.pr_number:
                lines.append(f"    PR          : #{m.pr_number}")

            lines.append("  [Configuration]")
            if m.model:
                lines.append(f"    Model       : {m.model}")
            if m.input_source:
                lines.append(f"    Input       : {m.input_source}")
            if m.code_version:
                lines.append(f"    Code version: {m.code_version}")

            if m.total_runtime_seconds or m.stage_runtimes:
                lines.append("  [Performance]")
                if m.total_runtime_seconds:
                    lines.append(
                        f"    Total time  : {m.total_runtime_seconds:.1f}s"
                    )
                if m.stage_runtimes:
                    lines.append("    Stage times :")
                    for stage, secs in m.stage_runtimes.items():
                        lines.append(f"      {stage}: {secs:.1f}s")
            lines.append("")

        if r.metadata and r.metadata.jobs:
            lines += ["PIPELINE JOB LOG", "-" * 70]
            for i, job in enumerate(r.metadata.jobs, 1):
                lines.append(
                    f"  {i:2d}. {job.name:<25s}  agent={job.agent}"
                    f"  t+{job.offset_s:.1f}s  dur={job.duration_s:.1f}s"
                )
                lines.append(f"       in : {job.input_summary}")
                lines.append(f"       out: {job.output_summary}")
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

        if r.metadata:
            m = r.metadata
            lines += ["## Run Metadata", ""]

            # --- Run context group ---
            context_rows = []
            if m.timestamp:
                context_rows.append(("Timestamp", _fmt_datetime_ny(m.timestamp)))
            if m.git_branch:
                context_rows.append(("Branch", m.git_branch))
            if m.git_commit:
                commit_val = (
                    f"[`{m.git_commit}`]({m.git_commit_url})"
                    if m.git_commit_url
                    else f"`{m.git_commit}`"
                )
                context_rows.append(("Commit", commit_val))
            if m.ci_run_url:
                # ci_run_url is expected to have the form
                # https://github.com/<owner>/<repo>/actions/runs/<run_id>
                # Extract the run ID from the last path segment for a short label.
                run_num = m.ci_run_url.rstrip("/").rsplit("/", 1)[-1]
                label = f"Run #{run_num}" if run_num.isdigit() else "CI Run"
                context_rows.append(("CI Run", f"[{label}]({m.ci_run_url})"))
            if m.pr_number:
                _gh_server = m.git_commit_url.split("/commit/")[0] if m.git_commit_url else ""
                pr_val = (
                    f"[#{m.pr_number}]({_gh_server}/pull/{m.pr_number})"
                    if _gh_server
                    else f"#{m.pr_number}"
                )
                context_rows.append(("PR", pr_val))
            if context_rows:
                lines += [
                    "**Run context**",
                    "",
                    "| Field | Value |",
                    "|-------|-------|",
                ]
                for field_name, value in context_rows:
                    lines.append(
                        f"| {field_name} | {str(value).replace('|', r'\|')} |"
                    )
                lines.append("")

            # --- Configuration group ---
            config_rows = []
            if m.model:
                config_rows.append(("Model", m.model))
            if m.input_source:
                config_rows.append(("Input", m.input_source))
            if m.code_version:
                config_rows.append(("Code version", m.code_version))
            if config_rows:
                lines += [
                    "**Configuration**",
                    "",
                    "| Field | Value |",
                    "|-------|-------|",
                ]
                for field_name, value in config_rows:
                    lines.append(
                        f"| {field_name} | {str(value).replace('|', r'\|')} |"
                    )
                lines.append("")

            # --- Performance group ---
            perf_rows: list[tuple[str, str]] = []
            if m.total_runtime_seconds:
                perf_rows.append(("Total runtime", f"{m.total_runtime_seconds:.1f}s"))
            for stage, secs in (m.stage_runtimes or {}).items():
                perf_rows.append((f"└─ {stage}", f"{secs:.1f}s"))
            if perf_rows:
                lines += [
                    "**Performance**",
                    "",
                    "| Field | Value |",
                    "|-------|-------|",
                ]
                for field_name, value in perf_rows:
                    lines.append(
                        f"| {field_name} | {str(value).replace('|', r'\|')} |"
                    )
                lines.append("")

        if r.metadata and r.metadata.jobs:
            lines += [
                "## Pipeline Job Log",
                "",
                _build_gantt(r.metadata, r.paper_title),
                "",
                "| # | Job | Agent | Start (s) | Duration (s) | Input | Output |",
                "|---|-----|-------|----------:|-------------:|-------|--------|",
            ]
            for i, job in enumerate(r.metadata.jobs, 1):
                lines.append(
                    f"| {i} | {job.name} | {job.agent} "
                    f"| {job.offset_s:.2f} | {job.duration_s:.2f} "
                    f"| {job.input_summary} | {job.output_summary} |"
                )
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
        if r.metadata:
            m = r.metadata
            data["metadata"] = {
                "model": m.model,
                "input_source": m.input_source,
                "timestamp": m.timestamp,
                "total_runtime_seconds": m.total_runtime_seconds,
                "stage_runtimes": m.stage_runtimes,
                "code_version": m.code_version,
                "git_branch": m.git_branch,
                "git_commit": m.git_commit,
                "git_commit_url": m.git_commit_url,
                "ci_run_url": m.ci_run_url,
                "pr_number": m.pr_number,
                "jobs": [
                    {
                        "name": j.name,
                        "agent": j.agent,
                        "offset_s": j.offset_s,
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
    """Return a Mermaid ``gantt`` diagram string for *metadata.jobs*.

    Timestamps are expressed as millisecond offsets from the run start so
    that the chart renders correctly regardless of wall-clock date.
    """
    chart_title = paper_title or "Novelty Evaluation"
    lines = [
        "```mermaid",
        "gantt",
        f"    title Pipeline Run — {chart_title}",
        "    dateFormat x",
        "    axisFormat %S.%Ls",
    ]

    section: str | None = None
    for job in metadata.jobs:
        agent_section = job.agent
        if agent_section != section:
            section = agent_section
            lines.append(f"    section {section}")
        start_ms = int(job.offset_s * 1000)
        dur_ms = max(1, int(job.duration_s * 1000))
        safe_name = job.name.replace(":", " -")
        lines.append(f"    {safe_name} :done, {start_ms}, {dur_ms}ms")

    lines.append("```")
    return "\n".join(lines)
