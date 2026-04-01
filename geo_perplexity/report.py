"""Generate Markdown report from perplexity analysis results."""

from __future__ import annotations

import statistics
from datetime import datetime, timezone
from pathlib import Path

from .perplexity import PerplexityResult


def _stats(values: list[float]) -> dict[str, float]:
    """Compute summary statistics for a list of perplexity values."""
    if not values:
        return {"mean": 0, "median": 0, "std": 0, "min": 0, "max": 0}
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


def _format_ppl(ppl: float) -> str:
    if ppl == float("inf"):
        return "∞ (error)"
    return f"{ppl:.2f}"


def generate_report(
    target_title: str,
    target_source: str,
    results: list[PerplexityResult],
    models: list[str],
    n_cited: int,
    n_extracted: int,
) -> str:
    """Generate a Markdown perplexity analysis report.

    Parameters
    ----------
    target_title:
        Title of the target paper.
    target_source:
        Source URL or file path of the target paper.
    results:
        All PerplexityResult objects from the analysis.
    models:
        List of model names used.
    n_cited:
        Total number of cited references found.
    n_extracted:
        Number of cited references with extracted text.

    Returns
    -------
    str
        Complete Markdown report.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "---",
        f"title: Geo-Perplexity Analysis",
        f"target: \"{target_title}\"",
        f"source: \"{target_source}\"",
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
        "Perplexity is estimated using conditional generation logprobs:",
        "1. Context paper text placed in system message (~4K tokens)",
        "2. First ~40% of target paper as prompt prefix",
        "3. Model generates continuation with `logprobs=True`",
        "4. PPL = exp(-mean(token_logprobs))",
        "",
        "**Interpretation**: Lower PPL → target is more predictable given context "
        "→ less novel. Higher PPL → more surprising → more novel.",
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
            self_ppl = self_results[0]
            lines.append(f"### Self-Perplexity (baseline)")
            lines.append("")
            lines.append(f"PPL(target | target) = **{_format_ppl(self_ppl.perplexity)}**")
            lines.append(f"- Avg logprob: {self_ppl.avg_logprob:.4f}")
            lines.append(f"- Tokens evaluated: {self_ppl.n_tokens}")
            if self_ppl.error:
                lines.append(f"- Error: {self_ppl.error}")
            lines.append("")

        # Random reference
        random_results = [r for r in model_results if r.context_type == "random"]
        if random_results:
            rand_ppl = random_results[0]
            lines.append(f"### Random Field Reference (baseline)")
            lines.append("")
            lines.append(f"PPL(target | random) = **{_format_ppl(rand_ppl.perplexity)}**")
            lines.append(f"- Reference: {rand_ppl.context_title}")
            lines.append(f"- Avg logprob: {rand_ppl.avg_logprob:.4f}")
            lines.append(f"- Tokens evaluated: {rand_ppl.n_tokens}")
            if rand_ppl.error:
                lines.append(f"- Error: {rand_ppl.error}")
            lines.append("")

        # Cited papers
        cited_results = [r for r in model_results if r.context_type == "cited"]
        if not cited_results:
            continue

        valid_ppls = [r.perplexity for r in cited_results if r.perplexity != float("inf")]
        st = _stats(valid_ppls)

        lines.append(f"### Cited Reference Perplexities")
        lines.append("")
        lines.append(f"**Statistics** (n={len(valid_ppls)} valid of {len(cited_results)} total):")
        lines.append(f"- Mean: {st['mean']:.2f}")
        lines.append(f"- Median: {st['median']:.2f}")
        lines.append(f"- Std: {st['std']:.2f}")
        lines.append(f"- Min: {st['min']:.2f}")
        lines.append(f"- Max: {st['max']:.2f}")
        lines.append("")

        # Full table sorted by perplexity
        sorted_cited = sorted(cited_results, key=lambda r: r.perplexity)
        lines.append("| Rank | PPL | Avg LogProb | Tokens | Reference |")
        lines.append("|------|-----|-------------|--------|-----------|")
        for i, r in enumerate(sorted_cited, 1):
            title_short = r.context_title[:60] + ("..." if len(r.context_title) > 60 else "")
            err = " ⚠️" if r.error else ""
            lines.append(
                f"| {i} | {_format_ppl(r.perplexity)} | {r.avg_logprob:.4f} | "
                f"{r.n_tokens} | {title_short}{err} |"
            )
        lines.append("")

        # Text histogram
        if valid_ppls:
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
        lines.append("|--------" + "|------" * len(models) + "|")

        for ctx_type, label in [("self", "Self PPL"), ("random", "Random PPL"), ("cited", "Mean Cited PPL")]:
            row = f"| {label} "
            for model in models:
                model_type_results = [
                    r for r in results
                    if r.model == model and r.context_type == ctx_type
                ]
                if ctx_type == "cited":
                    vals = [r.perplexity for r in model_type_results if r.perplexity != float("inf")]
                    val = statistics.mean(vals) if vals else float("inf")
                else:
                    val = model_type_results[0].perplexity if model_type_results else float("inf")
                row += f"| {_format_ppl(val)} "
            row += "|"
            lines.append(row)
        lines.append("")

    # Errors summary
    errors = [r for r in results if r.error]
    if errors:
        lines.append("## Errors")
        lines.append("")
        for r in errors:
            lines.append(f"- **{r.model}** | {r.context_title[:40]}: {r.error}")
        lines.append("")

    return "\n".join(lines)


def _text_histogram(values: list[float], bins: int = 15, width: int = 40) -> list[str]:
    """Generate a text-based histogram."""
    if not values:
        return ["(no data)"]

    lo, hi = min(values), max(values)
    if lo == hi:
        return [f"  All values = {lo:.2f}"]

    bin_width = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        idx = min(int((v - lo) / bin_width), bins - 1)
        counts[idx] += 1

    max_count = max(counts)
    lines = []
    for i, count in enumerate(counts):
        bar_len = int(count / max_count * width) if max_count > 0 else 0
        lo_val = lo + i * bin_width
        hi_val = lo_val + bin_width
        bar = "█" * bar_len
        lines.append(f"  {lo_val:7.1f}-{hi_val:7.1f} | {bar} ({count})")

    return lines


def save_report(report: str, output_dir: str | Path, filename: str = "report.md") -> Path:
    """Save report to the output directory."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename
    path.write_text(report, encoding="utf-8")
    return path
