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
| Unit tests (`pytest -m "not slow"`) | GitHub Actions | ~$0.02/run | ~2 min |
| Unit tests (local) | This sandbox | Free | <1 sec |
| Teacher hint extraction | This sandbox -> API | ~$0.15/paper (Opus, 60K input) | ~30s |
| Student reconstruction (x6 modes) | This sandbox -> API | ~$0.03/mode (Sonnet) | ~10s each |
| Teacher evaluation (x6 modes) | This sandbox -> API | ~$0.10/mode (Opus, 30K input) | ~15s each |
| **Full run (2 papers x 2 conditions x 6 modes)** | This sandbox -> API | **~$3-5 total** | **~15-30 min** |

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
|   +-- main()                  L643  CLI arg parsing + dispatch loop
|
+-- infra/                      <-- SUPPORTING MODULES
|   |-- llm.py                  L1    LLM call wrapper + retry-with-backoff
|   |-- evaluate.py             L1    Teacher evaluation scoring rubric
|   |-- audit.py                L1    AuditLog for reproducibility
|   +-- pdf_utils.py            L1    PDF download/extraction/caching
|
+-- prompts/                    <-- PROMPT TEMPLATES
|   |-- teacher_extract.txt           Teacher: extract problem hint (NO leakage)
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
|   |-- run07-v0.4-improved-eval/     Partial run (rate limited)
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
```

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
