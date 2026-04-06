#!/usr/bin/env python3
"""Cache all text data for test papers to data/cached_texts/.

This script downloads PDFs, extracts text (via LLM agentic parser),
fetches citations from Semantic Scholar, and saves everything to a
persistent, git-tracked JSON file per paper.

This means subsequent analysis runs can skip the expensive download +
LLM extraction steps entirely, and GitHub Actions workflows don't need
to burn runner time on long API waits.

Usage:
    python cache_texts.py                          # cache all papers in data/test_papers.ndjson
    python cache_texts.py https://arxiv.org/abs/2006.06138  # cache a single paper
    python cache_texts.py --dry-run                # show what would be cached
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
    load_dotenv()
except ImportError:
    pass

CACHE_DIR = Path("data/cached_texts")


def _get_openai_client():
    import openai
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)
    return openai.OpenAI(api_key=api_key)


def _make_llm_json(client, model: str = "gpt-4o"):
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
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", source)
    if m:
        return m.group(1)
    m = re.match(r"^(\d{4}\.\d{4,5}(?:v\d+)?)$", source.strip())
    if m:
        return m.group(1)
    return ""


def cache_path(arxiv_id: str) -> Path:
    return CACHE_DIR / f"{arxiv_id.replace('/', '_')}.json"


def is_cached(arxiv_id: str) -> bool:
    p = cache_path(arxiv_id)
    if not p.exists():
        return False
    data = json.loads(p.read_text())
    # Check it has the essential fields
    return bool(data.get("full_text") and data.get("references"))


def cache_single_paper(source: str, client, llm_json) -> Path | None:
    """Fetch, extract, and cache all text data for a single paper."""
    from geo_perplexity.reference_collector import fetch_all_citations
    from geo_perplexity.text_extractor import (
        batch_extract_full_text,
        download_arxiv_pdf,
        extract_text_llm_agentic,
        extract_text_pdfplumber,
    )
    from geo_perplexity.random_reference import find_random_non_cited_reference

    arxiv_id = _extract_arxiv_id(source)
    if not arxiv_id:
        print(f"  ERROR: cannot extract arXiv ID from {source}", file=sys.stderr)
        return None

    out_path = cache_path(arxiv_id)
    if is_cached(arxiv_id):
        print(f"  Already cached: {out_path}")
        return out_path

    print(f"\n{'='*60}")
    print(f"Caching: {source} (arXiv:{arxiv_id})")
    print(f"{'='*60}")

    # Step 1: Download and extract target paper text
    print("\n[1/4] Downloading and extracting target paper...")
    pdf_path = download_arxiv_pdf(arxiv_id)
    if not pdf_path:
        print(f"  ERROR: could not download PDF for {arxiv_id}", file=sys.stderr)
        return None

    raw_text = extract_text_pdfplumber(pdf_path)
    if not raw_text:
        print("  ERROR: could not extract text from PDF", file=sys.stderr)
        return None

    full_text = extract_text_llm_agentic(raw_text, llm_json)

    # Extract title and abstract
    title = ""
    for line in raw_text.splitlines()[:10]:
        line = line.strip()
        if len(line) > 10 and not any(kw in line.lower() for kw in ["abstract", "arxiv", "http"]):
            title = line
            break

    abstract = ""
    m = re.search(
        r"(?i)abstract[:\s]*\n(.+?)(?=\n\n|\nintroduction|\n1[\.\s])",
        raw_text,
        re.DOTALL,
    )
    if m:
        abstract = re.sub(r"\s+", " ", m.group(1)).strip()[:2000]

    print(f"  Title: {title[:80]}")
    print(f"  Text length: {len(full_text)} chars")

    # Step 2: Fetch citations
    print("\n[2/4] Fetching cited references from Semantic Scholar...")
    cited_papers = fetch_all_citations(arxiv_id=arxiv_id, title=title)
    print(f"  Found {len(cited_papers)} references")

    # Step 3: Extract full text for citations (batched LLM)
    print("\n[3/4] Extracting full text for cited papers...")
    cited_papers = batch_extract_full_text(cited_papers, llm_json)
    n_with_text = sum(1 for p in cited_papers if p.has_content)
    print(f"  {n_with_text}/{len(cited_papers)} have text")

    # Step 4: Find random reference
    print("\n[4/4] Finding random non-cited reference...")
    cited_ids = {p.paper_id for p in cited_papers if p.paper_id}
    random_ref = find_random_non_cited_reference(
        title=title, abstract=abstract, cited_ids=cited_ids,
    )
    if random_ref:
        batch_extract_full_text([random_ref], llm_json)
        print(f"  Random ref: {random_ref.title[:60]}")

    # Save everything
    cache_data = {
        "arxiv_id": arxiv_id,
        "source_url": source,
        "title": title or "Unknown",
        "abstract": abstract,
        "full_text": full_text,
        "raw_text": raw_text,  # preserve pdfplumber output for audit
        "raw_text_length": len(raw_text),
        "references": [
            {
                "paper_id": p.paper_id,
                "title": p.title,
                "abstract": p.abstract,
                "arxiv_id": p.arxiv_id,
                "year": p.year,
                "url": p.url,
                "full_text": p.full_text,
                "content_source": p.content_source,
                "has_content": p.has_content,
            }
            for p in cited_papers
        ],
        "random_ref": {
            "paper_id": random_ref.paper_id,
            "title": random_ref.title,
            "abstract": random_ref.abstract,
            "arxiv_id": random_ref.arxiv_id,
            "full_text": random_ref.full_text,
            "content_source": random_ref.content_source,
        } if random_ref else None,
        "stats": {
            "n_references": len(cited_papers),
            "n_with_content": n_with_text,
            "n_with_full_text": sum(1 for p in cited_papers if p.full_text and len(p.full_text) > 500),
            "n_abstract_only": sum(1 for p in cited_papers if p.content_source in ("abstract", "tldr")),
        },
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False))
    print(f"\n  Saved: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Cache text data for geo-perplexity analysis")
    parser.add_argument("source", nargs="?", help="Single arXiv URL or ID")
    parser.add_argument("--papers-file", default="data/test_papers.ndjson",
                        help="NDJSON file with paper URLs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cached")
    args = parser.parse_args()

    sources = []
    if args.source:
        sources.append(args.source)
    else:
        pf = Path(args.papers_file)
        if pf.exists():
            for line in pf.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    sources.append(json.loads(line)["url"])
                except (json.JSONDecodeError, KeyError):
                    pass

    if not sources:
        print("No papers to cache.", file=sys.stderr)
        sys.exit(1)

    print(f"Papers to cache: {len(sources)}")
    for s in sources:
        aid = _extract_arxiv_id(s)
        cached = is_cached(aid) if aid else False
        status = "CACHED" if cached else "PENDING"
        print(f"  [{status}] {s} → arXiv:{aid}")

    if args.dry_run:
        return

    client = _get_openai_client()
    llm_json = _make_llm_json(client)

    for source in sources:
        try:
            cache_single_paper(source, client, llm_json)
        except Exception as exc:
            print(f"\nERROR caching {source}: {exc}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            continue

    print("\nDone caching.")


if __name__ == "__main__":
    main()
