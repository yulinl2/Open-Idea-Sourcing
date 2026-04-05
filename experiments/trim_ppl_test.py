#!/usr/bin/env python3
"""Small-scale experiment: compare perplexity on full text vs TF-IDF-trimmed text.

Hypothesis: Trimming routine/boilerplate passages from the target paper should
increase the perplexity *separation* between highly-related and weakly-related
references, because we've removed the "shared predictability floor" of generic
academic writing.

This script:
1. Loads cached text data from data/cached_texts/
2. Computes TF-IDF against reference corpus
3. Filters target text to keep only conceptually dense passages
4. Runs perplexity on a small sample (self + 3 cited + 1 random) for both
   full and trimmed text
5. Compares the spread and documents findings

Usage:
    python experiments/trim_ppl_test.py
    python experiments/trim_ppl_test.py --arxiv-id 2006.06138 --n-refs 5
    python experiments/trim_ppl_test.py --keep-ratio 0.3  # aggressive trimming
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import statistics
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    load_dotenv()
except ImportError:
    pass

from geo_perplexity.text_filter import filter_to_dense_passages
from geo_perplexity.perplexity import estimate_perplexity, PerplexityResult


def load_cached_paper(arxiv_id: str) -> dict | None:
    """Load cached paper data."""
    path = Path(f"data/cached_texts/{arxiv_id.replace('/', '_')}.json")
    if not path.exists():
        print(f"  ERROR: no cache found at {path}", file=sys.stderr)
        print(f"  Run: python cache_texts.py https://arxiv.org/abs/{arxiv_id}", file=sys.stderr)
        return None
    return json.loads(path.read_text())


def select_ref_sample(refs: list[dict], n: int, seed: int = 42) -> list[dict]:
    """Select a stratified sample of references for testing.

    Picks refs with the most content diversity: some with full text,
    some with only abstracts, across different content lengths.
    """
    with_full = [r for r in refs if r.get("has_content") and len(r.get("full_text", "")) > 500]
    with_abstract = [r for r in refs if r.get("has_content") and len(r.get("full_text", "")) <= 500]

    rng = random.Random(seed)

    sample = []
    # Take from full-text refs first (more interesting comparison)
    rng.shuffle(with_full)
    sample.extend(with_full[:max(1, n * 2 // 3)])

    # Fill rest from abstract-only refs
    rng.shuffle(with_abstract)
    remaining = n - len(sample)
    sample.extend(with_abstract[:max(1, remaining)])

    return sample[:n]


def run_experiment(
    arxiv_id: str,
    n_refs: int = 5,
    keep_ratio: float = 0.5,
    model: str = "gpt-4o",
) -> dict:
    """Run the full vs trimmed perplexity comparison."""
    import openai

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    client = openai.OpenAI(api_key=api_key)

    # Load cached data
    data = load_cached_paper(arxiv_id)
    if not data:
        sys.exit(1)

    target_text = data["full_text"]
    refs = data["references"]
    random_ref = data.get("random_ref")

    print(f"\n{'='*60}")
    print(f"Trim-PPL Experiment: arXiv:{arxiv_id}")
    print(f"  Model: {model}")
    print(f"  Target text: {len(target_text)} chars")
    print(f"  Keep ratio: {keep_ratio} (will keep top {keep_ratio*100:.0f}% of sentences)")
    print(f"  References available: {len(refs)} total")
    print(f"{'='*60}\n")

    # Select reference sample
    content_refs = [r for r in refs if r.get("has_content")]
    sample_refs = select_ref_sample(content_refs, n_refs)
    print(f"Selected {len(sample_refs)} references for testing:")
    for r in sample_refs:
        src = r.get("content_source", "?")
        tlen = len(r.get("full_text", "") or r.get("abstract", ""))
        print(f"  - [{src}, {tlen}ch] {r['title'][:60]}")

    # Build background corpus for TF-IDF
    background_texts = [
        r.get("full_text") or r.get("abstract", "")
        for r in content_refs
        if r.get("full_text") or r.get("abstract")
    ]
    print(f"\nBackground corpus: {len(background_texts)} documents for IDF")

    # Filter target text
    print(f"\nFiltering target text (keep_ratio={keep_ratio})...")
    trimmed_text, diagnostics = filter_to_dense_passages(
        target_text, background_texts, keep_ratio=keep_ratio,
    )

    print(f"  Original: {diagnostics['original_length']} chars, "
          f"{diagnostics['n_sentences_total']} sentences")
    print(f"  Trimmed:  {diagnostics['filtered_length']} chars, "
          f"{diagnostics['n_sentences_kept']} sentences")
    print(f"  Compression: {diagnostics['compression_ratio']:.1%}")
    print(f"  Avg score kept:    {diagnostics['avg_score_kept']:.4f}")
    print(f"  Avg score dropped: {diagnostics['avg_score_dropped']:.4f}")
    print(f"  Score separation:  {diagnostics['score_separation']:.4f}")
    print(f"  Top distinctive terms: {', '.join(diagnostics['top_distinctive_terms'][:10])}")

    # Build context list: (id, title, text, type)
    contexts = []
    contexts.append(("self", "Target paper (self)", target_text, "self"))

    for r in sample_refs:
        text = r.get("full_text") or r.get("abstract", "")
        contexts.append((r.get("paper_id", ""), r["title"], text, "cited"))

    if random_ref:
        rtext = random_ref.get("full_text") or random_ref.get("abstract", "")
        if rtext:
            contexts.append((random_ref.get("paper_id", ""), random_ref["title"], rtext, "random"))

    # Run perplexity for BOTH full and trimmed target
    print(f"\nRunning perplexity comparisons ({len(contexts)} contexts × 2 variants)...")
    print(f"  This will make ~{len(contexts) * 2 * 3} API calls (est. 3 chunks each).\n")

    full_results = []
    trimmed_results = []

    for i, (ctx_id, ctx_title, ctx_text, ctx_type) in enumerate(contexts):

        # Full text perplexity
        print(f"  [{i+1}/{len(contexts)}] Full-text PPL | {ctx_type}: {ctx_title[:50]}...")
        r_full = estimate_perplexity(
            context_text=ctx_text,
            target_text=target_text,
            model=model,
            client=client,
            context_id=ctx_id,
            context_title=ctx_title,
            context_type=ctx_type,
        )
        full_results.append(r_full)
        ppl_str = f"{r_full.perplexity:.6f}" if math.isfinite(r_full.perplexity) else "ERROR"
        print(f"         PPL={ppl_str} ({r_full.n_tokens}tok)")

        # Trimmed text perplexity
        print(f"  [{i+1}/{len(contexts)}] Trimmed PPL  | {ctx_type}: {ctx_title[:50]}...")
        r_trim = estimate_perplexity(
            context_text=ctx_text,
            target_text=trimmed_text,
            model=model,
            client=client,
            context_id=ctx_id,
            context_title=ctx_title,
            context_type=ctx_type,
        )
        trimmed_results.append(r_trim)
        ppl_str = f"{r_trim.perplexity:.6f}" if math.isfinite(r_trim.perplexity) else "ERROR"
        print(f"         PPL={ppl_str} ({r_trim.n_tokens}tok)\n")

    # Analyze results
    print(f"\n{'='*60}")
    print("RESULTS COMPARISON")
    print(f"{'='*60}\n")

    def analyze_variant(results: list[PerplexityResult], label: str) -> dict:
        self_ppl = next((r.perplexity for r in results if r.context_type == "self"), float("nan"))
        cited_ppls = [r.perplexity for r in results if r.context_type == "cited" and math.isfinite(r.perplexity)]
        random_ppl = next((r.perplexity for r in results if r.context_type == "random"), float("nan"))

        stats = {}
        stats["self_ppl"] = self_ppl
        stats["random_ppl"] = random_ppl

        if cited_ppls:
            stats["cited_mean"] = statistics.mean(cited_ppls)
            stats["cited_median"] = statistics.median(cited_ppls)
            stats["cited_std"] = statistics.stdev(cited_ppls) if len(cited_ppls) > 1 else 0
            stats["cited_min"] = min(cited_ppls)
            stats["cited_max"] = max(cited_ppls)
            stats["cited_spread"] = max(cited_ppls) - min(cited_ppls)
            stats["cited_cv"] = stats["cited_std"] / stats["cited_mean"] if stats["cited_mean"] > 0 else 0
        else:
            stats["cited_mean"] = float("nan")
            stats["cited_spread"] = 0

        # Separation metrics
        if math.isfinite(self_ppl) and cited_ppls:
            stats["self_vs_cited_mean"] = stats["cited_mean"] - self_ppl
            stats["self_vs_cited_ratio"] = stats["cited_mean"] / self_ppl if self_ppl > 0 else float("nan")
        if math.isfinite(random_ppl) and cited_ppls:
            stats["random_vs_cited_mean"] = random_ppl - stats["cited_mean"]

        print(f"\n--- {label} ---")
        print(f"  Self PPL:        {self_ppl:.6f}")
        if cited_ppls:
            print(f"  Cited mean PPL:  {stats['cited_mean']:.6f}")
            print(f"  Cited median:    {stats['cited_median']:.6f}")
            print(f"  Cited std:       {stats['cited_std']:.6f}")
            print(f"  Cited spread:    {stats['cited_spread']:.6f}")
            print(f"  Cited CV:        {stats['cited_cv']:.4f}")
            print(f"  Self vs cited:   {stats.get('self_vs_cited_mean', 0):.6f} (ratio: {stats.get('self_vs_cited_ratio', 0):.6f})")
        if math.isfinite(random_ppl):
            print(f"  Random PPL:      {random_ppl:.6f}")
            print(f"  Random vs cited: {stats.get('random_vs_cited_mean', 0):.6f}")

        return stats

    full_stats = analyze_variant(full_results, "FULL TEXT")
    trim_stats = analyze_variant(trimmed_results, f"TRIMMED TEXT (keep={keep_ratio})")

    # Compare
    print(f"\n{'='*60}")
    print("COMPARISON: Full vs Trimmed")
    print(f"{'='*60}")

    improvements = {}
    if full_stats.get("cited_spread", 0) > 0 and trim_stats.get("cited_spread", 0) > 0:
        spread_change = trim_stats["cited_spread"] / full_stats["cited_spread"]
        improvements["spread_change"] = spread_change
        print(f"\n  Cited PPL spread: {full_stats['cited_spread']:.6f} → {trim_stats['cited_spread']:.6f} "
              f"({spread_change:.2f}x)")

    if full_stats.get("cited_cv", 0) > 0 and trim_stats.get("cited_cv", 0) > 0:
        cv_change = trim_stats["cited_cv"] / full_stats["cited_cv"]
        improvements["cv_change"] = cv_change
        print(f"  Cited CV:         {full_stats['cited_cv']:.4f} → {trim_stats['cited_cv']:.4f} "
              f"({cv_change:.2f}x)")

    self_vs_cited_full = full_stats.get("self_vs_cited_ratio", 1)
    self_vs_cited_trim = trim_stats.get("self_vs_cited_ratio", 1)
    if math.isfinite(self_vs_cited_full) and math.isfinite(self_vs_cited_trim):
        sep_change = (self_vs_cited_trim - 1) / (self_vs_cited_full - 1) if self_vs_cited_full != 1 else float("nan")
        if math.isfinite(sep_change):
            improvements["separation_change"] = sep_change
            print(f"  Self/cited ratio: {self_vs_cited_full:.6f} → {self_vs_cited_trim:.6f} "
                  f"(separation {sep_change:.2f}x)")

    # Per-reference comparison
    print(f"\n  Per-reference PPL comparison:")
    print(f"  {'Reference':<50} {'Full PPL':>12} {'Trim PPL':>12} {'Change':>10}")
    print(f"  {'-'*50} {'-'*12} {'-'*12} {'-'*10}")
    for rf, rt in zip(full_results, trimmed_results):
        if math.isfinite(rf.perplexity) and math.isfinite(rt.perplexity):
            change = (rt.perplexity - rf.perplexity) / rf.perplexity * 100
            title = rf.context_title[:50]
            print(f"  {title:<50} {rf.perplexity:>12.6f} {rt.perplexity:>12.6f} {change:>+9.3f}%")

    # Save results
    results_data = {
        "arxiv_id": arxiv_id,
        "model": model,
        "keep_ratio": keep_ratio,
        "n_refs_tested": len(sample_refs),
        "diagnostics": diagnostics,
        "full_text_stats": {k: v for k, v in full_stats.items() if not isinstance(v, float) or math.isfinite(v)},
        "trimmed_text_stats": {k: v for k, v in trim_stats.items() if not isinstance(v, float) or math.isfinite(v)},
        "improvements": improvements,
        "per_reference": [
            {
                "title": rf.context_title,
                "context_type": rf.context_type,
                "full_ppl": rf.perplexity if math.isfinite(rf.perplexity) else None,
                "trimmed_ppl": rt.perplexity if math.isfinite(rt.perplexity) else None,
                "full_tokens": rf.n_tokens,
                "trimmed_tokens": rt.n_tokens,
            }
            for rf, rt in zip(full_results, trimmed_results)
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"trim_ppl_{arxiv_id}_{keep_ratio}.json"
    out_path.write_text(json.dumps(results_data, indent=2))
    print(f"\n  Results saved: {out_path}")

    # Verdict
    print(f"\n{'='*60}")
    spread_improved = improvements.get("spread_change", 1) > 1.2
    cv_improved = improvements.get("cv_change", 1) > 1.2
    sep_improved = improvements.get("separation_change", 1) > 1.2

    if spread_improved or cv_improved or sep_improved:
        print("VERDICT: Trimming IMPROVED perplexity separation!")
        if spread_improved:
            print(f"  - PPL spread increased {improvements['spread_change']:.1f}x")
        if cv_improved:
            print(f"  - Coefficient of variation increased {improvements['cv_change']:.1f}x")
        if sep_improved:
            print(f"  - Self/cited separation increased {improvements['separation_change']:.1f}x")
    else:
        print("VERDICT: Trimming did NOT significantly improve separation.")
        print("  Consider: different keep_ratio, alternative filtering, or")
        print("  the current PPL method may be insensitive to text content.")

    print(f"{'='*60}\n")

    return results_data


def main():
    parser = argparse.ArgumentParser(description="Trim-PPL experiment")
    parser.add_argument("--arxiv-id", default="2006.06138")
    parser.add_argument("--n-refs", type=int, default=5)
    parser.add_argument("--keep-ratio", type=float, default=0.5)
    parser.add_argument("--model", default="gpt-4o")
    args = parser.parse_args()

    run_experiment(args.arxiv_id, args.n_refs, args.keep_ratio, args.model)


if __name__ == "__main__":
    main()
