#!/usr/bin/env python3
"""Incremental smoke tests for the geo-perplexity pipeline.

Each test writes its result to tests/results/ so CI can commit them back.
Run with:  python tests/smoke_test.py
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def _save(name: str, result: dict) -> None:
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    path = RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"  -> saved {path}")


def _get_client():
    import openai
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None, "OPENAI_API_KEY not set"
    return openai.OpenAI(api_key=key), ""


def _sanitize_traceback(tb: str) -> str:
    """Remove API keys and secrets from traceback strings."""
    import re
    return re.sub(r"(Bearer |sk-)[A-Za-z0-9_\-]+", r"\1[REDACTED]", tb)


# ── Test 1: Basic API connectivity ────────────────────────────────────

def test_api_connectivity():
    """Can we reach the OpenAI API at all?"""
    print("\n[Test 1] API connectivity ...")
    client, err = _get_client()
    if err:
        _save("01_connectivity", {"pass": False, "error": err})
        return False

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
            temperature=0,
        )
        text = resp.choices[0].message.content.strip()
        _save("01_connectivity", {"pass": True, "response": text, "model": resp.model})
        print(f"  OK — got: {text!r}")
        return True
    except Exception as exc:
        _save("01_connectivity", {"pass": False, "error": str(exc),
                                   "traceback": _sanitize_traceback(traceback.format_exc())})
        print(f"  FAIL — {exc}")
        return False


# ── Test 2: Logprobs availability ─────────────────────────────────────

def test_logprobs():
    """Does logprobs=True work? This is what the perplexity pipeline needs."""
    print("\n[Test 2] Logprobs availability ...")
    client, err = _get_client()
    if err:
        _save("02_logprobs", {"pass": False, "error": err})
        return False

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Reproduce the following text exactly."},
                {"role": "user", "content": "The quick brown fox jumps over the lazy dog."},
            ],
            max_tokens=30,
            temperature=0,
            logprobs=True,
            top_logprobs=1,
        )
        choice = resp.choices[0]
        has_logprobs = (choice.logprobs is not None
                        and choice.logprobs.content is not None
                        and len(choice.logprobs.content) > 0)

        result = {
            "pass": has_logprobs,
            "model": resp.model,
            "output": choice.message.content[:200] if choice.message.content else "",
            "n_logprob_tokens": len(choice.logprobs.content) if has_logprobs else 0,
        }

        if has_logprobs:
            lps = [t.logprob for t in choice.logprobs.content]
            result["sample_logprobs"] = lps[:10]
            result["avg_logprob"] = sum(lps) / len(lps)
            ppl = math.exp(-sum(lps) / len(lps))
            result["perplexity"] = ppl
            print(f"  OK — {len(lps)} tokens, PPL={ppl:.2f}")
        else:
            result["error"] = "logprobs field was empty/None"
            print(f"  FAIL — no logprobs returned")

        _save("02_logprobs", result)
        return has_logprobs
    except Exception as exc:
        _save("02_logprobs", {"pass": False, "error": str(exc),
                               "traceback": _sanitize_traceback(traceback.format_exc())})
        print(f"  FAIL — {exc}")
        return False


# ── Test 3: Mini perplexity (abstract vs abstract) ────────────────────

_TARGET_ABSTRACT = (
    "We propose conformal inference methods for counterfactual predictions "
    "and individual treatment effects. Our approach provides finite-sample "
    "valid prediction intervals that can be computed efficiently."
)

_REF_ABSTRACTS = {
    "closely_related": (
        "Conformal prediction provides distribution-free uncertainty "
        "quantification. We extend conformal methods to handle covariate "
        "shift, enabling valid prediction intervals under distribution "
        "mismatch between training and test data."
    ),
    "somewhat_related": (
        "Random forests are an ensemble learning method that constructs "
        "multiple decision trees for classification and regression. We "
        "propose generalized random forests that enable heterogeneous "
        "treatment effect estimation with valid confidence intervals."
    ),
    "unrelated": (
        "Large language models have demonstrated remarkable capabilities "
        "in text generation and understanding. We propose a new training "
        "approach using reinforcement learning from human feedback to "
        "improve alignment with human preferences."
    ),
}


def test_mini_perplexity():
    """Compute PPL(target_abstract | ref_abstract) for 3 refs.

    Expected: closely_related < somewhat_related < unrelated.
    """
    print("\n[Test 3] Mini perplexity (abstract scale) ...")
    client, err = _get_client()
    if err:
        _save("03_mini_perplexity", {"pass": False, "error": err})
        return False

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from geo_perplexity.perplexity import estimate_perplexity

    results = {}
    for label, ref_text in _REF_ABSTRACTS.items():
        print(f"  Computing PPL for {label} ...")
        r = estimate_perplexity(
            context_text=ref_text,
            target_text=_TARGET_ABSTRACT,
            model="gpt-4o",
            client=client,
            context_id=label,
            context_title=label,
            context_type="cited",
        )
        results[label] = {
            "perplexity": r.perplexity,
            "avg_logprob": r.avg_logprob,
            "n_tokens": r.n_tokens,
            "n_chunks": r.n_chunks,
            "error": r.error,
        }
        finite = math.isfinite(r.perplexity)
        status = f"PPL={r.perplexity:.2f}" if finite else f"ERROR: {r.error}"
        print(f"    {label}: {status}")
        time.sleep(0.5)

    # Also compute self-perplexity
    print(f"  Computing self-PPL ...")
    r_self = estimate_perplexity(
        context_text=_TARGET_ABSTRACT,
        target_text=_TARGET_ABSTRACT,
        model="gpt-4o",
        client=client,
        context_id="self",
        context_title="self",
        context_type="self",
    )
    results["self"] = {
        "perplexity": r_self.perplexity,
        "avg_logprob": r_self.avg_logprob,
        "n_tokens": r_self.n_tokens,
        "n_chunks": r_self.n_chunks,
        "error": r_self.error,
    }
    self_finite = math.isfinite(r_self.perplexity)
    print(f"    self: {'PPL=' + f'{r_self.perplexity:.2f}' if self_finite else 'ERROR: ' + r_self.error}")

    # Check ordering: self < closely_related < somewhat_related < unrelated
    all_finite = all(
        math.isfinite(results[k]["perplexity"])
        for k in ["self", "closely_related", "somewhat_related", "unrelated"]
    )

    ordering_correct = False
    if all_finite:
        ppls = {k: results[k]["perplexity"] for k in results}
        ordering_correct = (
            ppls["self"] < ppls["closely_related"] < ppls["somewhat_related"] < ppls["unrelated"]
        )
        results["ordering_check"] = {
            "self < closely_related": ppls["self"] < ppls["closely_related"],
            "closely_related < somewhat_related": ppls["closely_related"] < ppls["somewhat_related"],
            "somewhat_related < unrelated": ppls["somewhat_related"] < ppls["unrelated"],
            "full ordering (self < closely < somewhat < unrelated)": ordering_correct,
        }

    results["all_finite"] = all_finite
    results["pass"] = all_finite  # main criterion: did we get numbers at all?
    results["ordering_sensible"] = ordering_correct

    _save("03_mini_perplexity", results)
    return all_finite


# ── Test 4: Text extraction pipeline check ────────────────────────────

def test_text_extraction():
    """Check whether PDF download + extraction works for a known arXiv paper."""
    print("\n[Test 4] Text extraction pipeline ...")
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from geo_perplexity.text_extractor import download_arxiv_pdf, extract_text_pymupdf4llm

    test_id = "2006.06138"
    result = {"arxiv_id": test_id}

    # Step A: Download
    print(f"  Downloading arXiv:{test_id} ...")
    pdf_path = download_arxiv_pdf(test_id)
    result["download_ok"] = pdf_path is not None
    if not pdf_path:
        result["pass"] = False
        result["error"] = "PDF download failed"
        _save("04_text_extraction", result)
        return False

    result["pdf_path"] = pdf_path
    result["pdf_size_bytes"] = Path(pdf_path).stat().st_size
    print(f"  Downloaded: {result['pdf_size_bytes']} bytes")

    # Step B: pymupdf4llm extraction (SOTA v2 pipeline)
    print(f"  Extracting text via pymupdf4llm ...")
    raw_md = extract_text_pymupdf4llm(pdf_path)
    result["raw_text_length"] = len(raw_md)
    result["raw_extraction_ok"] = len(raw_md) > 300
    print(f"  Raw markdown: {len(raw_md)} chars")

    if not raw_md or len(raw_md) < 300:
        result["pass"] = False
        result["error"] = "pymupdf4llm extracted too little text"
        _save("04_text_extraction", result)
        return False

    result["raw_text_preview"] = raw_md[:500]

    # Step C: Full v2 extraction pipeline (no LLM needed)
    from geo_perplexity.text_extractor import extract_full_text
    try:
        extraction = extract_full_text(pdf_path, use_llm_cleaning=False)
        full_text = extraction["full_text"]
        result["v2_extraction_ok"] = len(full_text) > 200
        result["v2_text_length"] = len(full_text)
        result["v2_text_preview"] = full_text[:500]
        result["v2_title"] = extraction["title"]
        result["v2_abstract_length"] = len(extraction["abstract"])
        result["v2_method"] = extraction["extraction_method"]
        print(f"  V2 full text: {len(full_text)} chars ({extraction['extraction_method']})")
    except Exception as exc:
        result["v2_extraction_ok"] = False
        result["v2_error"] = str(exc)
        result["v2_traceback"] = _sanitize_traceback(traceback.format_exc())
        print(f"  V2 extraction failed: {exc}")

    result["pass"] = result["raw_extraction_ok"]
    _save("04_text_extraction", result)
    return result["pass"]


# ── Test 5: Reference collection ──────────────────────────────────────

def test_reference_collection():
    """Check Semantic Scholar API and see how many refs have arXiv IDs."""
    print("\n[Test 5] Reference collection ...")
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from geo_perplexity.reference_collector import fetch_all_citations

    test_id = "2006.06138"
    result = {"arxiv_id": test_id}

    try:
        papers = fetch_all_citations(arxiv_id=test_id)
        result["n_total"] = len(papers)
        result["n_with_arxiv_id"] = sum(1 for p in papers if p.arxiv_id)
        result["n_with_abstract"] = sum(1 for p in papers if p.abstract)
        result["n_no_content"] = sum(1 for p in papers if not p.abstract and not p.arxiv_id)
        result["pass"] = len(papers) > 0

        # Sample details for the first 5
        result["sample_refs"] = [
            {
                "title": p.title[:80],
                "has_arxiv": bool(p.arxiv_id),
                "has_abstract": bool(p.abstract),
                "arxiv_id": p.arxiv_id,
            }
            for p in papers[:10]
        ]

        print(f"  Found {len(papers)} refs: "
              f"{result['n_with_arxiv_id']} with arXiv, "
              f"{result['n_with_abstract']} with abstract, "
              f"{result['n_no_content']} with nothing")
    except Exception as exc:
        result["pass"] = False
        result["error"] = str(exc)
        result["traceback"] = _sanitize_traceback(traceback.format_exc())
        print(f"  FAIL: {exc}")

    _save("05_reference_collection", result)
    return result.get("pass", False)


# ── Runner ────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Geo-Perplexity Smoke Tests")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    tests = [
        ("API connectivity", test_api_connectivity),
        ("Logprobs", test_logprobs),
        ("Mini perplexity", test_mini_perplexity),
        ("Text extraction", test_text_extraction),
        ("Reference collection", test_reference_collection),
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
    print("=" * 60)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")

    # Write overall summary
    _save("00_summary", {
        "tests": {k: v for k, v in results.items()},
        "all_passed": all(results.values()),
    })

    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
