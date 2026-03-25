#!/usr/bin/env python3
"""report_review_agent.py — LLM-powered quality assessment of generated novelty reports.

This script acts as a second-pass QA layer: after ``review_paper.py``
generates a novelty report, this agent reads it, applies a structured rubric,
and outputs actionable feedback that developers can use to identify prompting,
parsing, or rendering regressions.

In a CI context the feedback is written to the GitHub Actions step summary so
it is visible without leaving the Actions UI. It can also be posted as a PR
comment via the GitHub REST API.

Usage
-----
    # Review a single report:
    python scripts/report_review_agent.py reports/my-report.md

    # Review all reports in a directory:
    python scripts/report_review_agent.py reports/*.md

    # Write feedback to a Markdown file as well:
    python scripts/report_review_agent.py reports/*.md --output-md reports/feedback.md

    # Write to GitHub Actions step summary (CI usage):
    python scripts/report_review_agent.py reports/*.md --github-summary

    # Post as a PR comment (requires GH_TOKEN and PR_NUMBER env vars):
    python scripts/report_review_agent.py reports/*.md --github-summary --post-pr-comment

Requirements
------------
OPENAI_API_KEY   — required (same key used by review_paper.py).
OPENAI_MODEL     — optional, defaults to gpt-4o.
GH_TOKEN         — required when --post-pr-comment is used.
GH_REPO          — owner/repo slug, required when --post-pr-comment is used.
PR_NUMBER        — PR number to comment on, required when --post-pr-comment is used.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import urllib.request
import urllib.parse
from pathlib import Path


# ---------------------------------------------------------------------------
# Rubric prompt
# ---------------------------------------------------------------------------

_RUBRIC_SYSTEM = """\
You are a senior ML researcher reviewing an automatically generated academic
paper novelty-evaluation report. Your job is to assess the *quality of the
report itself* — not to re-evaluate the paper — and to give the development
team actionable feedback they can use to improve the generation pipeline.

Evaluate the report on the following dimensions, each scored 1–5:

1. CONCEPT_TREE_DEPTH (1–5)
   Does the report contain a concept tree?  Does it have ≥3 top-level branches
   (e.g. Problem / Method / Evidence)?  Does it go ≥3 levels deep?  Does it
   expose concrete implementation details (not just high-level labels)?
   Score 1 if absent; 5 if it's a richly detailed multi-level tree.

2. NOVELTY_ANALYSIS_GROUNDING (1–5)
   Are the three novelty dimensions (Duplication / Combination / Equivalence)
   present with specific verdicts?  Are claims backed by named reference papers
   or specific textual evidence?  Score 1 if verdicts are generic; 5 if every
   claim cites a specific source.

3. DOMAIN_REFERENCES_QUALITY (1–5)
   Are domain references present (≥3)?  Are they specific, relevant, and
   correctly tied to the paper's core contribution?  Score 1 if absent or
   generic; 5 if precise and well-justified.

4. REPORT_COHERENCE (1–5)
   Does the overall verdict follow logically from the dimension analyses?
   Is the summary specific (not just a restatement of generic facts)?
   Score 1 if incoherent; 5 if tightly reasoned.

5. PIPELINE_HEALTH (1–5)
   Are there any visible error messages, empty sections, or placeholder text
   (e.g. "N/A", "none identified", timeout errors)?  Score 5 if the pipeline
   ran cleanly; lower scores for each issue found.

Respond in the following exact format (fill in the blanks):

CONCEPT_TREE_DEPTH: <score 1-5>
CONCEPT_TREE_DEPTH_FEEDBACK: <one to three sentences of specific feedback>

NOVELTY_ANALYSIS_GROUNDING: <score 1-5>
NOVELTY_ANALYSIS_GROUNDING_FEEDBACK: <one to three sentences of specific feedback>

DOMAIN_REFERENCES_QUALITY: <score 1-5>
DOMAIN_REFERENCES_QUALITY_FEEDBACK: <one to three sentences of specific feedback>

REPORT_COHERENCE: <score 1-5>
REPORT_COHERENCE_FEEDBACK: <one to three sentences of specific feedback>

PIPELINE_HEALTH: <score 1-5>
PIPELINE_HEALTH_FEEDBACK: <one to three sentences of specific feedback>

TOP_ISSUES:
1. <most important issue to fix, one sentence>
2. <second most important issue, one sentence>
3. <third most important issue, one sentence>

OVERALL_SCORE: <average of the five scores, one decimal>
OVERALL_SUMMARY: <two to four sentences summarising the report quality and the single highest-priority action>
"""

_RUBRIC_USER_TEMPLATE = """\
Please review the following novelty evaluation report:

---
{report_content}
---
"""

# Maximum characters of the report to include in the prompt to stay within
# context limits.  Truncate from the middle (keep header and footer).
_MAX_REPORT_CHARS = 12_000


def _truncate_report(text: str) -> str:
    """Keep the first and last halves of the report when it is too long."""
    if len(text) <= _MAX_REPORT_CHARS:
        return text
    half = _MAX_REPORT_CHARS // 2
    omitted = len(text) - _MAX_REPORT_CHARS
    mid_msg = f"\n\n[... {omitted:,} characters omitted for brevity ...]\n\n"
    return text[:half] + mid_msg + text[-half:]


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def _call_llm(report_content: str, model: str, api_key: str) -> str:
    """Send the report to the LLM and return its assessment text."""
    try:
        import openai
    except ImportError:  # pragma: no cover
        sys.exit("openai package is required: pip install openai")

    client = openai.OpenAI(api_key=api_key)
    user_prompt = _RUBRIC_USER_TEMPLATE.format(
        report_content=_truncate_report(report_content)
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _RUBRIC_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_scores(text: str) -> dict[str, str | float | list[str]]:
    """Extract scores and feedback blobs from the LLM response."""
    import re

    result: dict[str, str | float | list[str]] = {}
    dimensions = [
        "CONCEPT_TREE_DEPTH",
        "NOVELTY_ANALYSIS_GROUNDING",
        "DOMAIN_REFERENCES_QUALITY",
        "REPORT_COHERENCE",
        "PIPELINE_HEALTH",
    ]
    for dim in dimensions:
        m = re.search(rf"{dim}:\s*([1-5])", text)
        result[dim] = int(m.group(1)) if m else 0
        fb_key = dim + "_FEEDBACK"
        fb_m = re.search(
            rf"{fb_key}:\s*(.+?)(?=\n[A-Z_]{{3,}}:|\Z)", text, re.DOTALL
        )
        result[fb_key] = fb_m.group(1).strip() if fb_m else ""

    # TOP_ISSUES block
    issues_m = re.search(r"TOP_ISSUES:\n(.*?)(?=\n[A-Z_]+:|\Z)", text, re.DOTALL)
    issues: list[str] = []
    if issues_m:
        for line in issues_m.group(1).splitlines():
            line = line.strip()
            if re.match(r"^\d+\.\s+", line):
                issues.append(re.sub(r"^\d+\.\s+", "", line))
    result["TOP_ISSUES"] = issues

    overall_m = re.search(r"OVERALL_SCORE:\s*([\d.]+)", text)
    result["OVERALL_SCORE"] = float(overall_m.group(1)) if overall_m else 0.0

    summary_m = re.search(
        r"OVERALL_SUMMARY:\s*(.+?)(?=\n[A-Z_]+:|\Z)", text, re.DOTALL
    )
    result["OVERALL_SUMMARY"] = summary_m.group(1).strip() if summary_m else text.strip()

    return result


# ---------------------------------------------------------------------------
# Markdown feedback renderer
# ---------------------------------------------------------------------------

_SCORE_EMOJI = {5: "✅", 4: "🟢", 3: "🟡", 2: "🟠", 1: "🔴", 0: "❓"}

_DIM_LABELS = {
    "CONCEPT_TREE_DEPTH": "Concept Tree Depth",
    "NOVELTY_ANALYSIS_GROUNDING": "Novelty Analysis Grounding",
    "DOMAIN_REFERENCES_QUALITY": "Domain References Quality",
    "REPORT_COHERENCE": "Report Coherence",
    "PIPELINE_HEALTH": "Pipeline Health",
}


def _render_feedback_md(report_path: str, scores: dict, raw_llm: str) -> str:
    """Render a Markdown feedback block for one report."""
    name = Path(report_path).name
    overall = scores.get("OVERALL_SCORE", 0)
    overall_emoji = _SCORE_EMOJI.get(round(overall), "❓")
    lines = [
        f"## Report: `{name}`",
        "",
        f"**Overall quality score:** {overall_emoji} **{overall:.1f} / 5.0**",
        "",
        "### Dimension scores",
        "",
        "| Dimension | Score | Feedback |",
        "|-----------|------:|---------|",
    ]
    for key, label in _DIM_LABELS.items():
        score = int(scores.get(key, 0))
        emoji = _SCORE_EMOJI.get(score, "❓")
        feedback = str(scores.get(key + "_FEEDBACK", "")).replace("\n", " ")
        lines.append(f"| {label} | {emoji} {score}/5 | {feedback} |")

    issues = scores.get("TOP_ISSUES", [])
    if issues:
        lines += ["", "### Top issues to fix", ""]
        for i, issue in enumerate(issues, 1):
            lines.append(f"{i}. {issue}")

    summary = str(scores.get("OVERALL_SUMMARY", ""))
    if summary:
        lines += ["", "### Summary", "", summary]

    lines += [
        "",
        "<details>",
        "<summary>Raw LLM assessment</summary>",
        "",
        "```",
        raw_llm.strip(),
        "```",
        "",
        "</details>",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# GitHub integration
# ---------------------------------------------------------------------------

def _write_github_summary(content: str) -> None:
    """Append *content* to the GitHub Actions step summary file."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write(content)


def _post_pr_comment(content: str, pr_number: str, repo: str, token: str) -> None:
    """Post *content* as a comment on the given pull request."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    body = json.dumps({"body": content}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "open-idea-sourcing-report-review-agent/2.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status not in (200, 201):
                print(
                    f"Warning: GitHub API responded {resp.status} when posting comment.",
                    file=sys.stderr,
                )
    except Exception as exc:  # pragma: no cover
        print(f"Warning: could not post PR comment: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "reports",
        nargs="+",
        metavar="REPORT",
        help="One or more generated Markdown report files to review.",
    )
    p.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        help="OpenAI model to use for review (default: gpt-4o or OPENAI_MODEL env var).",
    )
    p.add_argument(
        "--output-md",
        metavar="FILE",
        default=None,
        help="Write aggregated feedback Markdown to this file.",
    )
    p.add_argument(
        "--github-summary",
        action="store_true",
        default=False,
        help="Append feedback to $GITHUB_STEP_SUMMARY (for CI use).",
    )
    p.add_argument(
        "--post-pr-comment",
        action="store_true",
        default=False,
        help=(
            "Post feedback as a PR comment. "
            "Requires GH_TOKEN, GH_REPO, and PR_NUMBER environment variables."
        ),
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print(
            "Error: OPENAI_API_KEY is not set. Cannot run report review agent.",
            file=sys.stderr,
        )
        return 1

    all_feedback_parts: list[str] = []
    header = textwrap.dedent("""\
        # Report Quality Feedback

        *Generated by the Open-Idea-Sourcing report review agent.*

        """)
    all_feedback_parts.append(header)

    for report_file in args.reports:
        path = Path(report_file)
        if not path.exists():
            print(f"Warning: report file not found: {path}", file=sys.stderr)
            continue

        report_content = path.read_text(encoding="utf-8")
        print(f"Reviewing {path.name} ...", file=sys.stderr)

        try:
            raw_llm = _call_llm(report_content, args.model, api_key)
        except Exception as exc:  # pragma: no cover
            print(f"Error calling LLM for {path.name}: {exc}", file=sys.stderr)
            all_feedback_parts.append(
                f"## Report: `{path.name}`\n\n> **Error:** {exc}\n\n---\n\n"
            )
            continue

        scores = _parse_scores(raw_llm)
        feedback_md = _render_feedback_md(report_file, scores, raw_llm)
        all_feedback_parts.append(feedback_md)

        # Print per-report summary to stderr for CI log readability
        overall = scores.get("OVERALL_SCORE", 0)
        print(
            f"  → Overall score: {overall:.1f}/5.0 | "
            f"Concept tree: {scores.get('CONCEPT_TREE_DEPTH', 0)}/5 | "
            f"Grounding: {scores.get('NOVELTY_ANALYSIS_GROUNDING', 0)}/5",
            file=sys.stderr,
        )

    aggregated = "\n".join(all_feedback_parts)

    # Write to stdout always
    print(aggregated)

    # Write to file if requested
    if args.output_md:
        out_path = Path(args.output_md)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(aggregated, encoding="utf-8")
        print(f"Feedback written to {out_path}", file=sys.stderr)

    # Write to GitHub Actions step summary
    if args.github_summary:
        _write_github_summary(aggregated)
        print("Feedback written to GitHub Actions step summary.", file=sys.stderr)

    # Post as PR comment
    if args.post_pr_comment:
        token = os.environ.get("GH_TOKEN", "")
        repo = os.environ.get("GH_REPO", "")
        pr_number = os.environ.get("PR_NUMBER", "")
        if not (token and repo and pr_number):
            print(
                "Warning: --post-pr-comment requires GH_TOKEN, GH_REPO, and PR_NUMBER "
                "environment variables. Skipping.",
                file=sys.stderr,
            )
        else:
            _post_pr_comment(aggregated, pr_number, repo, token)
            print(
                f"Feedback posted as comment on PR #{pr_number}.", file=sys.stderr
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
