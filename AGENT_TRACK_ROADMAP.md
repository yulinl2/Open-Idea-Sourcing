# AGENT_TRACK_ROADMAP.md

Implementation roadmap for the three agent-track branches and the shared `infra-base`.  
Read `PROJECT_INSTRUCTIONS_AGENT.md` first for the scientific charter and guiding principles.

---

## Table of Contents

1. [Overview and branch topology](#1-overview-and-branch-topology)
2. [infra-base — shared execution shell](#2-infra-base--shared-execution-shell)
3. [agent-e2e — end-to-end autonomous baseline](#3-agent-e2e--end-to-end-autonomous-baseline)
4. [agent-linear — checkpointed linear baseline](#4-agent-linear--checkpointed-linear-baseline)
5. [agent-reconstruct — reconstruction and discovery track](#5-agent-reconstruct--reconstruction-and-discovery-track)
6. [Human workflow](#6-human-workflow)
7. [Cross-track comparison protocol](#7-cross-track-comparison-protocol)

---

## 1. Overview and branch topology

```
infra-base          ← orphan; shared execution shell only
    │
    ├─ cherry-pick ─► agent-e2e          ← end-to-end autonomous baseline
    ├─ cherry-pick ─► agent-linear       ← checkpointed linear baseline
    └─ cherry-pick ─► agent-reconstruct  ← free reconstruction / discovery
```

Rules:
- **`infra-base`** is the only branch all three tracks may cherry-pick from.
- Track branches never merge into each other.
- Track branches never merge back into `main` or `infra-base`.
- Each track is a **self-contained world**: its `agent.py` (or equivalent entry point) and `report.md` template are the only files a reviewer needs to read.

---

## 2. infra-base — shared execution shell

### Purpose

Provide the **minimum shared substrate** that all three tracks need without
dragging in any track-specific logic or roleplay taxonomy. This is infrastructure,
not methodology.

### What belongs here

| Module | Role |
|--------|------|
| `infra/run_context.py` | `RunContext` dataclass — holds `paper_id`, `model`, `impl_id`, `track`, timestamps, git hash, tool list, `response_id`. Serialises to/from YAML front matter. |
| `infra/report_writer.py` | Writes the canonical `report.md` from a filled `RunContext` + structured sections. Enforces the required front-matter schema. |
| `infra/tool_registry.py` | Thin registry mapping Python-function tool names to callables; records invocations per run. Native model tools (e.g. `web_search`) bypass this and are captured via `response_id`. |
| `infra/search_tools.py` | **Last-resort fallback only.** Semantic Scholar + arXiv thin clients for when the model's native web search is unavailable or when structured S2 metadata (citation counts, canonical paper IDs) is specifically needed. |
| `infra/pdf_utils.py` | PDF-to-text extraction. No LLM logic. |
| `infra/README.md` | One-page description of every module and the cherry-pick contract. |

### What does NOT belong here

- Any agent roles, prompts, or judgment logic.
- Any track-specific orchestration.
- Any version-specific frozen snapshots (those stay in the track branch beside `agent.py`).

### Build sequence

```
Step 1  infra/run_context.py       — RunContext dataclass + YAML serialisation
Step 2  infra/report_writer.py     — report.md template enforcement
Step 3  infra/search_tools.py      — S2 + arXiv thin clients
Step 4  infra/pdf_utils.py         — PDF extraction wrapper
Step 5  infra/tool_registry.py     — tool call recorder
Step 6  infra/README.md            — cherry-pick contract documentation
```

### File layout

```
infra-base branch
└── infra/
    ├── README.md
    ├── run_context.py
    ├── report_writer.py
    ├── search_tools.py
    ├── pdf_utils.py
    └── tool_registry.py
```

---

## 3. agent-e2e — end-to-end autonomous baseline

### Scientific purpose

Establish the **simplest possible agentic baseline**: hand the agent a paper and
let it autonomously decide what tools to call, in what order, with minimal
external scaffolding. This is the "zero-shot agentic reviewer" — useful as a
lower-bound comparison point for the other tracks.

### Design principles

- Single entry point: `agent.py`
- Agent drives its own tool loop; no externally imposed stage ordering
- One `report.md` output; no intermediate checkpoint files
- Implementation identity declared at top: `AGENT_IMPL_ID = "e2e_v1_0_0"`

### Philosophy: maximally agentic

Do **not** implement custom search functions for what the model can do natively.
Use the model's built-in `web_search` tool as the primary retrieval mechanism — let
the agent decide what to search for, in what order, and when it has enough evidence.
`infra/search_tools.py` (S2, arXiv) is available as a last resort only (e.g., when
structured citation metadata is needed).

### Methodology

```
[Input]  paper URL or local PDF
    │
    ▼
[Agent loop]
    The agent reads the paper text and autonomously:
      - searches the web for related prior work (native web_search tool)
      - follows leads as it sees fit (no externally imposed search strategy)
      - decides how many comparison rounds to perform
      - decides when it has enough evidence to produce a verdict
    No external orchestrator imposes stage order or search order.
    │
    ▼
[Output]  report.md
    Contains: derivation audit, derivation map, residual novelty verdict
```

### Tool set

| Tool | Source | Purpose |
|------|--------|---------|
| `web_search` | Native model tool | Primary literature search — let the agent decide queries |
| `fetch_paper_text` | `infra/pdf_utils.py` | PDF/HTML ingestion; model can't read PDFs natively |
| `search_semantic_scholar` | `infra/search_tools.py` | **Fallback only** — structured S2 metadata when needed |

The agent should rely on `web_search` for discovery; do not pre-build rigid search pipelines.

### Build sequence

```
Step 1  cherry-pick infra/ from infra-base
Step 2  agent.py v1 — paper ingestion + native web_search tool loop; single verdict
Step 3  prompts/system.txt — agent system prompt (judgment standard, report schema)
Step 4  Freeze: agent_e2e_v1_0_0.py (adjacent snapshot)
Step 5  agent.py v2 — richer derivation map, uncertainty quantification
Step 6  Git tag: agent-e2e-v1.0.0
```

### File layout

```
agent-e2e branch
├── agent.py                  ← active implementation
├── agent_e2e_v1_0_0.py       ← frozen snapshot of v1
├── report_template.md        ← canonical report.md schema
├── prompts/
│   ├── system.txt            ← agent system prompt
│   └── verdict.txt           ← verdict synthesis prompt
├── infra/                    ← cherry-picked from infra-base
└── README.md
```

### AGENT_IMPL_ID versioning rule

Every `agent.py` declares at the top:

```python
AGENT_IMPL_ID = "e2e_v1_0_0"
```

Every `report.md` front matter echoes this:

```yaml
impl_id: e2e_v1_0_0
```

When a meaningful milestone is reached, freeze `agent.py` → `agent_e2e_vX_Y_Z.py`
beside it and bump `AGENT_IMPL_ID`.

---

## 4. agent-linear — checkpointed linear baseline

### Scientific purpose

Establish a **staged, auditable baseline** with explicit ordered checkpoints.
Each checkpoint serialises the pipeline context so any stage can be re-run
independently. This makes ablation and debugging tractable and provides a clean
comparison point against the free-form `agent-e2e` and exploratory
`agent-reconstruct` tracks.

### Design principles

- Explicit stage sequence; no autonomous reordering
- Each stage writes a checkpoint file: `checkpoints/stage_N.json`
- A stage can be re-run from its checkpoint without re-running prior stages
- Implementation identity declared at top: `AGENT_IMPL_ID = "linear_v1_0_0"`

### Stage sequence

```
Stage 1  Ingest
         Input:  paper URL / local PDF
         Output: checkpoints/stage_1_paper.json
                 {title, abstract, full_text, paper_id, source_url}

Stage 2  Decompose
         Input:  stage_1_paper.json
         Output: checkpoints/stage_2_decomp.json
                 {core_concept, technical_units[], assumptions[], bottleneck}
         Prompt: prompts/decompose.txt

Stage 3  Retrieve
         Input:  stage_2_decomp.json
         Output: checkpoints/stage_3_refs.json
                 {candidates[]: {paper_id, title, year, source, snippet}}
         Primary: native web_search tool — let the agent form its own queries
         Fallback: infra/search_tools.py (S2/arXiv) for structured metadata
         Rule:   agent decides search strategy; dedup candidates by paper_id

Stage 4  Compare
         Input:  stage_2_decomp.json + stage_3_refs.json
         Output: checkpoints/stage_4_comparisons.json
                 {comparisons[]: {ref_id, overlap[], differences[], derivation_path}}
         Prompt: prompts/compare.txt
         Rule:   top-K candidates only (K configurable); explicit per-paper comparison

Stage 5  Judge
         Input:  stage_4_comparisons.json
         Output: checkpoints/stage_5_judgment.json
                 {duplication, combination, equivalence, residual_novelty}
         Prompts: prompts/judge_dup.txt, prompts/judge_combo.txt, prompts/judge_equiv.txt
         Rule:   each dimension is an independent LLM call; chained context

Stage 6  Synthesise
         Input:  stage_5_judgment.json
         Output: checkpoints/stage_6_synthesis.json
                 {verdict, confidence, derivation_map, cited_evidence[]}
         Prompt: prompts/synthesise.txt

Stage R  Render
         Input:  all checkpoints
         Output: report.md
         Rule:   pure function; no LLM; deterministic
```

### Build sequence

```
Step 1  cherry-pick infra/ from infra-base
Step 2  pipeline.py — Pipeline([Stage, ...]) orchestrator + checkpoint I/O
Step 3  stages/ingest.py, stages/decompose.py
Step 4  stages/retrieve.py (with toggle flags per source)
Step 5  stages/compare.py, stages/judge.py, stages/synthesise.py
Step 6  stages/render.py — report.md writer
Step 7  agent.py — thin CLI that wires stages and runs pipeline
Step 8  Freeze: agent_linear_v1_0_0.py
Step 9  Git tag: agent-linear-v1.0.0
```

### File layout

```
agent-linear branch
├── agent.py                     ← active CLI entry point
├── agent_linear_v1_0_0.py       ← frozen snapshot
├── pipeline.py                  ← Pipeline class + checkpoint I/O
├── stages/
│   ├── ingest.py
│   ├── decompose.py
│   ├── retrieve.py
│   ├── compare.py
│   ├── judge.py
│   ├── synthesise.py
│   └── render.py
├── prompts/
│   ├── decompose.txt
│   ├── compare.txt
│   ├── judge_dup.txt
│   ├── judge_combo.txt
│   ├── judge_equiv.txt
│   └── synthesise.txt
├── checkpoints/                 ← gitignored; produced at runtime
├── infra/                       ← cherry-picked from infra-base
└── README.md
```

### Re-run protocol (human-facing)

To re-run from Stage 4 (e.g., to swap the comparison prompt):

```bash
python agent.py --paper-id 2006.06138 --from-stage 4
```

This reads `checkpoints/stage_3_refs.json` as the input and re-runs stages 4–R.

---

## 5. agent-reconstruct — minimal teacher-student reconstruction track

### Scientific purpose

This track operationalizes novelty as **reconstruction distance**: how much effort
(measured by mismatch between student's reconstruction and the actual paper) does it
take to recover a paper's methodology from its problem statement and prior work alone?

- A close reconstruction (verdict `MATCHED`) → the paper is largely derivable; the
  contribution was already in the prior-work hull.
- A large divergence (verdict `DIVERGED`) → the paper required a genuinely new leap;
  that leap is the irreducible novel contribution.

This is analogous to a **Wasserstein-like distance** between a paper and its prior-work
hull, measured not by embedding similarity but by reconstruction difficulty. The student's
effort and mismatch *is* the distance metric.

The `agent-e2e` and `agent-linear` tracks retrieve and compare; this track
**removes the paper from the picture entirely** and tests whether the methodology can
be re-derived independently. The comparison verdict directly quantifies novelty.

### Design principles

- **Teacher agent**: reads the full paper; extracts a minimal problem-definition hint
  (the domain problem to be solved) — *no solution revealed*
- **Student agent**: given only the hint + allowed references; develops a methodology
  from first principles and the provided references; **no external search allowed**
- One `report.md` output: contains the student's reconstruction and a comparison
  section noting where it matches or diverges from the actual paper
- No fixed stage sequence; minimal external scaffolding
- Implementation identity declared at top: `AGENT_IMPL_ID = "reconstruct_v1_0_0"`

### Methodology (v1 — minimal)

```
[Input]  paper (PDF or URL) + allowed reference list (arXiv IDs or PDFs)
    │
    ▼
[Teacher agent]
    Reads the full paper.
    Produces a minimal problem-definition hint:
      - The domain and subfield
      - The specific technical problem being addressed
      - The evaluation criteria (what a good solution looks like)
    Does NOT reveal: the paper's approach, key design decisions, or results.
    │
    ▼
[Student agent]
    Receives: hint + allowed reference texts only.
    No external search. No access to the full paper.
    Task: develop and detail a methodology to solve the stated problem,
          using the allowed references as building blocks.
          Aim for maximum technical depth without resorting to external sources.
    Output: a structured methodology description (approach, components,
            expected behaviour, any key design decisions made)
    │
    ▼
[Comparison pass]
    Compare student's methodology against the actual paper's approach.
    Note: components matched, components diverged, components missed.
    Quantify: reconstruction distance (MATCHED = ~0, DIVERGED = ~1)
    │
    ▼
[Output]  report.md
    Contains: hint used, student methodology, comparison table,
              reconstruction verdict (MATCHED / PARTIAL / DIVERGED),
              reconstruction distance score and evidence
```

### Tool set

| Agent | Allowed tools |
|-------|--------------|
| Teacher | `fetch_paper_text`, `pdf_utils.extract_text_from_pdf` |
| Student | `fetch_paper_text` (allowed refs only), `pdf_utils.extract_text_from_pdf` |
| Comparison | None (pure LLM synthesis) |

The student agent intentionally has **no search tools**. Its task is reconstruction
from the allowed reference set and its own reasoning — not retrieval.

### Build sequence

```
Step 1  cherry-pick infra/ from infra-base
Step 2  agent.py v1 — teacher + student loop (single LLM, two prompts)
Step 3  prompts/teacher.txt — problem-extraction prompt
        prompts/student.txt — reconstruction prompt
        prompts/compare.txt — comparison pass prompt
Step 4  Freeze: agent_reconstruct_v1_0_0.py
Step 5  Git tag: agent-reconstruct-v1.0.0
        (v2+ extensions: multiple students, hypothesis branching — deferred)
```

### File layout

```
agent-reconstruct branch
├── agent.py                           ← active implementation
├── agent_reconstruct_v1_0_0.py        ← frozen snapshot
├── prompts/
│   ├── teacher.txt                    ← problem-extraction prompt
│   ├── student.txt                    ← reconstruction prompt
│   └── compare.txt                    ← comparison pass prompt
├── infra/                             ← cherry-picked from infra-base
└── README.md
```

### Evolution philosophy

v1 is intentionally minimal. If the teacher-student split produces useful signal,
evolve toward multiple students (hypothesis branching), adversarial challenge
sub-agents, or iterative deepening — but only after v1 is frozen and evaluated.
Document all findings in `FINDINGS.md`; do not delete failed experiments.

---

## 6. Human workflow

### How agent CI runs in parallel with the baseline track

The baseline track (`ci.yml` → `review_paper.py`) and the agent tracks are
**separate GitHub Actions workflows** that run independently:

| Workflow | File | Entry point | Triggered by |
|----------|------|-------------|--------------|
| Baseline | `.github/workflows/ci.yml` | `review_paper.py` | All branches + manual |
| Agent track | `.github/workflows/agent-review.yml` | `agent.py` (per track) | `agent-*` branches + manual |

The two workflows never share a job or depend on each other. You can trigger
them simultaneously for the same paper without any interference.

**CI job separation:**

```
Push to main / feature branch
    └─► ci.yml → test → review_paper.py → reports/[paper_id]/

Manual dispatch on agent-review.yml
    └─► agent-review.yml → test-infra → agent.py (agent-<track> branch)
                                      → reports/agent-<track>/<paper_id>/
```

Reports from each workflow land under separate namespaces in the `reports`
branch, so they are easy to compare side by side.

### Triggering an agent review (all tracks)

1. Go to **Actions → Agent Track Review → Run workflow**
2. Fill in `paper_url` (arXiv abstract URL, e.g. `https://arxiv.org/abs/2006.06138`)
3. Select `track`: `e2e` | `linear` | `reconstruct`
4. Optionally set `model` (default: `gpt-4o`)
5. Click **Run workflow**

The CI job will:
- Check out the `agent-<track>` branch and run `agent.py`
- Upload `report.md` as a CI artifact named `agent-<track>-report-<paper_id>`
- Push `report.md` to the `reports` branch under `agent-<track>/<paper_id>/report.md`

**Push-triggered runs** (pushes to `agent-e2e`, `agent-linear`, `agent-reconstruct`):
- Run only the `test-infra` job (no API key needed)
- Gate on infra smoke tests before any review job is queued

### Reading a report

Every `report.md` is self-contained. A domain expert should be able to open it
on a phone and read the derivation audit without any additional context.

Required sections (see §7 of `PROJECT_INSTRUCTIONS_AGENT.md`):
- YAML front matter (metadata)
- Executive summary (1 paragraph)
- Final verdict (NOVEL / COMBINATION / EQUIVALENT / DUPLICATE)
- Technical contribution decomposition
- Strongest prior-work evidence (top 3–5 references with derivation notes)
- Derivation map (table or diagram: component → likely source)
- Residual novelty (what is genuinely new, if anything)
- Uncertainties (explicit; what was not found, what could not be verified)
- Audit appendix (tool calls, search queries, timestamps)

### Comparing runs across tracks

To compare `agent-e2e` vs `agent-linear` vs `agent-reconstruct` on the same paper:

1. Find the three `report.md` files under `reports/agent-<track>/<paper_id>/` on the `reports` branch
2. Compare `final_verdict` and `confidence` in YAML front matter
3. Compare `derivation_map` sections for agreement and disagreement
4. Compare `residual_novelty` for depth and specificity

To compare agent track results against the baseline programmatic pipeline:
- Baseline reports: `reports/<paper_id>/` (written by `ci.yml`)
- Agent reports: `reports/agent-<track>/<paper_id>/` (written by `agent-review.yml`)

The `impl_id` field in every front matter pinpoints the exact frozen snapshot
that produced the result, enabling exact replay.

### Adding a new frozen snapshot (developer workflow)

When a meaningful milestone is reached in any track:

1. Copy `agent.py` → `agent_[track]_v[X]_[Y]_[Z].py` in the same directory
2. Bump `AGENT_IMPL_ID` in `agent.py`
3. Commit: `git commit -m "freeze snapshot: [track] v[X].[Y].[Z]"`
4. Tag: `git tag agent-[track]-v[X].[Y].[Z]`

No reorganisation of directories is needed. The frozen copy sits beside the
active implementation and is immediately human-readable.

### Cherry-picking an infra improvement (developer workflow)

When `infra-base` gets an improvement that a track needs:

```bash
git cherry-pick <commit-hash-from-infra-base>
```

Run the track's tests to verify nothing broke. Commit message should reference
the infra-base commit: `cherry-pick infra: [description] (infra-base@<hash>)`.

---

## 7. Cross-track comparison protocol

The three tracks are designed to be compared on the same set of benchmark papers.
The recommended comparison set:

- At least one **clearly derivative paper** (known combination of prior work)
- At least one **clearly novel paper** (well-cited breakthrough)
- At least one **ambiguous paper** (mixed signals; good test of uncertainty handling)

For each paper × track combination, record in a shared `COMPARISON_LOG.md`:

| paper_id | track | impl_id | verdict | confidence | residual_novelty_quality | notes |
|----------|-------|---------|---------|------------|--------------------------|-------|
| 2006.06138 | e2e | e2e_v1_0_0 | COMBINATION | 0.72 | shallow | missed key prior |
| 2006.06138 | linear | linear_v1_0_0 | COMBINATION | 0.81 | medium | correct derivation path |
| 2006.06138 | reconstruct | reconstruct_v1_0_0 | NOVEL | 0.55 | deep | argued false residual |

The comparison log is maintained in the `main` branch so it aggregates across tracks.

A track is considered **scientifically winning** if its derivation audits are:
1. More accurate (fewer false NOVEL verdicts for derivative papers)
2. More specific (derivation map traces to specific sections/algorithms, not just paper titles)
3. Better calibrated (confidence scores correlate with actual correctness)

This comparison protocol is the primary feedback loop for evolving each track.
