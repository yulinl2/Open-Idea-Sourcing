#!/usr/bin/env python3
"""Incremental batch PPL runner — saves progress after each evaluation.

Can be killed and resumed safely. Generates the final report once all
evaluations are done.

Usage:
    python run_batch_ppl.py 2006.06138
    python run_batch_ppl.py 2602.04770
    python run_batch_ppl.py 2006.06138 --max-evals 15
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
    load_dotenv()
except ImportError:
    pass


def _get_openai_client():
    import openai
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)
    return openai.OpenAI(api_key=api_key)


def _load_cached(arxiv_id: str):
    """Load from cache, return (target, cited_papers, random_ref)."""
    from geo_perplexity.reference_collector import CitedPaper

    cache_path = Path(f"data/cached_texts/{arxiv_id.replace('/', '_')}.json")
    data = json.loads(cache_path.read_text())

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


def _build_contexts(target, cited_papers, random_ref):
    """Build list of (text, id, title, type, source) tuples."""
    contexts = []
    # Self
    contexts.append((
        target["full_text"], "self", "Target paper (self)", "self", "self",
    ))
    # Cited
    for p in cited_papers:
        if p.has_content:
            contexts.append((
                p.best_text,
                p.paper_id or p.arxiv_id,
                p.title,
                "cited",
                getattr(p, "content_source", "") or "",
            ))
    # Random
    if random_ref and random_ref.has_content:
        contexts.append((
            random_ref.best_text,
            random_ref.paper_id or random_ref.arxiv_id,
            random_ref.title,
            "random",
            getattr(random_ref, "content_source", "") or "",
        ))
    return contexts


def _progress_path(arxiv_id: str) -> Path:
    return Path(f"data/ppl_progress_{arxiv_id.replace('/', '_')}.json")


def _load_progress(arxiv_id: str) -> dict:
    path = _progress_path(arxiv_id)
    if path.exists():
        return json.loads(path.read_text())
    return {"completed": {}, "results": []}


def _save_progress(arxiv_id: str, progress: dict):
    path = _progress_path(arxiv_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(progress, indent=2))


def _result_to_dict(r) -> dict:
    return {
        "context_id": r.context_id,
        "context_title": r.context_title,
        "model": r.model,
        "perplexity": r.perplexity if math.isfinite(r.perplexity) else None,
        "avg_logprob": r.avg_logprob if math.isfinite(r.avg_logprob) else None,
        "n_tokens": r.n_tokens,
        "n_chunks": r.n_chunks,
        "context_type": r.context_type,
        "error": r.error,
        "context_source": r.context_source,
        "context_tokens": r.context_tokens,
    }


def _dict_to_result(d) -> "PerplexityResult":
    from geo_perplexity.perplexity import PerplexityResult
    return PerplexityResult(
        context_id=d["context_id"],
        context_title=d["context_title"],
        model=d["model"],
        perplexity=d["perplexity"] if d["perplexity"] is not None else float("nan"),
        avg_logprob=d["avg_logprob"] if d["avg_logprob"] is not None else float("nan"),
        n_tokens=d["n_tokens"],
        n_chunks=d["n_chunks"],
        context_type=d["context_type"],
        error=d.get("error", ""),
        context_source=d.get("context_source", ""),
        context_tokens=d.get("context_tokens", 0),
    )


def run_batch(arxiv_id: str, model: str = "gpt-4o", max_evals: int = 0,
              workers: int = 4):
    """Run PPL evaluations with parallel execution, saving after each one.

    Uses a thread pool (like compute_all_perplexities) to overlap API
    latency across evaluations, while saving results incrementally so
    progress survives process kills.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from geo_perplexity.perplexity import (
        _get_encoding, _chunk_text, _TokenBucketLimiter,
        _MAX_CONTEXT_TOKENS, _CHUNK_TOKENS, _TPM_LIMIT,
        estimate_perplexity,
    )

    print(f"=== Batch PPL runner: arXiv:{arxiv_id}, model={model} ===")

    # Load data
    target, cited_papers, random_ref = _load_cached(arxiv_id)
    contexts = _build_contexts(target, cited_papers, random_ref)
    n_with_text = sum(1 for p in cited_papers if p.has_content)

    print(f"  Title: {target['title']}")
    print(f"  {n_with_text} refs with text, random_ref={'yes' if random_ref else 'no'}")
    print(f"  Total contexts: {len(contexts)} (self + {n_with_text} cited"
          f"{' + 1 random' if random_ref and random_ref.has_content else ''})")

    # Pre-compute encoding and chunks
    enc = _get_encoding(model)
    target_text = target["full_text"]
    chunks = _chunk_text(target_text, _CHUNK_TOKENS, enc)
    print(f"  Target: {len(enc.encode(target_text))} tokens, {len(chunks)} chunks")

    # Load progress
    progress = _load_progress(arxiv_id)
    completed = progress["completed"]  # key = "ctx_idx:model"

    # Build job list sorted by estimated cost (cheapest first)
    jobs = []
    for ci in range(len(contexts)):
        key = f"{ci}:{model}"
        if key not in completed:
            ctx_text = contexts[ci][0]
            ctx_tok = min(len(enc.encode(ctx_text)), _MAX_CONTEXT_TOKENS)
            est_cost = ctx_tok * len(chunks)
            jobs.append((est_cost, ci, ctx_tok))
    jobs.sort()

    total_all = len(contexts)
    done_so_far = total_all - len(jobs)
    print(f"  Progress: {done_so_far}/{total_all} done, {len(jobs)} remaining")

    if not jobs:
        print("  All evaluations complete!")
        return True, progress

    if max_evals > 0:
        jobs = jobs[:max_evals]
        print(f"  Running up to {max_evals} evaluations this batch")

    # Setup
    client = _get_openai_client()
    limiter = _TokenBucketLimiter(_TPM_LIMIT)
    _save_lock = threading.Lock()
    done_count = [done_so_far]

    effective_workers = min(workers, len(jobs))
    print(f"  Workers: {effective_workers}, TPM limit: {_TPM_LIMIT}")

    def _run_one(ci: int, ctx_tok: int) -> "PerplexityResult":
        ctx_text, ctx_id, ctx_title, ctx_type, ctx_source = contexts[ci]

        result = estimate_perplexity(
            context_text=ctx_text,
            target_text="",
            model=model,
            client=client,
            context_id=ctx_id,
            context_title=ctx_title,
            context_type=ctx_type,
            _chunks=chunks,
            _enc=enc,
            _limiter=limiter,
        )
        result.context_source = ctx_source
        result.context_tokens = ctx_tok

        # Save immediately under lock
        key = f"{ci}:{model}"
        with _save_lock:
            done_count[0] += 1
            completed[key] = True
            progress["results"].append(_result_to_dict(result))
            _save_progress(arxiv_id, progress)

            ppl_str = f"{result.perplexity:.6f}" if math.isfinite(result.perplexity) else "ERROR"
            err_str = f" [{result.error}]" if result.error else ""
            print(f"  [{done_count[0]}/{total_all}] {ctx_type}:{ctx_title[:50]}…"
                  f" PPL={ppl_str} ({result.n_tokens}tok, {result.n_chunks}ch){err_str}",
                  flush=True)

        return result

    # Execute with thread pool for API latency overlap
    if effective_workers <= 1:
        for _, ci, ctx_tok in jobs:
            _run_one(ci, ctx_tok)
    else:
        with ThreadPoolExecutor(max_workers=effective_workers) as pool:
            futures = {
                pool.submit(_run_one, ci, ctx_tok): ci
                for _, ci, ctx_tok in jobs
            }
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    ci = futures[future]
                    _, ctx_id, ctx_title, ctx_type, ctx_source = contexts[ci]
                    with _save_lock:
                        done_count[0] += 1
                        key = f"{ci}:{model}"
                        completed[key] = True
                        from geo_perplexity.perplexity import PerplexityResult
                        err_result = PerplexityResult(
                            context_id=ctx_id, context_title=ctx_title,
                            model=model, perplexity=float("nan"),
                            avg_logprob=float("nan"), n_tokens=0,
                            n_chunks=0, context_type=ctx_type,
                            error=f"worker exception: {exc}",
                            context_source=ctx_source,
                        )
                        progress["results"].append(_result_to_dict(err_result))
                        _save_progress(arxiv_id, progress)
                        print(f"  [{done_count[0]}/{total_all}] ERROR {ctx_title[:50]}: {exc}",
                              flush=True)

    remaining = total_all - len(completed)
    print(f"\n  Batch done. {len(completed)}/{total_all} complete, {remaining} remaining.")
    return remaining == 0, progress


def generate_final_report(arxiv_id: str, model: str = "gpt-4o"):
    """Generate report from accumulated progress data."""
    from geo_perplexity.report import generate_report, save_report

    target, cited_papers, random_ref = _load_cached(arxiv_id)
    progress = _load_progress(arxiv_id)

    results = [_dict_to_result(d) for d in progress["results"]]
    n_with_text = sum(1 for p in cited_papers if p.has_content)

    # Determine source URL
    source_url = f"https://arxiv.org/abs/{arxiv_id}"

    report = generate_report(
        target_title=target["title"],
        target_source=source_url,
        results=results,
        models=[model],
        n_cited=len(cited_papers),
        n_extracted=n_with_text,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = arxiv_id.replace("/", "_")
    report_path = save_report(report, "reports", f"perplexity_{slug}_{timestamp}.md")
    print(f"Report saved: {report_path}")
    return report_path


def main():
    parser = argparse.ArgumentParser(description="Incremental batch PPL runner")
    parser.add_argument("arxiv_id", help="arXiv ID (e.g. 2006.06138)")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--max-evals", type=int, default=0,
                        help="Max evaluations per batch (0=unlimited)")
    parser.add_argument("--report-only", action="store_true",
                        help="Skip computation, just generate report from saved progress")
    parser.add_argument("--reset", action="store_true",
                        help="Clear progress and start fresh")
    args = parser.parse_args()

    if args.reset:
        path = _progress_path(args.arxiv_id)
        if path.exists():
            path.unlink()
            print(f"Cleared progress for {args.arxiv_id}")

    if args.report_only:
        generate_final_report(args.arxiv_id, args.model)
        return

    all_done, progress = run_batch(args.arxiv_id, args.model, args.max_evals)

    if all_done:
        print("\nAll evaluations complete! Generating report...")
        generate_final_report(args.arxiv_id, args.model)


if __name__ == "__main__":
    main()
