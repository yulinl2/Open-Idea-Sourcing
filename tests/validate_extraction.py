"""Automated extraction quality validation — zero LLM cost.

Runs a suite of checks on cached text data to catch common extraction
failures BEFORE they reach the perplexity pipeline.  Designed to run
in CI or locally after every cache rebuild.

Usage:
    python -m tests.validate_extraction                     # validate all cached papers
    python -m tests.validate_extraction data/cached_texts/2006.06138.json  # single file

Checks performed:
    1. Structural completeness (title, abstract, full_text present and non-trivial)
    2. Content ratio (full_text should be 15-95% of raw_text — not truncated or bloated; more extreme ratios are treated more severely)
    3. Section coverage (body text should contain numbered sections or standard headings)
    4. Reference bleed (bibliography should NOT appear in full_text)
    5. Duplicate paragraphs (no paragraph repeated verbatim)
    6. HTML/math corruption (the <[^>]+> regex bug — detect leftover damage)
    7. Concatenated word density (flag if suspiciously high outside figure text)
    8. Running header contamination (repeated title/page numbers)
    9. Abstract sanity (should start near beginning of paper, not from body)
   10. Reference coverage (what fraction of refs have usable content)
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    check: str
    passed: bool
    message: str
    severity: str = "error"  # "error", "warning", "info"


@dataclass
class PaperValidation:
    """Full validation result for one cached paper."""
    paper_id: str
    path: str
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results if r.severity == "error")

    @property
    def n_errors(self) -> int:
        return sum(1 for r in self.results if not r.passed and r.severity == "error")

    @property
    def n_warnings(self) -> int:
        return sum(1 for r in self.results if not r.passed and r.severity == "warning")


def validate_cached_paper(path: str | Path) -> PaperValidation:
    """Run all validation checks on a single cached paper JSON."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        val = PaperValidation(paper_id=path.stem, path=str(path))
        val.results.append(ValidationResult(
            check="json_valid", passed=False,
            message=f"Corrupt cache file: {exc}",
        ))
        return val
    paper_id = data.get("arxiv_id", path.stem)
    val = PaperValidation(paper_id=paper_id, path=str(path))

    title = data.get("title", "")
    abstract = data.get("abstract", "")
    full_text = data.get("full_text", "")
    raw_text = data.get("raw_text", "")
    refs = data.get("references", [])

    # ── 1. Structural completeness ────────────────────────────────────
    val.results.append(ValidationResult(
        check="title_present",
        passed=bool(title and len(title) > 5),
        message=f"Title: '{title[:60]}' ({len(title)} chars)" if title else "Title is empty",
    ))
    val.results.append(ValidationResult(
        check="abstract_present",
        passed=bool(abstract and len(abstract) > 50),
        message=f"Abstract: {len(abstract)} chars" if abstract else "Abstract is empty",
    ))
    val.results.append(ValidationResult(
        check="full_text_present",
        passed=bool(full_text and len(full_text) > 500),
        message=f"Full text: {len(full_text):,d} chars",
    ))

    # ── 2. Content ratio ──────────────────────────────────────────────
    if raw_text and full_text:
        ratio = len(full_text) / len(raw_text)
        val.results.append(ValidationResult(
            check="content_ratio",
            passed=0.15 <= ratio <= 0.95,
            message=f"Content ratio: {ratio:.1%} (full_text/raw_text = {len(full_text):,d}/{len(raw_text):,d})",
            severity="error" if ratio < 0.10 or ratio > 0.98 else "warning",
        ))

    # ── 3. Section coverage ───────────────────────────────────────────
    if full_text:
        # Look for numbered sections (1., 2., 3., etc.) or common headings
        numbered = re.findall(r'^\d+\.?\s+[A-Z]', full_text, re.MULTILINE)
        headings = re.findall(
            r'(?i)\b(?:introduction|method|results?|conclusion|discussion|experiment|related work|appendix)\b',
            full_text,
        )
        n_sections = len(set(numbered)) + len(set(h.lower() for h in headings))
        val.results.append(ValidationResult(
            check="section_coverage",
            passed=n_sections >= 3,
            message=f"Sections found: {n_sections} (numbered: {len(numbered)}, headings: {len(headings)})",
            severity="warning",
        ))

    # ── 4. Reference bleed ────────────────────────────────────────────
    if full_text:
        tail = full_text[-3000:]
        ref_bleed = bool(re.search(
            r'\n\s*(?:#{1,3}\s*)?(?:\*{0,2})?References(?:\*{0,2})?\s*\n',
            tail, re.IGNORECASE,
        ))
        val.results.append(ValidationResult(
            check="no_reference_bleed",
            passed=not ref_bleed,
            message="Bibliography section found in tail of full_text" if ref_bleed else "No bibliography bleed",
        ))

    # ── 5. Duplicate paragraphs ───────────────────────────────────────
    if full_text:
        paragraphs = [p.strip() for p in full_text.split('\n\n') if len(p.strip()) > 100]
        seen = set()
        dupes = 0
        for p in paragraphs:
            norm = re.sub(r'\s+', ' ', p[:150])
            if norm in seen:
                dupes += 1
            seen.add(norm)
        val.results.append(ValidationResult(
            check="no_duplicate_paragraphs",
            passed=dupes == 0,
            message=f"{dupes} duplicate paragraphs out of {len(paragraphs)}" if dupes else f"No duplicates in {len(paragraphs)} paragraphs",
            severity="warning",
        ))

    # ── 6. HTML/math corruption (the <[^>]+> bug) ────────────────────
    if full_text:
        # Detect if massive chunks were eaten: look for suspicious jumps
        # between top-level section numbers.  Uses a strict pattern to avoid
        # matching enumerated list items (e.g., "1. Compute the ...").
        heading_keywords = (
            r'(?:Introduction|Method|Result|Conclusion|Discussion|Experiment|'
            r'Related|Background|Preliminar|Appendix|Overview|Framework|'
            r'Notation|Setup|Model|Algorithm|Evaluation|Feature|Package|'
            r'Proof|Theorem|Definition|Analysis|Implementation|Prediction|'
            r'Conditional|Simulation|Training|Inference|Sampling)'
        )
        section_pattern = (
            r'^(\d+)\.?\s+'
            r'(?:' + heading_keywords + r'|_[A-Z].*?_[- ]|[A-Z][a-z]+(?:\s+[A-Za-z]+){1,})'
        )
        section_nums = [int(m.group(1)) for m in re.finditer(section_pattern, full_text, re.MULTILINE)]
        # Deduplicate while preserving order
        seen_nums = set()
        unique_section_nums = []
        for n in section_nums:
            if n not in seen_nums:
                seen_nums.add(n)
                unique_section_nums.append(n)
        gaps = []
        for i in range(1, len(unique_section_nums)):
            if unique_section_nums[i] - unique_section_nums[i-1] > 1:
                gaps.append(f"{unique_section_nums[i-1]}→{unique_section_nums[i]}")
        val.results.append(ValidationResult(
            check="no_section_gaps",
            passed=len(gaps) == 0,
            message=f"Section number gaps: {', '.join(gaps)}" if gaps else "No section gaps detected",
        ))

    # ── 7. Concatenated word density ──────────────────────────────────
    if full_text:
        # camelCase that isn't a known package name
        concats = re.findall(r'[a-z]{4,}[A-Z][a-z]{4,}', full_text)
        # Filter known legitimate camelCase (R packages, method names)
        known_camel = {'camelCase', 'DataFrame', 'causalToolbox', 'bartMachine',
                       'randomForest', 'cfcausalPaper', 'conformalInference',
                       'ImageNet', 'ConvNeXt', 'ResNet', 'StyleGAN'}
        real = [c for c in concats if c not in known_camel]
        density = len(real) / max(len(full_text), 1) * 10000  # per 10K chars
        val.results.append(ValidationResult(
            check="low_concat_density",
            passed=density < 5.0,
            message=f"Concatenated words: {len(real)} ({density:.1f} per 10K chars)",
            severity="warning",
        ))

    # ── 8. Running header contamination ───────────────────────────────
    if full_text and title:
        esc = re.escape(title[:50])
        headers = re.findall(r'^\d{1,3}\s*\n\n' + esc, full_text, re.MULTILINE)
        val.results.append(ValidationResult(
            check="no_running_headers",
            passed=len(headers) == 0,
            message=f"{len(headers)} running page headers found" if headers else "No running headers",
            severity="warning",
        ))

    # ── 9. Abstract sanity ────────────────────────────────────────────
    if abstract and full_text:
        # Abstract should appear near the start of the full text
        abs_start = abstract[:80].lower()
        ft_lower = full_text[:5000].lower()
        abs_in_early = abs_start in ft_lower
        val.results.append(ValidationResult(
            check="abstract_in_early_text",
            passed=abs_in_early,
            message="Abstract text found in first 5K chars of full_text" if abs_in_early
                    else "Abstract text NOT found in early full_text — possible wrong extraction",
            severity="warning",
        ))

    # ── 10. Reference coverage ────────────────────────────────────────
    if refs:
        n_total = len(refs)
        n_content = sum(1 for r in refs if r.get('has_content'))
        n_full = sum(1 for r in refs if r.get('full_text') and len(r['full_text']) > 500)
        n_none = n_total - n_content
        coverage = n_content / max(n_total, 1)

        val.results.append(ValidationResult(
            check="ref_coverage",
            passed=coverage >= 0.40,
            message=f"Refs: {n_total} total, {n_full} full text, {n_content - n_full} abstract/tldr, {n_none} empty ({coverage:.0%} coverage)",
            severity="warning" if coverage >= 0.30 else "error",
        ))

        # Check ref text quality: no bibliography bleed in any ref
        refs_with_bleed = 0
        for r in refs:
            ft = r.get('full_text', '')
            if ft and len(ft) > 3000:
                if re.search(r'\nReferences\s*\n', ft[-3000:], re.IGNORECASE):
                    refs_with_bleed += 1
        val.results.append(ValidationResult(
            check="ref_no_bib_bleed",
            passed=refs_with_bleed == 0,
            message=f"{refs_with_bleed} refs have bibliography in text" if refs_with_bleed
                    else "No refs have bibliography bleed",
            severity="warning",
        ))

    return val


def print_validation(val: PaperValidation) -> None:
    """Pretty-print validation results."""
    status = "PASS" if val.passed else "FAIL"
    print(f"\n{'='*70}")
    print(f"[{status}] {val.paper_id}  ({val.n_errors} errors, {val.n_warnings} warnings)")
    print(f"{'='*70}")

    for r in val.results:
        if r.passed:
            icon = "OK"
        elif r.severity == "error":
            icon = "FAIL"
        else:
            icon = "WARN"
        print(f"  [{icon:4s}] {r.check:30s}  {r.message}")


def main():
    """Validate all cached papers or specific files."""
    paths = []
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    else:
        cache_dir = Path("data/cached_texts")
        if cache_dir.exists():
            paths = sorted(cache_dir.glob("*.json"))
            # Exclude v1 audit copies
            paths = [p for p in paths if "_v1" not in p.name]

    if not paths:
        print("No cached papers found to validate.", file=sys.stderr)
        sys.exit(1)

    all_passed = True
    for path in paths:
        val = validate_cached_paper(path)
        print_validation(val)
        if not val.passed:
            all_passed = False

    print(f"\n{'='*70}")
    if all_passed:
        print("ALL PAPERS PASSED VALIDATION")
    else:
        print("SOME PAPERS FAILED VALIDATION")
        sys.exit(1)


if __name__ == "__main__":
    main()
