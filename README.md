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
| 2006.06138 — Distribution-Free Risk-Controlling Prediction Sets | Conformal prediction | Abstract only |
| 2602.04770 — Conformal Prediction with Learned Features | Conformal prediction | Abstract only |
| 2103.04984 — Conformal Inference of Counterfactuals and ITEs | Causal inference | Full PDF |

## Development Roadmap

1. **v0.1**: One-off generation, 6 modes, full audit trail
2. **v0.2**: Dual backend, with_refs/no_refs conditions
3. **v0.3** (current): Teacher evaluation scoring, cross-condition comparison,
   pymupdf + arxiv HTML extraction, 3rd test paper
4. **v0.4**: Iterative teacher-student game with feedback loops
5. **v0.5**: Loop termination criteria (convergence detection, max rounds)
6. **v0.6**: Cross-paper comparison and novelty ranking
