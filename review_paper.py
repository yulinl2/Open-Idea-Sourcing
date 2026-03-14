#!/usr/bin/env python3
"""review_paper.py — CLI for evaluating academic paper novelty.

Usage
-----
    python review_paper.py paper.pdf [options]
    python review_paper.py paper.txt [options]

Environment variables
---------------------
OPENAI_API_KEY
    Required when using the default OpenAI backend.
OPENAI_MODEL
    OpenAI model name (default: gpt-4o).

Examples
--------
    # Review a PDF against a local reference store:
    python review_paper.py my_paper.pdf --references refs.json --format markdown

    # Review a plain-text paper and add new references interactively:
    python review_paper.py my_paper.txt --format text

    # Output JSON for downstream processing:
    python review_paper.py my_paper.pdf --format json > report.json
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from open_idea_sourcing.novelty_evaluator import NoveltyEvaluator
from open_idea_sourcing.paper_parser import PaperParser
from open_idea_sourcing.reference_store import ReferenceStore
from open_idea_sourcing.report_generator import ReportGenerator
from open_idea_sourcing.similarity_search import SimilaritySearch


def _build_llm(model: str):
    """Create a simple OpenAI chat-completion callable."""
    try:
        import openai
    except ImportError as exc:
        raise SystemExit(
            "openai package is required. Install it with: pip install openai"
        ) from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY environment variable is not set.\n"
            "Export your OpenAI API key before running this command."
        )

    client = openai.OpenAI(api_key=api_key)

    def call_llm(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    return call_llm


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="review_paper",
        description="Evaluate the genuine novelty of an academic paper using AI.",
    )
    parser.add_argument(
        "paper",
        help="Path to the paper file (.pdf or .txt).",
    )
    parser.add_argument(
        "--references",
        metavar="FILE",
        default=None,
        help="Path to a JSON file containing reference papers "
             "(produced by --save-references).",
    )
    parser.add_argument(
        "--save-references",
        metavar="FILE",
        default=None,
        help="Save the (possibly updated) reference store to this JSON file.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="Output format for the report (default: text).",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        help="OpenAI model name (default: gpt-4o or OPENAI_MODEL env var).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of similar reference papers to surface (default: 5).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # --- Parse the submitted paper ---
    paper_path = Path(args.paper)
    if not paper_path.exists():
        print(f"Error: file not found: {paper_path}", file=sys.stderr)
        return 1

    parser = PaperParser()
    print(f"Parsing paper: {paper_path.name} ...", file=sys.stderr)
    paper = parser.parse_file(paper_path)
    if not paper.full_text.strip():
        print("Error: no text could be extracted from the paper.", file=sys.stderr)
        return 1

    # --- Load reference store ---
    store = ReferenceStore()
    if args.references:
        ref_path = Path(args.references)
        if ref_path.exists():
            print(f"Loading reference store: {ref_path} ...", file=sys.stderr)
            store.load(ref_path)
        else:
            print(
                f"Warning: reference file not found: {ref_path}", file=sys.stderr
            )

    # --- Similarity search ---
    searcher = SimilaritySearch(store)
    similar = searcher.search(paper.key_content(), top_k=args.top_k)

    # --- LLM evaluation ---
    llm = _build_llm(args.model)
    evaluator = NoveltyEvaluator(llm=llm, top_k_similar=args.top_k)
    print("Running novelty evaluation ...", file=sys.stderr)
    report = evaluator.evaluate(paper, similar_papers=similar)

    # --- Optionally save updated store ---
    if args.save_references:
        store.save(args.save_references)
        print(
            f"Reference store saved to: {args.save_references}", file=sys.stderr
        )

    # --- Render report ---
    generator = ReportGenerator()
    print(generator.generate(report, fmt=args.format))
    return 0


if __name__ == "__main__":
    sys.exit(main())
