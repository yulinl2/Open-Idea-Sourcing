# Text Extraction: Strategies, Caveats, and Failure Modes

## Date: 2026-04-08

## Background

The original extraction pipeline (v1) used **pdfplumber** for raw PDF text
extraction followed by a **GPT-4o agentic parser** (2-pass LLM with JSON
structured output).  This produced severely degraded results:

| Paper | v1 full_text | v1 abstract | Actual PDF size | Coverage |
|-------|-------------|-------------|-----------------|----------|
| 2006.06138 | 8,902 chars | 0 chars | 111,896 chars | 8% |
| 2602.04770 | 2,652 chars | 0 chars | 77,842 chars | 3.4% |

Root causes:
1. pdfplumber produces garbled text from multi-column layouts (concatenated words)
2. LLM parser only receives first 15K chars, truncating 85%+ of content
3. Title/abstract extraction relied on fragile regex over garbled raw text
4. Reference papers capped at 15K chars in raw fallback mode

The v2 pipeline uses **pymupdf4llm** (PyMuPDF markdown backend) as the
primary extractor, achieving 7–14x more content with zero LLM cost for
extraction.

---

## Extraction Pipeline (v2)

### Architecture

```
PDF file
  │
  ├─ pymupdf4llm.to_markdown()          ← SOTA, handles columns/math/tables
  │    └─ _strip_references_section()    ← remove bibliography
  │    └─ _strip_markdown_artifacts()    ← clean formatting, page numbers, figure markers
  │    └─ _strip_running_headers()       ← remove repeated page headers
  │    └─ (optional) LLM cleaning pass   ← GPT-4o for target papers only
  │
  ├─ [fallback] pdfminer.six            ← layout-based extraction
  │
  └─ [fallback] abstract from Semantic Scholar
```

### Key Design Decisions

1. **pymupdf4llm over pdfplumber**: pymupdf4llm uses PyMuPDF's internal
   layout engine + optional ONNX-based layout detection.  It produces clean
   markdown with proper heading hierarchy, paragraph separation, and math
   symbol preservation.  pdfplumber frequently concatenates words from
   multi-column PDFs (e.g., "ZhengyangGeng1,2,3,*" instead of
   "Zhengyang Geng").

2. **No LLM for reference extraction**: Reference papers use pymupdf4llm
   only (no LLM cleaning pass).  This keeps cost at zero for the ~60–90
   reference papers per target paper, while still producing 25–53K chars of
   clean text per reference (vs. 5–11K in v1).

3. **SIGALRM timeout**: pymupdf4llm's ONNX layout analysis can hang on
   very large PDFs (100+ pages).  A 120-second signal-based timeout prevents
   blocking the entire pipeline.  If it times out, the pipeline falls back
   to pdfminer.six.

4. **Reference stripping before artifact cleaning**: The bibliography is
   removed first because markdown artifact patterns (bold markers, headings)
   also appear in reference entries and could confuse downstream cleaning.

---

## Known Failure Modes and Fixes

### 1. The `<[^>]+>` HTML Regex Bug (CRITICAL — fixed)

**Symptom**: 52% of body text silently deleted, entire sections vanish.

**Cause**: A naive HTML tag removal regex `re.sub(r'<[^>]+>', '', text)`
intended to strip `<br>` tags also matches math inequality signs (`<`, `>`)
in pymupdf4llm output.  A single match from `<==**` (figure placeholder
closing) to the next `>` (in something like `E[X] < ∞`) ate up to 11,896
characters of body text.

**Fix**: Replace with targeted regex that only matches real HTML tags:
```python
re.sub(r'<(?:br|hr|/?\w{1,10})(?:\s[^>]{0,50})?/?>', '', text)
```

**Detection**: The `no_section_gaps` validation check catches this by
detecting jumps in section numbering (e.g., section 2 → section 5).

### 2. Inline Abstract Extraction

**Symptom**: Abstract starts mid-sentence or extracts body text instead.

**Cause**: pymupdf4llm may render `**Summary** . Evaluating treatment...`
(bold heading + text on same line) or `**Abstract**\n\nWe propose...`
(heading on separate line).  A regex that requires `\n` after the heading
keyword misses the inline variant.

**Fix**: Allow optional `\n` in the capture pattern:
```python
r'(?:Abstract|ABSTRACT|Summary)(?:\*{0,2})?[:\.\s]*\n?(.*?)(?=next_section)'
```

**Detection**: `abstract_in_early_text` checks that the cached abstract
appears in the first 5K chars of full_text.

### 3. pymupdf4llm Figure Placeholders

**Symptom**: Text like `**==> picture [322 x 215] intentionally omitted <==**`
scattered through body text, or `--- Start of picture text ---` / 
`--- End of picture text ---` markers with figure OCR text between them.

**Fix**: Two explicit regex removals in `_strip_markdown_artifacts()`:
```python
# Figure placeholders
re.sub(r'\*{0,2}=+>\s*picture\s*\[[^\]]*\]\s*intentionally omitted\s*<?=+\*{0,2}', '', text)
# Picture text block markers
re.sub(r'-{3,}\s*(?:Start|End) of picture text\s*-{3,}', '', text)
```

**Note**: The OCR text from inside figures (axis labels, legends) is NOT
removed.  This text occasionally contains concatenated words (e.g.,
`varianceConditional` from axis labels) which is harmless for perplexity
analysis.

### 4. Running Page Headers

**Symptom**: Repeated lines like `5\n\nGenerative Modeling via Drifting`
throughout the text (page number + paper title on each page).

**Fix**: Two-layer removal:
1. **Standalone page numbers**: `re.sub(r'\n\n\d{1,3}\s*\n\n', '\n\n', text)`
   removes isolated digits between blank lines.
2. **Title-specific headers**: `_strip_running_headers(text, title)` uses the
   known paper title to match `<number>\n\n<title>` patterns.

**Detection**: `no_running_headers` validation check.

### 5. pymupdf4llm ONNX Timeout

**Symptom**: Pipeline hangs indefinitely on large PDFs.

**Cause**: The ONNX layout detection model processes each page and can take
minutes on 50+ page PDFs with complex layouts (tables, figures).

**Fix**: `signal.alarm(_EXTRACT_TIMEOUT)` with a 120-second timeout.  Falls
back to pdfminer.six, which is slower but more predictable.

**Caveat**: `signal.SIGALRM` only works on Unix.  If running on Windows,
a threading-based timeout would be needed instead.

### 6. Garbled Math Brackets

**Symptom**: Complex math renders as `[X][i] _[∈]_[R] _[p]_[and]`.

**Cause**: pymupdf4llm's text extraction from PDFs with complex
subscripts/superscripts produces bracket-notation artifacts.  This is a
known limitation — the layout engine represents sub/superscript runs as
bracket-delimited segments.

**Impact**: Affects ~0.65% of total text.  Prose around the math remains
fully readable.  Not worth fixing since:
- The perplexity model sees enough surrounding context
- LLM cleaning could fix it but costs ~$0.01/page × 90 refs = $0.90/paper
- The garbled notation is consistent across papers (doesn't bias comparisons)

---

## Validation Strategy

### Zero-Cost Automated Checks (`tests/validate_extraction.py`)

Run after every cache rebuild: `python -m tests.validate_extraction`

| # | Check | Catches | Severity |
|---|-------|---------|----------|
| 1 | `title_present` | Empty/missing title | error |
| 2 | `abstract_present` | Empty/missing abstract | error |
| 3 | `full_text_present` | Extraction completely failed | error |
| 4 | `content_ratio` | Truncation (<15%) or bloat (>95%) | error/warn |
| 5 | `section_coverage` | Missing sections, garbled structure | warning |
| 6 | `no_reference_bleed` | Bibliography leaked into body text | error |
| 7 | `no_duplicate_paragraphs` | Copy-paste duplication | warning |
| 8 | `no_section_gaps` | The `<[^>]+>` bug — content deleted between sections | error |
| 9 | `low_concat_density` | Words smashed together (old pdfplumber bug) | warning |
| 10 | `no_running_headers` | Page number/title repetition | warning |
| 11 | `abstract_in_early_text` | Wrong text extracted as abstract | warning |
| 12 | `ref_coverage` | Too many refs with no content | error/warn |
| 13 | `ref_no_bib_bleed` | Refs include their own bibliography | warning |

**Cost**: Zero — all checks are regex/string-based, no API calls.

**When to run**: After every `cache_texts.py` execution.  Can be added to CI.

### When to Suspect Extraction Problems

1. **Content ratio < 30%** for a paper without appendices → likely content
   being deleted by a regex
2. **Content ratio > 95%** → references not being stripped
3. **Section gaps** (e.g., 2 → 5) → a cleaning regex is eating content
   between sections
4. **Abstract not in early text** → the abstract regex matched a body
   occurrence of "abstract" or "summary" instead of the heading

---

## Performance Characteristics

### Extraction Speed

| Component | Time per paper | Notes |
|-----------|---------------|-------|
| PDF download (arXiv) | 1–5s | Rate-limited; cached locally |
| pymupdf4llm extraction | 2–30s | Depends on page count; ONNX layout |
| Reference stripping + cleaning | <0.1s | Pure regex |
| Semantic Scholar API | 2–10s | Rate-limited (429s common) |
| Full pipeline (target + 90 refs) | 3–6 min | Dominated by ref PDF downloads |

### Cost

| Operation | Cost |
|-----------|------|
| pymupdf4llm extraction | $0 (local) |
| pdfminer.six fallback | $0 (local) |
| LLM cleaning (optional) | ~$0.02/paper (GPT-4o, 60K tokens) |
| Validation suite | $0 (regex-only) |
| Semantic Scholar API | $0 (free tier) |

### Storage

| File | Typical size |
|------|-------------|
| Target paper cache JSON | 300–2,500 KB |
| v1 audit copy | 400–800 KB |
| `.cache/pdf_text_v2/` | ~50 KB per ref (git-ignored) |

---

## Caveats for Future Development

1. **Don't use `<[^>]+>` to strip HTML in academic text.**  Math notation
   frequently contains `<` and `>` as inequality signs, angle brackets, and
   pymupdf4llm's figure markers.  Always use a whitelist of known tag names.

2. **pymupdf4llm output format may change between versions.**  The figure
   placeholder format (`**==> picture [...] <==**`) and picture-text markers
   (`--- Start of picture text ---`) are not documented as stable API.  Pin
   the pymupdf4llm version in `requirements.txt` and re-validate after upgrades.

3. **The reference-stripping regex assumes "References" appears once.**  If a
   paper has a section titled "References to Prior Work" or discusses
   "references" in the body, the regex might cut too early.  The 30%
   minimum-content guard prevents catastrophic truncation, but edge cases
   may lose content.  The `content_ratio` validation check catches this.

4. **pdfminer.six has a cryptography dependency conflict** on some systems
   (Debian's system `cryptography` package vs. pip's version).  If pdfminer
   fails to import, the pipeline still works — it just skips straight to the
   abstract-only fallback.

5. **Semantic Scholar rate limits aggressively** (HTTP 429).  The pipeline
   retries with exponential backoff (2s, 4s, 8s, 16s) up to 4 times.  For
   batch processing many papers, add longer delays between papers.

6. **Some older arXiv papers use scanned PDFs** (bitmap images, no text
   layer).  pymupdf4llm will return empty text for these.  The pipeline
   falls back to abstract-only, but true OCR (e.g., Tesseract, Nougat)
   would be needed for full extraction.  This is rare for post-2000 papers.

7. **`signal.SIGALRM` is Unix-only.**  The timeout mechanism for hung
   pymupdf4llm extractions won't work on Windows.  For cross-platform
   support, consider `threading.Timer` with `os.kill` as an alternative.

8. **v1 audit files should be kept** (`*_v1.json`) until the v2 pipeline
   has been validated in production perplexity runs.  They allow A/B
   comparison of extraction quality's impact on perplexity scores.

---

## Adding New Papers

```bash
# Cache a new paper
python cache_texts.py https://arxiv.org/abs/XXXX.XXXXX --no-llm-clean

# Validate extraction quality
python -m tests.validate_extraction data/cached_texts/XXXX.XXXXX.json

# Force re-cache (preserves v1 automatically)
python cache_texts.py --force https://arxiv.org/abs/XXXX.XXXXX
```

If validation fails, check the specific failing check against the failure
modes documented above.  The most common fix is adding a new regex pattern
to `_strip_markdown_artifacts()` for whatever artifact pymupdf4llm produced
for that particular PDF layout.
