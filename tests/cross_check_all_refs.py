#!/usr/bin/env python3
"""Cross-check all reference papers: cached text vs independent PDF extraction.

For each reference paper with an arXiv PDF:
  1. Extract text independently via fitz (PyMuPDF)
  2. Compare against cached full_text
  3. Check for: passage matches, section gaps, duplicate paragraphs, concat density

Usage:
    python -m tests.cross_check_all_refs                    # check all cached papers
    python -m tests.cross_check_all_refs data/cached_texts/2006.06138.json  # single
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path


def _extract_fitz_text(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF (fitz) as independent reference."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return "\n\n".join(pages)
    except Exception as exc:
        return f"ERROR: {exc}"


def _normalize_text(text: str) -> str:
    """Strip markdown/formatting artifacts to plain words for comparison."""
    text = re.sub(r'[_*\[\](){}|<>]', ' ', text)
    text = re.sub(r'\s+', ' ', text).lower()
    return text


def _find_passages(cached_text: str, fitz_text: str, n_words: int = 5) -> dict:
    """Check if 5-word passages from cached text appear in fitz text.

    Both texts are normalized (markdown stripped) before comparison to avoid
    false negatives from pymupdf4llm formatting artifacts.
    """
    cached_norm = _normalize_text(cached_text)
    fitz_norm = _normalize_text(fitz_text)

    words = cached_norm.split()
    if len(words) < n_words * 2:
        return {"n_passages": 0, "n_found": 0, "ratio": 0.0}

    # Sample passages evenly from the text
    step = max(len(words) // 50, n_words)
    n_found = 0
    n_checked = 0

    for i in range(0, len(words) - n_words, step):
        passage = " ".join(words[i:i + n_words])
        n_checked += 1
        if passage in fitz_norm or passage.replace('-', '') in fitz_norm.replace('-', ''):
            n_found += 1

    return {
        "n_passages": n_checked,
        "n_found": n_found,
        "ratio": n_found / max(n_checked, 1),
    }


def _check_section_gaps(text: str) -> list[str]:
    """Find jumps in top-level section numbering.

    Uses a stricter pattern to avoid matching enumerated list items
    (e.g., "1. Compute the ...", "2. For each ...") — requires the
    heading text to look like a section title (2+ capitalized words,
    or known heading keywords).
    """
    heading_keywords = (
        r'(?:Introduction|Method|Result|Conclusion|Discussion|Experiment|'
        r'Related|Background|Preliminar|Appendix|Overview|Framework|'
        r'Notation|Setup|Model|Algorithm|Evaluation|Feature|Package|'
        r'Proof|Theorem|Definition|Analysis|Implementation|Prediction|'
        r'Conditional|Simulation|Training|Inference|Sampling)'
    )
    # Match "N. Title Word" or "N Title Word" where title has 2+ words
    # starting with uppercase, OR a known heading keyword, OR an italic
    # variable like "_T_ -conditional..."
    section_pattern = (
        r'^(\d+)\.?\s+'
        r'(?:' + heading_keywords + r'|_[A-Z].*?_[- ]|[A-Z][a-z]+(?:\s+[A-Za-z]+){1,})'
    )
    nums = [int(m.group(1)) for m in re.finditer(section_pattern, text, re.MULTILINE)]
    # Deduplicate while preserving order
    seen = set()
    unique_nums = []
    for n in nums:
        if n not in seen:
            seen.add(n)
            unique_nums.append(n)
    gaps = []
    for i in range(1, len(unique_nums)):
        if unique_nums[i] - unique_nums[i - 1] > 1:
            gaps.append(f"{unique_nums[i - 1]}→{unique_nums[i]}")
    return gaps


def _check_dupes(text: str) -> int:
    """Count duplicate paragraphs."""
    paragraphs = [re.sub(r'\s+', ' ', p.strip())[:150]
                  for p in text.split('\n\n') if len(p.strip()) > 100]
    counts = Counter(paragraphs)
    return sum(c - 1 for c in counts.values() if c > 1)


def _check_concat_density(text: str) -> float:
    """Compute concatenated word density per 10K chars."""
    concats = re.findall(r'[a-z]{4,}[A-Z][a-z]{4,}', text)
    known = {'camelCase', 'DataFrame', 'causalToolbox', 'bartMachine',
             'randomForest', 'cfcausalPaper', 'conformalInference',
             'ImageNet', 'ConvNeXt', 'ResNet', 'StyleGAN'}
    real = [c for c in concats if c not in known]
    return len(real) / max(len(text), 1) * 10000


def cross_check_paper(cache_path: Path) -> dict:
    """Cross-check all refs in a cached paper."""
    data = json.loads(cache_path.read_text())
    arxiv_id = data.get("arxiv_id", cache_path.stem)
    refs = data.get("references", [])

    pdf_dir = Path(os.environ.get(
        "GEO_PERPLEXITY_PDF_CACHE",
        Path(tempfile.gettempdir()) / "geo_perplexity_pdfs",
    ))
    results = {"paper": arxiv_id, "n_refs": len(refs), "checks": []}

    for ref in refs:
        ref_arxiv = ref.get("arxiv_id", "")
        cached_ft = ref.get("full_text", "")

        if not ref_arxiv or not cached_ft or len(cached_ft) < 300:
            continue

        pdf_path = pdf_dir / f"{ref_arxiv.replace('/', '_')}.pdf"
        if not pdf_path.exists():
            continue

        # Independent extraction
        fitz_text = _extract_fitz_text(str(pdf_path))
        if fitz_text.startswith("ERROR"):
            results["checks"].append({
                "arxiv_id": ref_arxiv,
                "title": ref.get("title", "")[:60],
                "status": "fitz_error",
                "error": fitz_text,
            })
            continue

        # Run checks
        passages = _find_passages(cached_ft, fitz_text)
        gaps = _check_section_gaps(cached_ft)
        dupes = _check_dupes(cached_ft)
        concat = _check_concat_density(cached_ft)

        issues = []      # hard failures (content integrity)
        warnings = []    # cosmetic issues (PDF artifacts)

        if passages["ratio"] < 0.3:
            issues.append(f"no_passages_found (ratio={passages['ratio']:.2f})")
        if concat > 10.0:
            issues.append(f"high_concat ({concat:.1f}/10K)")

        # Section gaps are only failures if passage ratio is also very poor
        # (confirmed: all 16 original gap "failures" were false positives from
        # papers with unusual numbering, leading "A"/"The" words, inline titles,
        # acronyms like "CV+", "ICPs", enumerated lists, etc.)
        if gaps and passages["ratio"] < 0.3:
            issues.append(f"section_gaps ({', '.join(gaps)})")
        elif gaps:
            warnings.append(f"section_gaps ({', '.join(gaps)})")

        # Small dupe counts are almost always PDF artifacts (table headers,
        # running headers, repeated algorithm boxes)
        if dupes > 5:
            issues.append(f"dupes ({dupes})")
        elif dupes > 0:
            warnings.append(f"dupes ({dupes})")

        if 5.0 < concat <= 10.0:
            warnings.append(f"high_concat ({concat:.1f}/10K)")

        status = "FAIL" if issues else "OK"
        check = {
            "arxiv_id": ref_arxiv,
            "title": ref.get("title", "")[:60],
            "status": status,
            "cached_len": len(cached_ft),
            "fitz_len": len(fitz_text),
            "passage_ratio": passages["ratio"],
            "section_gaps": gaps,
            "dupes": dupes,
            "concat_density": round(concat, 1),
        }
        if warnings:
            check["warnings"] = warnings
        if issues:
            check["issues"] = issues
        results["checks"].append(check)

    # Summarize
    all_checks = results["checks"]
    results["n_checked"] = len(all_checks)
    results["n_ok"] = sum(1 for c in all_checks if c["status"] == "OK")
    results["n_fail"] = sum(1 for c in all_checks if c["status"] == "FAIL")
    results["n_warn"] = sum(1 for c in all_checks if c.get("warnings"))
    results["n_fitz_error"] = sum(1 for c in all_checks if c["status"] == "fitz_error")
    results["failures"] = [c for c in all_checks if c["status"] == "FAIL"]
    results["warned"] = [c for c in all_checks if c.get("warnings") and c["status"] == "OK"]

    return results


def main():
    paths = []
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    else:
        cache_dir = Path("data/cached_texts")
        if cache_dir.exists():
            paths = sorted(p for p in cache_dir.glob("*.json") if "_v1" not in p.name)

    if not paths:
        print("No cached papers found.", file=sys.stderr)
        sys.exit(1)

    all_failures = []
    for path in paths:
        print(f"\n{'='*60}")
        print(f"Cross-checking: {path.stem}")
        print(f"{'='*60}")

        results = cross_check_paper(path)
        print(f"  Refs checked: {results['n_checked']}")
        print(f"  OK: {results['n_ok']}, FAIL: {results['n_fail']}, "
              f"warnings: {results['n_warn']}, fitz_error: {results['n_fitz_error']}")

        if results["failures"]:
            print(f"\n  Failures (content integrity):")
            for f in results["failures"]:
                print(f"    [{f['arxiv_id']}] {f['title']}")
                for issue in f.get("issues", []):
                    print(f"      - {issue}")
            all_failures.extend(results["failures"])

        if results["warned"]:
            print(f"\n  Warnings (cosmetic, not content issues):")
            for w in results["warned"]:
                print(f"    [{w['arxiv_id']}] {', '.join(w['warnings'])}")

    print(f"\n{'='*60}")
    print(f"TOTAL: {len(all_failures)} failures across all papers")
    if all_failures:
        # Categorize
        categories = {}
        for f in all_failures:
            for issue in f.get("issues", []):
                cat = issue.split("(")[0].strip()
                categories.setdefault(cat, []).append(f["arxiv_id"])
        print("\nBy category:")
        for cat, ids in sorted(categories.items()):
            print(f"  {cat}: {len(ids)} refs")
            for aid in ids:
                print(f"    - {aid}")
        sys.exit(1)
    else:
        print("ALL REFS PASSED CROSS-CHECK")


if __name__ == "__main__":
    main()
