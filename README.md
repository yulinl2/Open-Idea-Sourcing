# agent-staged-reconstruct

**Multi-mode teacher-student paper reconstruction pipeline.**

Given a research paper and its cited references, this pipeline measures how much
of the paper's intellectual contribution a capable LLM can reconstruct from
references alone — across 6 levels of reconstruction granularity.

## Scientific Goal

If a student model, given only the problem statement and cited references, can
closely reconstruct a paper's methodology, that suggests the contribution was
*highly derivable* from prior work. Conversely, large divergence signals
genuine novelty. By running 6 reconstruction modes (from abstract to full
paper), we get a granular signal about *which aspects* of a paper are novel.

Two experimental conditions enable controlled measurement:
- **with_refs**: student receives hint + reference abstracts
- **no_refs**: student receives hint only (baseline)

The delta between conditions isolates the information contribution of references.

## Architecture

```
Teacher (gpt-5.4 / claude-opus)          Student (gpt-4o / claude-sonnet)
──────────────────────────────           ────────────────────────────────
Reads full paper  ──┐                    Has NO paper access
Scores outputs   ──┐│                    Has NO web search
                   ││                    Has NO tools
                   ▼▼
           Problem hint
           (no solution   ───► Reconstructs from:
            leakage)           - Problem hint
                               - Reference abstracts (or none)
                               ─────────────────────
                               6 reconstruction modes:
                               1. Abstract
           Evaluation ◄────    2. Idea mindmap
           scores (1-5)        3. Problem formulation
           + novelty gap       4. Problem + methodology
                               5. Full paper (guided skeleton)
                               6. Full paper (freestyle)
```

## Output Structure

```
reports/
  <timestamp>/                         # timestamped dispatch
    SUMMARY.md                         # summary with scores + comparison
    results.json                       # machine-readable results
    <paper_id>/
      _teacher/
        hint.json                      # teacher's problem-context extraction
        audit.json                     # full LLM call audit trail
      with_refs/                       # condition: student has references
        abstract/
          output.md                    # student reconstruction
          audit.json                   # full audit trail
          eval.json                    # teacher evaluation scores
          eval_audit.json              # evaluation audit trail
        mindmap/
        problem/
        problem_method/
        full_guided/
        full_freestyle/
      no_refs/                         # condition: baseline without refs
        abstract/
        ...
      _pairwise/                       # side-by-side comparison (v0.5+)
        abstract.json                  # reference impact score (1-7)
        abstract_audit.json
        ...
```

## Usage

```bash
# Run all modes on all test papers with evaluation
python agent.py --evaluate

# Single paper, specific modes
python agent.py --paper-url https://arxiv.org/abs/2006.06138 --modes abstract mindmap

# Override models
python agent.py --student-model gpt-4o --teacher-model gpt-5.4

# Choose backend: auto (default), openai, anthropic
python agent.py --backend anthropic --evaluate

# Specific conditions only
python agent.py --conditions with_refs
```

Requires `OPENAI_API_KEY` or Anthropic auth (auto-detected).

## Paper Text Extraction

Resolution priority for arxiv papers:
1. `data/pdfs/<id>.txt` — pre-extracted text (highest quality)
2. `data/pdfs/<id>.pdf` — local PDF + pymupdf extraction
3. ar5iv HTML — preserves LaTeX math (when network available)
4. PDF download — last resort
5. Embedded abstract from `test_papers.ndjson` — minimal fallback

To add a paper's full text, place the PDF in `data/pdfs/<arxiv_id>.pdf`
or pre-extracted text in `data/pdfs/<arxiv_id>.txt`.

## Design Decisions

- **Student has no web search**: prevents knowledge leakage from the student
  retrieving the actual paper or its derivatives.
- **Teacher has web search available** (future): can enrich problem context
  with broader field awareness, improving prompt quality.
- **Output in Markdown**: avoids typesetting noise; LaTeX math in `$...$`
  renders in most viewers. Can be upgraded to PDF later with generic tooling.
- **Audit-first**: every LLM call is recorded with full prompts, responses,
  token counts, and timing for scientific reproducibility.
- **Dual backend**: supports both OpenAI (gpt-4o/gpt-5.4) and Anthropic
  (claude-sonnet/claude-opus) with auto-detection.

## Test Papers

| Paper | Domain | Full Text |
|-------|--------|-----------|
| 2006.06138 — Conformal Inference of Counterfactuals and ITEs (Lei & Candès) | Causal inference + conformal | Full PDF |
| 2602.04770 — Generative Modeling via Drifting (Deng et al.) | Generative models | Full PDF |

## Development Roadmap

1. **v0.1**: One-off generation, 6 modes, full audit trail
2. **v0.2**: Dual backend, with_refs/no_refs conditions
3. **v0.3**: Teacher evaluation scoring, cross-condition comparison,
   pymupdf + arxiv HTML extraction
4. **v0.3.1**: Full evaluation run with novelty gap analysis,
   cached PDF text extraction (archived — used hallucinated metadata)
5. **v0.4**: Anti-leakage teacher prompt redesign, improved eval rubric,
   reference_usage removed from composite, reconstruction_difficulty added
6. **v0.5.0** (current): Pairwise evaluator (side-by-side with_refs vs no_refs
   on 1-7 impact scale), calibrated scoring rubric with concrete anchors,
   mandatory reference-engagement instructions in all student prompts,
   retry-with-backoff for rate limits, teacher hint caching, API key priority
7. **v0.6** (planned): Cross-paper comparison and novelty ranking, batch API
   mode for 50% cost reduction, multi-run variance measurement
