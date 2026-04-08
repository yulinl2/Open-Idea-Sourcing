#!/usr/bin/env python3
"""Geo-perplexity analysis: measure paper novelty via conditional perplexity.

Usage:
    python run_analysis.py https://arxiv.org/abs/2006.06138
    python run_analysis.py paper.pdf
    python run_analysis.py --papers-file data/test_papers.ndjson
    python run_analysis.py https://arxiv.org/abs/2006.06138 --models gpt-4o
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
import sys
import tempfile
import urllib.request
from pathlib import Path

# Load .env before anything else
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
    load_dotenv()
except ImportError:
    pass


def _get_openai_client():
    """Create an OpenAI client from environment."""
    import openai

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print(
            "ERROR: OPENAI_API_KEY not set. "
            "Set it in .env or as an environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)
    return openai.OpenAI(api_key=api_key)


def _make_llm_json(client, model: str = "gpt-4o"):
    """Create a (system, user) -> response callable for the agentic extractor."""
    def llm_json(system_prompt: str, user_prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=8000,
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""
    return llm_json


def _extract_arxiv_id(source: str) -> str:
    """Extract arXiv ID from URL or bare ID."""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", source)
    if m:
        return m.group(1)
    m = re.match(r"^(\d{4}\.\d{4,5}(?:v\d+)?)$", source.strip())
    if m:
        return m.group(1)
    return ""


def _download_source(source: str) -> str:
    """Download a URL to a temp file, or return the path if it's a local file."""
    if Path(source).exists():
        return source

    if source.startswith("http"):
        # Ensure we get the PDF version for arXiv URLs
        if "arxiv.org/abs/" in source:
            source = source.replace("/abs/", "/pdf/") + ".pdf"

        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        req = urllib.request.Request(source, headers={"User-Agent": "geo-perplexity/0.1"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            tmp.write(resp.read())
        tmp.close()
        return tmp.name

    print(f"ERROR: cannot resolve source: {source}", file=sys.stderr)
    sys.exit(1)


def _parse_target_paper(pdf_path: str, llm_json) -> dict:
    """Parse the target paper via the SOTA v2 extractor.

    Returns dict with title, abstract, full_text.
    """
    from geo_perplexity.text_extractor import extract_full_text

    extraction = extract_full_text(pdf_path, llm_json=llm_json, use_llm_cleaning=False)

    if not extraction["full_text"]:
        print("ERROR: could not extract any text from PDF", file=sys.stderr)
        sys.exit(1)

    return {
        "title": extraction["title"] or "Unknown Title",
        "abstract": extraction["abstract"],
        "full_text": extraction["full_text"],
    }


def _load_from_cache(arxiv_id: str):
    """Try to load pre-cached text data, skipping expensive extraction."""
    from geo_perplexity.reference_collector import CitedPaper

    cache_path = Path(f"data/cached_texts/{arxiv_id.replace('/', '_')}.json")
    if not cache_path.exists():
        return None

    try:
        data = json.loads(cache_path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"WARNING: ignoring invalid cache file {cache_path}: {e}", file=sys.stderr)
        return None
    if not data.get("full_text") or not data.get("references"):
        return None

    target = {
        "title": data.get("title", "Unknown"),
        "abstract": data.get("abstract", ""),
        "full_text": data["full_text"],
    }

    cited_papers = []
    for r in data["references"]:
        p = CitedPaper(
            paper_id=r.get("paper_id", ""),
            title=r.get("title", ""),
            abstract=r.get("abstract", ""),
            arxiv_id=r.get("arxiv_id", ""),
            year=r.get("year"),
            url=r.get("url", ""),
            full_text=r.get("full_text", ""),
            content_source=r.get("content_source", ""),
        )
        cited_papers.append(p)

    random_ref = None
    if data.get("random_ref"):
        rr = data["random_ref"]
        random_ref = CitedPaper(
            paper_id=rr.get("paper_id", ""),
            title=rr.get("title", ""),
            abstract=rr.get("abstract", ""),
            arxiv_id=rr.get("arxiv_id", ""),
            full_text=rr.get("full_text", ""),
            content_source=rr.get("content_source", ""),
        )

    return target, cited_papers, random_ref


def run_single_paper(
    source: str,
    models: list[str],
    output_dir: str,
) -> Path | None:
    """Run the full geo-perplexity analysis for a single paper."""
    from geo_perplexity.perplexity import compute_all_perplexities
    from geo_perplexity.random_reference import find_random_non_cited_reference
    from geo_perplexity.reference_collector import fetch_all_citations
    from geo_perplexity.report import generate_report, save_report
    from geo_perplexity.text_extractor import batch_extract_full_text

    print(f"\n{'='*60}")
    print(f"Geo-Perplexity Analysis: {source}")
    print(f"Models: {', '.join(models)}")
    print(f"{'='*60}\n")

    # Step 0: Set up OpenAI client
    client = _get_openai_client()
    arxiv_id = _extract_arxiv_id(source)

    # Try loading from persistent cache first (skips expensive extraction)
    cached = _load_from_cache(arxiv_id) if arxiv_id else None
    if cached:
        target, cited_papers, random_ref = cached
        n_with_text = sum(1 for p in cited_papers if p.has_content)
        print(f"[cache] Loaded pre-cached data for arXiv:{arxiv_id}")
        print(f"  Title: {target['title']}")
        print(f"  {n_with_text}/{len(cited_papers)} refs with text, "
              f"random_ref={'yes' if random_ref else 'no'}")
    else:
        llm_json = _make_llm_json(client, model="gpt-4o")  # use 4o for extraction

        # Step 1: Parse target paper
        print("[1/5] Parsing target paper...")
        pdf_path = _download_source(source)
        target = _parse_target_paper(pdf_path, llm_json)
        print(f"  Title: {target['title']}")
        print(f"  Abstract: {target['abstract'][:100]}...")

        # Step 2: Collect all cited references
        print("\n[2/5] Collecting cited references...")
        cited_papers = fetch_all_citations(arxiv_id=arxiv_id, title=target["title"])
        print(f"  Found {len(cited_papers)} cited references")

        if not cited_papers:
            print("  WARNING: No cited references found. Trying title-based lookup...")
            cited_papers = fetch_all_citations(title=target["title"])
            print(f"  Found {len(cited_papers)} via title lookup")

        # Step 3: Extract full text for cited papers (batched LLM)
        print("\n[3/5] Extracting full text from cited papers (batched LLM)...")
        cited_papers = batch_extract_full_text(cited_papers, llm_json)
        n_with_text = sum(1 for p in cited_papers if p.has_content)
        print(f"  {n_with_text}/{len(cited_papers)} papers have extractable text")

        # Step 4: Find random non-cited reference
        print("\n[4/5] Finding random non-cited field reference...")
        cited_ids = {p.paper_id for p in cited_papers if p.paper_id}
        random_ref = find_random_non_cited_reference(
            title=target["title"],
            abstract=target["abstract"],
            cited_ids=cited_ids,
            target_year=None,  # could extract from paper metadata
        )
        if random_ref:
            # Also extract its text
            batch_extract_full_text([random_ref], llm_json)
            print(f"  Random ref: {random_ref.title[:60]}...")
        else:
            print("  WARNING: Could not find a random non-cited reference")

    # Step 5: Compute perplexities
    print(f"\n[5/5] Computing perplexities across {len(models)} model(s)...")
    n_contexts = n_with_text + 1 + (1 if random_ref and random_ref.has_content else 0)  # cited + self + random
    print(f"  Total evaluations: {n_contexts} contexts × {len(models)} models = {n_contexts * len(models)}")

    results = compute_all_perplexities(
        target_text=target["full_text"],
        cited_papers=cited_papers,
        random_ref=random_ref,
        models=models,
        client=client,
    )

    # Generate report
    print("\nGenerating report...")
    report = generate_report(
        target_title=target["title"],
        target_source=source,
        results=results,
        models=models,
        n_cited=len(cited_papers),
        n_extracted=n_with_text,
    )

    # Determine output filename (with timestamp to preserve all versions)
    slug = arxiv_id or re.sub(r"[^\w]", "_", target["title"][:40])
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = save_report(report, output_dir, f"perplexity_{slug}_{timestamp}.md")
    print(f"\nReport saved: {report_path}")

    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Geo-perplexity analysis: measure paper novelty via conditional perplexity"
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Paper URL (arXiv) or local PDF path",
    )
    parser.add_argument(
        "--papers-file",
        help="NDJSON file with one {\"url\": ...} per line for batch processing",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["gpt-4o"],
        help="OpenAI models to evaluate (default: gpt-4o)",
    )
    parser.add_argument(
        "--output",
        default="reports",
        help="Output directory for reports (default: reports/)",
    )

    args = parser.parse_args()

    if not args.source and not args.papers_file:
        parser.error("Provide a paper source or --papers-file")

    sources = []
    if args.papers_file:
        with open(args.papers_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    sources.append(obj["url"])
                except (json.JSONDecodeError, KeyError) as exc:
                    print(f"  Skipping invalid line: {line} ({exc})", file=sys.stderr)
    elif args.source:
        sources.append(args.source)

    if not sources:
        print("ERROR: No valid paper sources found", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(sources)} paper(s) with models: {', '.join(args.models)}")

    for source in sources:
        try:
            run_single_paper(source, args.models, args.output)
        except Exception as exc:
            print(f"\nERROR processing {source}: {exc}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            continue

    print("\nDone.")


if __name__ == "__main__":
    main()
