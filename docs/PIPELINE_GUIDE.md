# Pipeline Guide

> Quick-reference for understanding what runs where, what costs what,
> and how to navigate each piece. Designed for fast scanning.

---

## 1. The Big Picture

```
YOU (laptop/phone)
 |
 |  chat via claude.ai/code
 v
CLAUDE CODE SANDBOX (this container)          GITHUB ACTIONS
 |                                             |
 |  python agent.py --evaluate ...             |  pytest (unit tests only)
 |  (LLM calls go to Anthropic/OpenAI API)     |  triggers on push
 |  (idle waiting = FREE)                       |  ~2 min, no API keys
 |                                             |
 v                                             v
ANTHROPIC / OPENAI API                        PASS / FAIL badge
 |
 |  billed per token
 v
reports/ folder --> git push --> GitHub
```

**Key insight:** The sandbox is free compute. LLM API calls cost money.
GitHub Actions minutes cost money. So: run experiments here, CI just runs tests.

---

## 2. What Runs Where

| Step | Where | Cost | Duration |
|------|-------|------|----------|
| Unit tests (83 tests) | Local | Free | <1 sec |
| Teacher hint extraction | API | ~$0.25/paper (Opus, 60K input) | ~17s |
| Student reconstruction (per mode) | API | ~$0.05/mode (Sonnet) | ~15-35s |
| Teacher evaluation (per mode) | API | ~$0.22/mode (Opus, 30K input) | ~19s |
| Teacher evaluation (per mode, Sonnet) | API | ~$0.05/mode (`--eval-model`) | ~12s |
| Pairwise comparison (per mode) | API | ~$0.10/mode (Opus, 30K input) | ~15s |
| **Single-shot (1 paper, 4 modes, both conditions)** | API | **~$3-4** | **~15 min** |
| **Iterative (1 paper, 4 modes, 1 condition)** | API | **~$8-9** | **~25 min** |
| **Iterative + `--eval-model sonnet`** | API | **~$4-5** | **~25 min** |
| **Iterative + `--parallel-modes`** | API | same cost | **~8 min** |

Validated on a 4-pair (2 papers × 2 refs) cross-comparison study.
Detailed per-stage and per-round breakdowns in
[reports/CROSS_PAIR_COMPARISON.md](../reports/CROSS_PAIR_COMPARISON.md).

---

## 3. File Map (click to jump)

```
Open-Idea-Sourcing/
|
+-- agent.py                    <-- MAIN ENTRY POINT (orchestration)
|   |-- _make_client()          L85   API key vs session token selection
|   |-- dispatch_paper()        L342  per-paper orchestration loop
|   |-- run_teacher()           L179  teacher hint extraction
|   |-- run_student()           L236  student reconstruction
|   |-- prepare_refs_text()     L288  reference text assembly
|   +-- main()                  L700  CLI arg parsing + dispatch loop
|
+-- infra/                      <-- SUPPORTING MODULES
|   |-- llm.py                  L1    LLM call wrapper + caching/chaining + retry
|   |-- iterative.py            L1    Iterative hint-refinement engine
|   |-- evaluate.py             L1    Teacher evaluation scoring rubric
|   |-- audit.py                L1    AuditLog for reproducibility
|   +-- pdf_utils.py            L1    PDF download/extraction/caching
|
+-- prompts/                    <-- PROMPT TEMPLATES
|   |-- teacher_extract.txt           Teacher: extract problem hint (NO leakage)
|   |-- teacher_refine_hint.txt       Teacher: refine hint (iterative mode)
|   |-- student_abstract.txt          Mode 1: reconstruct abstract
|   |-- student_mindmap.txt           Mode 2: idea mindmap
|   |-- student_problem_formulation.txt   Mode 3: problem section
|   |-- student_problem_and_method.txt    Mode 4: problem + method
|   |-- student_full_guided.txt       Mode 5: full paper (skeleton)
|   +-- student_full_freestyle.txt    Mode 6: full paper (free form)
|
+-- data/                       <-- INPUT DATA (source of truth)
|   |-- test_papers.ndjson            2 target papers (conformal + generative)
|   |-- references.json               Reference papers metadata
|   +-- pdfs/                         Cached PDFs + extracted text
|       |-- 2006.06138.pdf/txt        Lei-Candes (conformal inference)
|       |-- 2602.04770.pdf/txt        Deng et al (generative modeling)
|       +-- 1904.06019.pdf/txt        Tibshirani et al (reference)
|
+-- reports/                    <-- OUTPUT (one subfolder per run)
|   |-- run06-v0.4-antileak/          Complete run, old eval rubric
|   |-- run07-v0.4-improved-eval/     Complete run, calibrated rubric
|   |-- run08-v0.5-pairwise/          Complete run + pairwise comparison
|   +-- LEAKAGE_ANALYSIS.md           Info leakage findings doc
|
+-- tests/
|   +-- test_pipeline.py              33 unit tests (<1s total)
|
+-- .github/workflows/
|   +-- reconstruct.yml               CI: unit tests only (no experiments)
|
+-- docs/
    +-- PIPELINE_GUIDE.md             (this file)
```

---

## 4. How a Single Experiment Flows

```
                    +------------------+
                    |  test_papers     |
                    |  .ndjson         |
                    +--------+---------+
                             |
                     for each paper
                             |
                             v
                    +------------------+
                    |  TEACHER         |  reads full paper (60K chars)
                    |  (Opus)          |  extracts problem hint
                    |  agent.py:179    |  NO solution leakage
                    +--------+---------+
                             |
                        hint.json (cached -- reused if exists)
                             |
              +--------------+--------------+
              |                             |
         with_refs                      no_refs
              |                             |
    refs from data/references.json     refs_text = ""
    + full text from data/pdfs/
              |                             |
              v                             v
    +------------------+          +------------------+
    |  STUDENT x6      |          |  STUDENT x6      |
    |  (Sonnet)        |          |  (Sonnet)        |
    |  agent.py:236    |          |  agent.py:236    |
    |  modes:          |          |  same 6 modes    |
    |  abstract        |          |  but no refs     |
    |  mindmap         |          +--------+---------+
    |  problem         |                   |
    |  problem_method  |                   |
    |  full_guided     |                   |
    |  full_freestyle  |                   |
    +--------+---------+                   |
             |                             |
             v                             v
    +------------------+          +------------------+
    |  EVALUATOR x6    |          |  EVALUATOR x6    |
    |  (Opus)          |          |  (Opus)          |
    |  evaluate.py:86  |          |  evaluate.py:86  |
    |  scores 1-5 on:  |          |  same rubric     |
    |  - problem_understanding     +--------+---------+
    |  - technical_depth                    |
    |  - novelty_alignment                  |
    |  - writing_quality                    |
    |  - completeness                       |
    +--------+---------+                   |
             |                             |
             +-------------+---------------+
                           |
                           v
                  +------------------+
                  |  COMPARE         |
                  |  with_refs vs    |
                  |  no_refs scores  |
                  |  per mode        |
                  +------------------+
                           |
                           v
                  Delta = ref impact signal
                  Paper 1 (related ref): should be positive
                  Paper 2 (unrelated ref): should be ~0

                           |
                           v
                  +------------------+
                  |  PAIRWISE EVAL   |  (v0.5+)
                  |  (Opus)          |
                  |  evaluate.py:148 |
                  |  Side-by-side    |
                  |  A vs B on 1-7   |
                  |  scale           |
                  +------------------+
                           |
                           v
                  Reference Impact Score (1-7)
                  7 = refs dramatically helped
                  4 = no difference
                  1 = refs actively hurt
```

### Student reference engagement (v0.5+)

All student prompts include mandatory reference-engagement instructions:
students must build their approach ON TOP of the references, not just cite
them in passing. This prevents students from ignoring references and
reconstructing from general knowledge — which would make the with_refs vs
no_refs comparison meaningless.

---

## 5. Cost Optimization Features

| Feature | What it does | Savings |
|---------|-------------|---------|
| **Teacher hint caching** | Skips Opus call if `hint.json` exists in output dir | ~$0.15/paper on reruns |
| **Retry with backoff** | 429 errors wait 30s/60s/120s/240s instead of crashing | Avoids wasted partial runs |
| **API key priority** | `ANTHROPIC_API_KEY` env var checked before session token | Uses your API tier rate limits |
| **CI = tests only** | GitHub Actions only runs `pytest -m "not slow"` | No Actions minutes burned on LLM |

---

## 6. How to Run Experiments

**Full run (all papers, all modes, both conditions, with eval):**
```bash
python agent.py --evaluate --backend anthropic \
  --output-dir reports --timestamp run08-description
```

**Single paper, single condition (for debugging):**
```bash
python agent.py --evaluate --backend anthropic \
  --paper-url "https://arxiv.org/abs/2006.06138" \
  --conditions with_refs \
  --output-dir reports --timestamp test-run
```

**Specific modes only:**
```bash
python agent.py --evaluate --backend anthropic \
  --modes abstract problem_method full_freestyle \
  --output-dir reports --timestamp quick-3mode
```

---

## 7. Batch Processing API (Anthropic)

Anthropic offers a [Message Batches API](https://docs.anthropic.com/en/docs/build-with-claude/message-batches)
that processes requests asynchronously at **50% cost reduction**:

- You submit a batch of requests (up to 100K)
- Results come back within 24 hours (usually faster)
- No rate limits on submission
- Trade-off: latency (minutes-hours vs seconds)

**For this project:** A full run is ~50 API calls. Submitting as a batch
would cut the ~$3-5 cost to ~$1.50-2.50 and eliminate rate limit issues
entirely. The trade-off is you'd wait for results instead of streaming them.

To implement: modify `infra/llm.py` to support a `--batch` mode that
collects all requests, submits via `client.batches.create()`, polls for
completion, then maps results back to the output structure.

---

## 8. Environment Cheat Sheet

| Variable | Where to set | What it does |
|----------|-------------|-------------|
| `ANTHROPIC_API_KEY` | Cloud env settings | Anthropic API auth (preferred) |
| `OPENAI_API_KEY` | Cloud env settings | OpenAI API auth |
| _(session token)_ | Auto (Claude Code) | Fallback if no API key set |
