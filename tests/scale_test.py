#!/usr/bin/env python3
"""Scale-up test: real paper perplexity with Semantic Scholar abstracts.

Uses the actual target paper text and real cited reference abstracts.
Tests with a single model (gpt-4o) to keep costs/time manageable.

Run with:  python tests/scale_test.py
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

MODEL = "gpt-4o"
TARGET_ARXIV = "2006.06138"
# Keep scale test fast (full coverage is done by the geo-perplexity workflow)
MAX_REFS = 10


def _save(name: str, result: dict) -> None:
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    path = RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"  -> saved {path}")


def _sanitize_traceback(tb: str) -> str:
    return re.sub(r"(Bearer |sk-)[A-Za-z0-9_\-]+", r"\1[REDACTED]", tb)


def _get_client():
    import openai
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None, "OPENAI_API_KEY not set"
    return openai.OpenAI(api_key=key), ""


def test_real_paper_abstracts():
    """PPL(target_fulltext | ref_abstract) for real cited papers.

    This tests whether the pipeline produces meaningful PPL variation
    across real cited references using just their abstracts as context.
    """
    print("\n[Scale Test A] Real paper with abstract-only contexts")
    print(f"  Target: arXiv:{TARGET_ARXIV}, Model: {MODEL}")

    client, err = _get_client()
    if err:
        _save("10_real_abstracts", {"pass": False, "error": err})
        return False

    from geo_perplexity.reference_collector import fetch_all_citations
    from geo_perplexity.text_extractor import (
        download_arxiv_pdf,
        extract_text_pdfplumber,
        extract_text_llm_agentic,
    )
    from geo_perplexity.perplexity import estimate_perplexity

    result = {"target_arxiv": TARGET_ARXIV, "model": MODEL}

    # Step 1: Get target paper full text
    print("  Downloading target paper...")
    pdf_path = download_arxiv_pdf(TARGET_ARXIV)
    if not pdf_path:
        result["pass"] = False
        result["error"] = "Failed to download target PDF"
        _save("10_real_abstracts", result)
        return False

    raw_text = extract_text_pdfplumber(pdf_path)

    def llm_json(system_prompt, user_prompt):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=8000,
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or ""

    full_text = extract_text_llm_agentic(raw_text, llm_json)
    result["target_text_length"] = len(full_text)
    print(f"  Target text: {len(full_text)} chars")

    # Step 2: Fetch refs with abstracts
    print("  Fetching cited references...")
    all_refs = fetch_all_citations(arxiv_id=TARGET_ARXIV)
    refs_with_abstract = [p for p in all_refs if p.abstract and len(p.abstract) > 100]
    result["n_total_refs"] = len(all_refs)
    result["n_refs_with_abstract"] = len(refs_with_abstract)

    # Use all refs with abstracts (up to MAX_REFS)
    test_refs = refs_with_abstract[:MAX_REFS]
    result["n_test_refs"] = len(test_refs)
    print(f"  Using {len(test_refs)} refs (of {len(refs_with_abstract)} with abstracts)")

    # Step 3: Self-perplexity
    print("  Computing self-PPL...")
    r_self = estimate_perplexity(
        context_text=full_text,
        target_text=full_text,
        model=MODEL,
        client=client,
        context_id="self",
        context_title="self",
        context_type="self",
    )
    result["self_ppl"] = {
        "perplexity": r_self.perplexity,
        "avg_logprob": r_self.avg_logprob,
        "n_tokens": r_self.n_tokens,
        "n_chunks": r_self.n_chunks,
        "error": r_self.error,
    }
    ppl_s = f"{r_self.perplexity:.4f}" if math.isfinite(r_self.perplexity) else "ERROR"
    print(f"    self: PPL={ppl_s} ({r_self.n_tokens} tokens)")

    # Step 4: PPL for each ref (abstract as context)
    print("  Computing PPL for cited refs (abstract as context)...")
    ref_results = []
    for i, ref in enumerate(test_refs):
        r = estimate_perplexity(
            context_text=ref.abstract,
            target_text=full_text,
            model=MODEL,
            client=client,
            context_id=ref.paper_id,
            context_title=ref.title,
            context_type="cited",
        )
        entry = {
            "title": ref.title[:80],
            "has_arxiv": bool(ref.arxiv_id),
            "abstract_length": len(ref.abstract),
            "perplexity": r.perplexity,
            "avg_logprob": r.avg_logprob,
            "n_tokens": r.n_tokens,
            "n_chunks": r.n_chunks,
            "error": r.error,
        }
        ref_results.append(entry)
        ppl_s = f"{r.perplexity:.4f}" if math.isfinite(r.perplexity) else "ERROR"
        print(f"    [{i+1}/{len(test_refs)}] {ref.title[:50]}... PPL={ppl_s}")
        time.sleep(0.3)

    result["ref_results"] = ref_results

    # Step 5: Analysis
    valid_ppls = [r["perplexity"] for r in ref_results if math.isfinite(r["perplexity"])]
    result["n_valid"] = len(valid_ppls)
    result["n_errored"] = len(ref_results) - len(valid_ppls)

    if valid_ppls:
        import statistics
        result["stats"] = {
            "mean": statistics.mean(valid_ppls),
            "median": statistics.median(valid_ppls),
            "std": statistics.stdev(valid_ppls) if len(valid_ppls) > 1 else 0,
            "min": min(valid_ppls),
            "max": max(valid_ppls),
            "spread": max(valid_ppls) - min(valid_ppls),
        }

        # Check: self-PPL should be lower than most cited PPLs
        if math.isfinite(r_self.perplexity):
            n_below_self = sum(1 for p in valid_ppls if p < r_self.perplexity)
            result["n_cited_below_self_ppl"] = n_below_self
            result["self_is_lowest"] = n_below_self == 0

        # Is there meaningful variation?
        result["meaningful_spread"] = result["stats"]["spread"] > 0.01

    result["pass"] = len(valid_ppls) > 0
    _save("10_real_abstracts", result)
    return result["pass"]


def test_ref_content_coverage():
    """Detailed analysis of why refs lack content.

    Categorizes all references to understand the gap.
    """
    print("\n[Scale Test B] Reference content coverage analysis")

    from geo_perplexity.reference_collector import fetch_all_citations

    result = {"arxiv_id": TARGET_ARXIV}
    all_refs = fetch_all_citations(arxiv_id=TARGET_ARXIV)
    result["n_total"] = len(all_refs)

    categories = {
        "has_arxiv_and_abstract": [],
        "has_arxiv_no_abstract": [],
        "no_arxiv_has_abstract": [],
        "no_arxiv_no_abstract": [],
    }

    for p in all_refs:
        has_arxiv = bool(p.arxiv_id)
        has_abstract = bool(p.abstract)
        if has_arxiv and has_abstract:
            categories["has_arxiv_and_abstract"].append(p.title[:80])
        elif has_arxiv and not has_abstract:
            categories["has_arxiv_no_abstract"].append(p.title[:80])
        elif not has_arxiv and has_abstract:
            categories["no_arxiv_has_abstract"].append(p.title[:80])
        else:
            categories["no_arxiv_no_abstract"].append(p.title[:80])

    result["categories"] = {k: {"count": len(v), "samples": v[:5]} for k, v in categories.items()}

    # What fraction could we cover with different strategies?
    n_arxiv = len(categories["has_arxiv_and_abstract"]) + len(categories["has_arxiv_no_abstract"])
    n_abstract = len(categories["has_arxiv_and_abstract"]) + len(categories["no_arxiv_has_abstract"])
    n_either = n_arxiv + len(categories["no_arxiv_has_abstract"])
    result["coverage"] = {
        "arxiv_pdf_only": f"{n_arxiv}/{len(all_refs)} ({100*n_arxiv/len(all_refs):.0f}%)",
        "abstract_only": f"{n_abstract}/{len(all_refs)} ({100*n_abstract/len(all_refs):.0f}%)",
        "arxiv_or_abstract": f"{n_either}/{len(all_refs)} ({100*n_either/len(all_refs):.0f}%)",
        "nothing": f"{len(categories['no_arxiv_no_abstract'])}/{len(all_refs)} ({100*len(categories['no_arxiv_no_abstract'])/len(all_refs):.0f}%)",
    }

    result["pass"] = True
    _save("11_ref_coverage", result)
    print(f"  Coverage breakdown:")
    for k, v in result["coverage"].items():
        print(f"    {k}: {v}")
    return True


def main():
    print("=" * 60)
    print("Geo-Perplexity Scale Tests")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    tests = [
        ("Ref coverage analysis", test_ref_content_coverage),
        ("Real paper abstracts PPL", test_real_paper_abstracts),
    ]

    results = {}
    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as exc:
            print(f"  UNEXPECTED ERROR in {name}: {exc}")
            print(_sanitize_traceback(traceback.format_exc()))
            results[name] = False

    print("\n" + "=" * 60)
    print("SUMMARY")
    for name, passed in results.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")

    _save("10_scale_summary", {
        "tests": results,
        "all_passed": all(results.values()),
    })

    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
