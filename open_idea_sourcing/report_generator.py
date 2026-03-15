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
from pathlib import Path
from typing import Literal

from .novelty_evaluator import NoveltyReport

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


def suggest_filename(report: NoveltyReport, fmt: str = "markdown") -> str:
    """Return an informative filename for *report* in output format *fmt*.

    The filename encodes the paper title (truncated and sanitised) and the
    run timestamp (when available) so that reports are easy to distinguish
    and sort chronologically.

    Examples
    --------
    >>> # report with title "Attention Is All You Need" run on 2024-06-01
    >>> suggest_filename(report, "markdown")
    'novelty_report_Attention_Is_All_You_Need_2024-06-01.md'
    """
    ext_map = {"text": "txt", "markdown": "md", "json": "json", "pdf": "pdf"}
    ext = ext_map.get(fmt, "txt")

    # Sanitise the paper title: keep letters, digits, spaces and hyphens.
    safe_title = re.sub(r"[^\w\s-]", "", report.paper_title or "untitled")
    safe_title = re.sub(r"\s+", "_", safe_title.strip())[:60]

    timestamp = ""
    if report.metadata and report.metadata.timestamp:
        # Use the date part only (YYYY-MM-DD) to keep the filename readable.
        timestamp = report.metadata.timestamp[:10]

    parts = [p for p in ("novelty_report", safe_title, timestamp) if p]
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

        if r.metadata:
            m = r.metadata
            lines += ["RUN METADATA", "-" * 70]
            if m.timestamp:
                lines.append(f"  Timestamp   : {m.timestamp}")
            if m.model:
                lines.append(f"  Model       : {m.model}")
            if m.input_source:
                lines.append(f"  Input       : {m.input_source}")
            if m.code_version:
                lines.append(f"  Code version: {m.code_version}")
            if m.total_runtime_seconds:
                lines.append(
                    f"  Total time  : {m.total_runtime_seconds:.1f}s"
                )
            if m.stage_runtimes:
                lines.append("  Stage times :")
                for stage, secs in m.stage_runtimes.items():
                    lines.append(f"    {stage}: {secs:.1f}s")
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

        if r.metadata:
            m = r.metadata
            lines += ["## Run Metadata", ""]
            rows = []
            if m.timestamp:
                rows.append(("Timestamp", m.timestamp))
            if m.model:
                rows.append(("Model", m.model))
            if m.input_source:
                rows.append(("Input", m.input_source))
            if m.code_version:
                rows.append(("Code version", m.code_version))
            if m.total_runtime_seconds:
                rows.append(("Total runtime", f"{m.total_runtime_seconds:.1f}s"))
            for stage, secs in (m.stage_runtimes or {}).items():
                rows.append((f"  {stage}", f"{secs:.1f}s"))
            if rows:
                lines += [
                    "| Field | Value |",
                    "|-------|-------|",
                ]
                for field_name, value in rows:
                    lines.append(
                        f"| {field_name} | {str(value).replace('|', chr(124))} |"
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
        if r.metadata:
            m = r.metadata
            data["metadata"] = {
                "model": m.model,
                "input_source": m.input_source,
                "timestamp": m.timestamp,
                "total_runtime_seconds": m.total_runtime_seconds,
                "stage_runtimes": m.stage_runtimes,
                "code_version": m.code_version,
            }
        return json.dumps(data, indent=2)
