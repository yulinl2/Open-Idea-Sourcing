"""Generate Markdown report from perplexity analysis results."""

from __future__ import annotations

import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

from .perplexity import PerplexityResult


def _finite(values: list[float]) -> list[float]:
    """Filter to only finite (non-inf, non-nan) values."""
    return [v for v in values if math.isfinite(v)]


def _stats(values: list[float]) -> dict[str, float]:
    """Compute summary statistics, ignoring non-finite values."""
    vals = _finite(values)
    if not vals:
        return {"n": 0, "mean": 0, "median": 0, "std": 0, "min": 0, "max": 0}
    return {
        "n": len(vals),
        "mean": statistics.mean(vals),
        "median": statistics.median(vals),
        "std": statistics.stdev(vals) if len(vals) > 1 else 0.0,
        "min": min(vals),
        "max": max(vals),
    }


def _fmt(value: float) -> str:
    """Format a float for display, handling inf/nan gracefully."""
    if math.isnan(value):
        return "—"
    if math.isinf(value):
        return "∞ (error)"
    return f"{value:.2f}"


def _fmt_lp(value: float) -> str:
    """Format a logprob value."""
    if not math.isfinite(value):
        return "—"
    return f"{value:.4f}"


def generate_report(
    target_title: str,
    target_source: str,
    results: list[PerplexityResult],
    models: list[str],
    n_cited: int,
    n_extracted: int,
) -> str:
    """Generate a Markdown perplexity analysis report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "---",
        "title: Geo-Perplexity Analysis",
        f'target: "{target_title}"',
        f'source: "{target_source}"',
        f"models: {models}",
        f"generated: {now}",
        "---",
        "",
        f"# Geo-Perplexity Analysis: {target_title}",
        "",
        "## Overview",
        "",
        f"- **Target paper**: {target_title}",
        f"- **Source**: `{target_source}`",
        f"- **Models evaluated**: {', '.join(models)}",
        f"- **Cited references found**: {n_cited}",
        f"- **References with extracted text**: {n_extracted}",
        f"- **Generated**: {now}",
        "",
        "## Methodology",
        "",
        "**Exact conditional perplexity** via verbatim-echo with logprobs:",
        "",
        "1. Reference paper text → system message (~6K tokens context)",
        "2. Target paper text is chunked into ~800-token windows",
        "3. Model is instructed to reproduce each chunk **verbatim**",
        "4. `logprobs=True` returns P(token_i | context, token_1..i-1) for each echoed token",
        "5. **PPL = exp(−(1/N) Σ log p(token_i))** — exact, not approximate",
        "",
        "**Interpretation**: Lower PPL → target is more predictable given that "
        "reference → reference explains more of the target's content. "
        "Higher PPL → target says something the reference doesn't prepare you for.",
        "",
    ]

    for model in models:
        model_results = [r for r in results if r.model == model]
        if not model_results:
            continue

        lines.append(f"## Results: {model}")
        lines.append("")

        # Self-perplexity
        self_results = [r for r in model_results if r.context_type == "self"]
        if self_results:
            r = self_results[0]
            lines.append("### Self-Perplexity (lower bound)")
            lines.append("")
            lines.append(f"PPL(target | target) = **{_fmt(r.perplexity)}**")
            lines.append(f"- Avg logprob: {_fmt_lp(r.avg_logprob)}")
            lines.append(f"- Tokens: {r.n_tokens} across {r.n_chunks} chunks")
            if r.error:
                lines.append(f"- ⚠ Partial: {r.error}")
            lines.append("")

        # Random reference
        random_results = [r for r in model_results if r.context_type == "random"]
        if random_results:
            r = random_results[0]
            lines.append("### Random Field Reference (control)")
            lines.append("")
            lines.append(f"PPL(target | random) = **{_fmt(r.perplexity)}**")
            lines.append(f"- Reference: {r.context_title}")
            lines.append(f"- Avg logprob: {_fmt_lp(r.avg_logprob)}")
            lines.append(f"- Tokens: {r.n_tokens} across {r.n_chunks} chunks")
            if r.error:
                lines.append(f"- ⚠ Partial: {r.error}")
            lines.append("")

        # Cited papers
        cited_results = [r for r in model_results if r.context_type == "cited"]
        if not cited_results:
            continue

        valid_ppls = _finite([r.perplexity for r in cited_results])
        errored = [r for r in cited_results if not math.isfinite(r.perplexity)]
        st = _stats([r.perplexity for r in cited_results])

        lines.append("### Cited Reference Perplexities")
        lines.append("")

        if st["n"] > 0:
            lines.append(f"**Statistics** (n={st['n']} valid, {len(errored)} errored):")
            lines.append(f"- Mean: {st['mean']:.2f}")
            lines.append(f"- Median: {st['median']:.2f}")
            lines.append(f"- Std: {st['std']:.2f}")
            lines.append(f"- Range: [{st['min']:.2f}, {st['max']:.2f}]")
        else:
            lines.append(f"**No valid perplexity scores** ({len(errored)} errors)")
        lines.append("")

        # Full table sorted by perplexity (finite first, then errors)
        finite_cited = sorted(
            [r for r in cited_results if math.isfinite(r.perplexity)],
            key=lambda r: r.perplexity,
        )
        error_cited = [r for r in cited_results if not math.isfinite(r.perplexity)]

        lines.append("| Rank | PPL | Avg LogProb | Tokens | Chunks | Reference |")
        lines.append("|------|-----|-------------|--------|--------|-----------|")
        for i, r in enumerate(finite_cited + error_cited, 1):
            title_short = r.context_title[:55]
            if len(r.context_title) > 55:
                title_short += "…"
            err_mark = " ⚠" if r.error else ""
            lines.append(
                f"| {i} | {_fmt(r.perplexity)} | {_fmt_lp(r.avg_logprob)} | "
                f"{r.n_tokens} | {r.n_chunks} | {title_short}{err_mark} |"
            )
        lines.append("")

        # Text histogram (only finite values)
        if len(valid_ppls) >= 3:
            lines.append("### Distribution")
            lines.append("")
            lines.append("```")
            lines.extend(_text_histogram(valid_ppls))
            lines.append("```")
            lines.append("")

    # Model comparison
    if len(models) > 1:
        lines.append("## Model Comparison")
        lines.append("")
        lines.append("| Metric | " + " | ".join(models) + " |")
        lines.append("|--------" + "|--------" * len(models) + "|")

        for ctx_type, label in [
            ("self", "Self PPL"),
            ("random", "Random PPL"),
            ("cited", "Mean Cited PPL"),
            ("cited", "Median Cited PPL"),
        ]:
            row = f"| {label} "
            for model in models:
                mrs = [r for r in results if r.model == model and r.context_type == ctx_type]
                if ctx_type == "cited":
                    vals = _finite([r.perplexity for r in mrs])
                    if "Median" in label:
                        val = statistics.median(vals) if vals else float("nan")
                    else:
                        val = statistics.mean(vals) if vals else float("nan")
                else:
                    val = mrs[0].perplexity if mrs else float("nan")
                row += f"| {_fmt(val)} "
            row += "|"
            lines.append(row)
        lines.append("")

    # Errors summary
    errors = [r for r in results if r.error]
    if errors:
        lines.append(f"## Errors ({len(errors)} total)")
        lines.append("")
        for r in errors:
            lines.append(f"- **{r.model}** | {r.context_title[:50]}: {r.error}")
        lines.append("")

    return "\n".join(lines)


def _text_histogram(values: list[float], bins: int = 12, width: int = 40) -> list[str]:
    """Generate a text-based histogram of finite values."""
    vals = _finite(values)
    if not vals:
        return ["(no data)"]

    lo, hi = min(vals), max(vals)
    if lo == hi:
        return [f"  All values = {lo:.2f}"]

    bin_width = (hi - lo) / bins
    counts = [0] * bins
    for v in vals:
        idx = min(int((v - lo) / bin_width), bins - 1)
        counts[idx] += 1

    max_count = max(counts) if counts else 1
    lines = []
    for i, count in enumerate(counts):
        bar_len = int(count / max_count * width) if max_count > 0 else 0
        lo_val = lo + i * bin_width
        hi_val = lo_val + bin_width
        bar = "█" * bar_len
        lines.append(f"  {lo_val:7.1f}–{hi_val:7.1f} │ {bar} ({count})")

    return lines


def save_report(report: str, output_dir: str | Path, filename: str = "report.md") -> Path:
    """Save report to the output directory."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename
    path.write_text(report, encoding="utf-8")
    return path
