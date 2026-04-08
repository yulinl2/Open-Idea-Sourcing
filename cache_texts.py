#!/usr/bin/env python3
"""Cache all text data for test papers to data/cached_texts/.

v2 — Uses SOTA extraction pipeline:
  - pymupdf4llm (PyMuPDF markdown) as primary extractor
  - pdfminer.six as fallback
  - Optional LLM cleaning pass for target papers
  - Preserves older v1 cache files for cross-check / audit

This script downloads PDFs, extracts text, fetches citations from
Semantic Scholar, and saves everything to a persistent, git-tracked
JSON file per paper.

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
    """Create an LLM callable for JSON-mode responses."""
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


def _make_llm_text(client, model: str = "gpt-4o"):
    """Create an LLM callable for plain-text responses (v2 cleaning)."""
    def llm_text(system_prompt: str, user_prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=16000,
            temperature=0.0,
        )
        return response.choices[0].message.content or ""
    return llm_text


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


def cache_single_paper(source: str, client, llm_json, llm_text=None) -> Path | None:
    """Fetch, extract, and cache all text data for a single paper.

    v2: Uses pymupdf4llm + pdfminer.six pipeline with optional LLM cleaning.
    Preserves v1 cache files for cross-check / audit.
    """
    from geo_perplexity.reference_collector import fetch_all_citations
    from geo_perplexity.text_extractor import (
        batch_extract_full_text,
        download_arxiv_pdf,
        extract_full_text,
    )
    from geo_perplexity.random_reference import find_random_non_cited_reference

    arxiv_id = _extract_arxiv_id(source)
    if not arxiv_id:
        print(f"  ERROR: cannot extract arXiv ID from {source}", file=sys.stderr)
        return None

    out_path = cache_path(arxiv_id)

    # Preserve v1 if it exists and we haven't already
    v1_path = CACHE_DIR / f"{arxiv_id.replace('/', '_')}_v1.json"
    if out_path.exists() and not v1_path.exists():
        import shutil
        shutil.copy2(out_path, v1_path)
        print(f"  Preserved v1: {v1_path}")

    print(f"\n{'='*60}")
    print(f"Caching (v2 SOTA): {source} (arXiv:{arxiv_id})")
    print(f"{'='*60}")

    # Step 1: Download and extract target paper text (SOTA pipeline)
    print("\n[1/4] Downloading and extracting target paper (pymupdf4llm)...")
    pdf_path = download_arxiv_pdf(arxiv_id)
    if not pdf_path:
        print(f"  ERROR: could not download PDF for {arxiv_id}", file=sys.stderr)
        return None

    extraction = extract_full_text(
        pdf_path, llm_json=llm_text, use_llm_cleaning=bool(llm_text),
    )
    full_text = extraction["full_text"]
    raw_md = extraction["raw_md"]
    title = extraction["title"]
    abstract = extraction["abstract"]
    method = extraction["extraction_method"]

    if not full_text:
        print("  ERROR: could not extract text from PDF", file=sys.stderr)
        return None

    print(f"  Method: {method}")
    print(f"  Title: {title[:80]}")
    print(f"  Abstract: {len(abstract)} chars")
    print(f"  Full text: {len(full_text)} chars (raw: {len(raw_md)} chars)")

    # Step 2: Fetch citations
    print("\n[2/4] Fetching cited references from Semantic Scholar...")
    cited_papers = fetch_all_citations(arxiv_id=arxiv_id, title=title)
    print(f"  Found {len(cited_papers)} references")

    # Step 3: Extract full text for citations (pymupdf4llm, no LLM cleaning)
    print("\n[3/4] Extracting full text for cited papers (pymupdf4llm)...")
    cited_papers = batch_extract_full_text(cited_papers, llm_json)
    n_with_text = sum(1 for p in cited_papers if p.has_content)
    n_full_text = sum(1 for p in cited_papers if p.full_text and len(p.full_text) > 500)
    print(f"  {n_with_text}/{len(cited_papers)} have content ({n_full_text} full text)")

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
        "raw_text": raw_md,  # pymupdf4llm markdown for audit
        "raw_text_length": len(raw_md),
        "extraction_method": method,
        "extraction_version": "v2-sota",
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
            "n_with_full_text": n_full_text,
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
    parser.add_argument("--force", action="store_true",
                        help="Re-cache even if already cached (preserves v1)")
    parser.add_argument("--no-llm-clean", action="store_true",
                        help="Skip LLM cleaning pass for target papers")
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

    print(f"Papers to cache: {len(sources)} (v2 SOTA pipeline)")
    for s in sources:
        aid = _extract_arxiv_id(s)
        cached = is_cached(aid) if aid else False
        status = "CACHED" if (cached and not args.force) else "PENDING"
        print(f"  [{status}] {s} → arXiv:{aid}")

    if args.dry_run:
        return

    # When forcing re-cache, delete existing cache entries so is_cached returns False
    if args.force:
        for s in sources:
            aid = _extract_arxiv_id(s)
            if aid:
                p = cache_path(aid)
                if p.exists():
                    p.unlink()
                    print(f"  Removed old cache: {p}")

    client = _get_openai_client()
    llm_json = _make_llm_json(client)
    llm_text = None if args.no_llm_clean else _make_llm_text(client)

    for source in sources:
        try:
            cache_single_paper(source, client, llm_json, llm_text=llm_text)
        except Exception as exc:
            print(f"\nERROR caching {source}: {exc}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            continue

    print("\nDone caching (v2 SOTA).")


if __name__ == "__main__":
    main()
