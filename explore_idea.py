#!/usr/bin/env python3
"""explore_idea.py — CLI for top-down idea search & decomposition.

Takes a research idea or topic and produces a hierarchical decomposition
enriched with academic references found via Semantic Scholar online search.

Usage
-----
    python explore_idea.py "Attention mechanisms in deep learning"
    python explore_idea.py "Quantum error correction" --depth 3
    python explore_idea.py "Federated learning" --max-refs 3 --no-online-search
    python explore_idea.py "Diffusion models" --format json --output report.json

Environment variables
---------------------
OPENAI_API_KEY
    Required when using the default OpenAI backend.
OPENAI_MODEL
    OpenAI model name (default: gpt-4o).

Examples
--------
    # Decompose an idea with default settings (depth 2, markdown output):
    python explore_idea.py "Transformers in NLP"

    # Deeper decomposition saved to a custom location:
    python explore_idea.py "Reinforcement learning" --depth 3 --output my_report.md

    # JSON output for downstream processing:
    python explore_idea.py "Generative adversarial networks" --format json

    # Disable online search (useful when offline or rate-limited):
    python explore_idea.py "Neural ODEs" --no-online-search

    # Use a custom report store directory:
    python explore_idea.py "Graph neural networks" --reports-dir /path/to/my_reports
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared in requirements
    load_dotenv = None


def _load_environment() -> None:
    """Load environment variables from .env without overriding existing env vars."""
    if load_dotenv is None:
        if not os.environ.get("OPENAI_API_KEY"):
            print(
                "Warning: python-dotenv is not installed; .env will not be auto-loaded. "
                "Run 'make install' or export OPENAI_API_KEY in your shell.",
                file=sys.stderr,
            )
        return

    cwd_env = Path.cwd() / ".env"
    script_env = Path(__file__).resolve().parent / ".env"
    seen: set[Path] = set()
    for env_path in (cwd_env, script_env):
        resolved = env_path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            load_dotenv(dotenv_path=resolved, override=False)
            return
    load_dotenv(override=False)


def _build_llm(model: str):
    """Construct a callable that sends prompts to OpenAI and returns responses."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise SystemExit(
            "Error: OPENAI_API_KEY is not set. "
            "Export it in your shell or add it to your .env file."
        )
    try:
        import openai  # type: ignore[import]
    except ImportError as exc:
        raise SystemExit(
            "Error: openai package is not installed. "
            "Run: pip install openai"
        ) from exc

    client = openai.OpenAI(api_key=api_key)

    def call_llm(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    return call_llm


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="explore_idea",
        description=(
            "Top-down research idea decomposition with online reference search. "
            "Decomposes a research idea into a hierarchy of sub-topics using an "
            "LLM, then searches Semantic Scholar for relevant references at each node."
        ),
    )
    parser.add_argument(
        "idea",
        help="Research idea or topic to explore (e.g. 'Attention mechanisms').",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        metavar="N",
        help="Number of decomposition levels (default: 2).",
    )
    parser.add_argument(
        "--max-refs",
        type=int,
        default=5,
        metavar="N",
        help="Maximum references to fetch per node (default: 5).",
    )
    parser.add_argument(
        "--no-online-search",
        action="store_true",
        default=False,
        help="Disable online reference search via Semantic Scholar.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "text", "json"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help=(
            "Write the report to FILE.  When omitted the report is saved "
            "automatically in --reports-dir."
        ),
    )
    parser.add_argument(
        "--reports-dir",
        metavar="DIR",
        default="reports",
        help=(
            "Directory for auto-generated report files "
            "(default: reports).  Created automatically if it does not exist."
        ),
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        help="OpenAI model name (default: gpt-4o or OPENAI_MODEL env var).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _load_environment()
    args = _parse_args(argv)

    from open_idea_sourcing.idea_decomposer import IdeaDecomposer
    from open_idea_sourcing.online_search import OnlineReferenceSearch
    from open_idea_sourcing.report_generator import ReportGenerator, suggest_idea_filename

    # Build LLM callable
    try:
        llm = _build_llm(args.model)
    except SystemExit as exc:
        print(str(exc.code), file=sys.stderr)
        return 1

    # Build online search (or stub with empty results when disabled)
    if args.no_online_search:
        class _NoopSearch:
            def search(self, query: str, max_results: int = 5):
                return []
        online_search = _NoopSearch()  # type: ignore[assignment]
    else:
        online_search = OnlineReferenceSearch()

    # Run decomposition
    print(
        f"Decomposing idea: {args.idea!r} (depth={args.depth}) ...",
        file=sys.stderr,
    )
    decomposer = IdeaDecomposer(
        llm=llm,
        online_search=online_search,
        max_refs_per_node=args.max_refs,
    )
    try:
        root = decomposer.decompose(args.idea, depth=args.depth)
    except Exception as exc:
        print(f"Error: decomposition failed: {exc}", file=sys.stderr)
        return 1

    node_count = len(root.all_nodes())
    print(f"Decomposition complete: {node_count} node(s).", file=sys.stderr)

    # Render report
    generator = ReportGenerator()
    content = generator.generate_idea_report(root, fmt=args.format)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
        auto_save = False
    else:
        reports_dir = Path(args.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = reports_dir / suggest_idea_filename(args.idea, args.format)
        auto_save = True

    try:
        output_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"Error: could not write output file: {exc}", file=sys.stderr)
        return 1

    print(f"Report written to: {output_path}", file=sys.stderr)
    if auto_save:
        print(content)

    return 0


if __name__ == "__main__":
    sys.exit(main())
