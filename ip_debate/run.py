"""Command-line entrypoint for the IP debate / reconstruction pipeline.

This module is the **debate-track equivalent of ``review_paper.py``** — it
defines the CLI interface for ``ip_debate`` and is the only entrypoint that
CI and users should call for this track.  It never imports or delegates to
``review_paper.py``; the two pipelines are fully decoupled.

Usage (once the pipeline is implemented)::

    python -m ip_debate.run --paper-url https://arxiv.org/abs/2006.06138
    python -m ip_debate.run --papers-file data/papers.ndjson --debate-mode crewai
    python -m ip_debate.run --paper-url <url> --output-format markdown --output report.md

Current status: v0.0.0 stub — argument parsing is fully wired but the
pipeline body raises :class:`NotImplementedError`.  CI uses this module to
verify the interface before the pipeline is built.
"""

from __future__ import annotations

import argparse
import sys


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the debate-track CLI.

    The arguments here are intentionally different from ``review_paper.py``
    (the baseline CLI) because the debate pipeline has a different interface:

    * ``--debate-mode`` selects the multi-agent strategy (no such concept in
      the baseline).
    * ``--paper-url`` / ``--papers-file`` mirror the baseline convenience flags
      but feed into a completely different pipeline.
    * There is no ``--no-online-search`` or decomposition-related flag here —
      those concepts belong to the baseline novelty-evaluation pipeline.
    """
    p = argparse.ArgumentParser(
        prog="python -m ip_debate.run",
        description=(
            "IP Debate / Reconstruction Pipeline  (ip_debate v0.0.0 stub)\n\n"
            "Runs a paper through the multi-agent debate pipeline to test IP "
            "reconstruction accuracy.  The interface is SEPARATE from the "
            "baseline novelty-evaluation pipeline (review_paper.py)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── Input source (mutually exclusive) ──────────────────────────────────
    input_group = p.add_mutually_exclusive_group()
    input_group.add_argument(
        "--paper-url",
        metavar="URL",
        default="",
        help=(
            "URL of a single paper to process "
            "(e.g. https://arxiv.org/abs/2006.06138)."
        ),
    )
    input_group.add_argument(
        "--papers-file",
        metavar="PATH",
        default="",
        help=(
            "Path to an NDJSON batch file where each line is "
            '{\"url\": \"...\", \"title\": \"...\"}.'
        ),
    )

    # ── Debate strategy ─────────────────────────────────────────────────────
    p.add_argument(
        "--debate-mode",
        choices=["crewai", "wasserstein", "hybrid"],
        default="crewai",
        help=(
            "Multi-agent debate strategy to use.  "
            "crewai: CrewAI role-based debate (default).  "
            "wasserstein: Wasserstein adversarial reconstruction game.  "
            "hybrid: combines both."
        ),
    )

    # ── Output ──────────────────────────────────────────────────────────────
    p.add_argument(
        "--output-format",
        choices=["text", "markdown", "json"],
        default="markdown",
        help="Report format (default: markdown).",
    )
    p.add_argument(
        "--output",
        metavar="PATH",
        default="",
        help=(
            "Write the report to this file path instead of stdout.  "
            "The directory is created if it does not exist."
        ),
    )

    # ── Config ──────────────────────────────────────────────────────────────
    p.add_argument(
        "--config",
        metavar="PATH",
        default="",
        help=(
            "Path to a YAML config file with debate pipeline settings.  "
            "CLI flags take precedence over config-file values."
        ),
    )

    return p


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and run the debate pipeline.

    Parameters
    ----------
    argv:
        Argument list (defaults to :data:`sys.argv`).

    Raises
    ------
    NotImplementedError
        Always — pipeline not yet implemented (v0.0.0 stub).
    SystemExit
        On argument errors or ``--help``."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.paper_url and not args.papers_file:
        parser.error("Provide either --paper-url or --papers-file.")

    # ── Pipeline stub ───────────────────────────────────────────────────────
    # Replace everything below with real pipeline logic when building v0.1.0.
    raise NotImplementedError(
        f"ip_debate pipeline not yet implemented (v0.0.0 stub).\n"
        f"  debate_mode  : {args.debate_mode}\n"
        f"  output_format: {args.output_format}\n"
        f"  paper_url    : {args.paper_url or '(batch)'}\n"
        f"  papers_file  : {args.papers_file or '(none)'}\n"
        "Build the pipeline first, then remove this stub."
    )


if __name__ == "__main__":
    main()
