# AGENT_TRACK_ROADMAP.md

Per-branch implementation roadmap for the agent track. Read `PROJECT_INSTRUCTIONS_AGENT.md` first.

---

## Table of Contents

1. [Branch topology](#1-branch-topology)
2. [infra-base — shared execution shell](#2-infra-base--shared-execution-shell)
3. [agent-e2e — end-to-end autonomous baseline](#3-agent-e2e--end-to-end-autonomous-baseline)
4. [agent-linear — checkpointed linear baseline](#4-agent-linear--checkpointed-linear-baseline)
5. [agent-reconstruct — teacher-student reconstruction track](#5-agent-reconstruct--teacher-student-reconstruction-track)
6. [Human workflow and CI setup](#6-human-workflow-and-ci-setup)
7. [Cross-track comparison protocol](#7-cross-track-comparison-protocol)

---

## 1. Branch topology

```
infra-base              ← orphan; shared execution shell only
    │
    ├─ cherry-pick ──► agent-e2e          ← autonomous end-to-end baseline
    ├─ cherry-pick ──► agent-linear       ← checkpointed staged baseline
    └─ cherry-pick ──► agent-reconstruct  ← teacher-student reconstruction
```

Rules:
- **`infra-base`** is the only source all three track branches cherry-pick from.
- Track branches never merge into each other.
- Track branches never merge back into `main` or `infra-base`.
- `main` carries the baseline implementation and CI workflow files. Agent-track
  implementation code lives only on `infra-base` and the `agent-*` branches.

---

## 2. infra-base — shared execution shell

### Purpose

Provide the minimum substrate all three tracks need: run metadata, report rendering, tool call recording, PDF ingestion, and a last-resort search fallback. No methodology lives here.

### Module inventory

| Module | Purpose |
|--------|---------|
| `infra/run_context.py` | `RunContext` dataclass — holds all required metadata fields; serialises to/from YAML front matter. |
| `infra/report_writer.py` | `ReportWriter` — enforces the required `report.md` structure (YAML front matter + all required sections). |
| `infra/tool_registry.py` | Thin recorder for Python-function tool calls per run. Native model tools (e.g. `web_search`) are captured via `response_id`, not here. |
| `infra/search_tools.py` | **Last-resort fallback only.** Semantic Scholar + arXiv thin clients for structured citation metadata when the model's native search is insufficient. |
| `infra/pdf_utils.py` | PDF-to-text extraction. No LLM logic. |
| `infra/README.md` | One-page cherry-pick contract and module descriptions. |

### What does NOT belong here

- Agent roles, prompts, or judgment logic.
- Track-specific orchestration.
- Frozen implementation snapshots (those live beside `agent.py` in the track branch).

### Build sequence

```
Step 1  infra/run_context.py      — RunContext dataclass + YAML serialisation
Step 2  infra/report_writer.py    — report.md template enforcement
Step 3  infra/search_tools.py     — S2 + arXiv thin clients (last-resort)
Step 4  infra/pdf_utils.py        — PDF extraction wrapper
Step 5  infra/tool_registry.py    — tool call recorder
Step 6  infra/README.md           — cherry-pick contract
```

### File layout

```
infra-base branch
└── infra/
    ├── __init__.py
    ├── README.md
    ├── run_context.py
    ├── report_writer.py
    ├── search_tools.py
    ├── pdf_utils.py
    └── tool_registry.py
```

---

## 3. agent-e2e — end-to-end autonomous baseline

### Purpose

The simplest agentic baseline: hand the agent a paper and let it autonomously decide what to search, in what order, and when it has enough evidence. No externally imposed stage ordering. Serves as the lower-bound comparison point for the staged and reconstruction tracks.

### Design

- Single entry point: `agent.py`
- Agent drives its own tool loop — no external orchestrator
- One `report.md` output; no intermediate checkpoint files
- Implementation identity at top: `AGENT_IMPL_ID = "e2e_v1_0_0"`

**Tool philosophy:** use the model's native `web_search` tool as the primary mechanism. Do not pre-build rigid search pipelines. `infra/search_tools.py` is available as a last resort when structured citation metadata is specifically needed.

### Methodology

```
Input:  paper URL or local PDF
    │
    ▼
Agent loop
    The agent autonomously:
    - reads the paper text
    - searches the web for related prior work (native web_search)
    - follows leads as it sees fit
    - decides how many comparison rounds to perform
    - decides when it has enough evidence
    │
    ▼
Output: report.md
    Derivation audit, derivation map, residual novelty verdict
```

### Tool set

| Tool | Source | Purpose |
|------|--------|---------|
| `web_search` | Native model tool | Primary literature search — let the agent choose queries |
| `fetch_paper_text` | `infra/pdf_utils.py` | PDF/HTML ingestion |
| `search_semantic_scholar` | `infra/search_tools.py` | **Last-resort fallback** — structured S2 metadata |

### Build sequence

```
Step 1  cherry-pick infra/ from infra-base
Step 2  agent.py v1 — paper ingestion + native web_search loop; single verdict
Step 3  prompts/system.txt — judgment standard and report schema
Step 4  Freeze: agent_e2e_v1_0_0.py
Step 5  Git tag: agent-e2e-v1.0.0
```

### File layout

```
agent-e2e branch
├── agent.py                  ← active implementation (declares AGENT_IMPL_ID)
├── agent_e2e_v1_0_0.py       ← frozen snapshot of v1
├── prompts/
│   ├── system.txt            ← agent system prompt
│   └── verdict.txt           ← verdict synthesis prompt
├── infra/                    ← cherry-picked from infra-base
└── README.md
```

---

## 4. agent-linear — checkpointed linear baseline

### Purpose

A staged, auditable baseline with explicit ordered checkpoints. Each checkpoint serialises the pipeline state so any stage can be re-run independently. Ablation and debugging are tractable; the stage sequence provides a clear structural comparison against the free-form `agent-e2e` and the reconstruction approach of `agent-reconstruct`.

### Design

- Explicit stage sequence; no autonomous stage reordering
- Each stage reads its input checkpoint and writes its output checkpoint: `checkpoints/stage_N.json`
- Re-runnable from any stage: `python agent.py --paper-id 2006.06138 --from-stage 4`
- Implementation identity at top: `AGENT_IMPL_ID = "linear_v1_0_0"`

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
         Primary:  native web_search tool — agent forms its own queries
         Fallback: infra/search_tools.py for structured metadata
         Rule:   dedup candidates by paper_id

Stage 4  Compare
         Input:  stage_2_decomp.json + stage_3_refs.json
         Output: checkpoints/stage_4_comparisons.json
                 {comparisons[]: {ref_id, overlap[], differences[], derivation_path}}
         Prompt: prompts/compare.txt
         Rule:   top-K candidates only (K configurable)

Stage 5  Judge
         Input:  stage_4_comparisons.json
         Output: checkpoints/stage_5_judgment.json
                 {duplication, combination, equivalence, residual_novelty}
         Prompts: prompts/judge_dup.txt, prompts/judge_combo.txt, prompts/judge_equiv.txt
         Rule:   each judgment dimension is an independent LLM call

Stage 6  Synthesise
         Input:  stage_5_judgment.json
         Output: checkpoints/stage_6_synthesis.json
                 {verdict, confidence, derivation_map, cited_evidence[]}
         Prompt: prompts/synthesise.txt

Stage R  Render
         Input:  all checkpoints
         Output: report.md
         Rule:   pure rendering; no LLM calls
```

### Build sequence

```
Step 1  cherry-pick infra/ from infra-base
Step 2  pipeline.py — Pipeline orchestrator + checkpoint I/O
Step 3  stages/ingest.py, stages/decompose.py
Step 4  stages/retrieve.py
Step 5  stages/compare.py, stages/judge.py, stages/synthesise.py
Step 6  stages/render.py — report.md writer
Step 7  agent.py — thin CLI wiring stages and running pipeline
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

---

## 5. agent-reconstruct — teacher-student reconstruction track

### Purpose

The intuition: if an agent can reconstruct a paper's methodology from nothing but the problem statement and an allowed reference set — without ever seeing the paper's solution — the methodology was already derivable from prior work. If the reconstruction diverges significantly, the paper likely contains genuine novel contribution. Reconstruction difficulty is a proxy for novelty.

**v1 output:** a qualitative verdict (`MATCHED / PARTIAL / DIVERGED`) based on comparing the student's reconstruction against the actual paper.

> **Long-term aspiration, not a v1 goal:** How to formalise reconstruction difficulty as a principled quantitative distance metric (analogous to a distance from the paper to its prior-work hull) is an open research question. v1 does not attempt it.

### Design

- **Teacher agent** — reads the full paper; emits a minimal *problem-definition hint* (domain, specific technical problem, evaluation criteria); reveals no solution or design decisions.
- **Student agent** — receives only the hint and the allowed reference texts; reconstructs a methodology from scratch using the references and its own reasoning; has **no search tools** by design.
- **Comparison pass** — pure LLM synthesis comparing the student's methodology against the actual paper; produces a verdict and a matched/diverged breakdown.

One `report.md` output. No fixed stage sequence. Implementation identity at top: `AGENT_IMPL_ID = "reconstruct_v1_0_0"`.

### Methodology (v1)

```
Input:  paper (PDF or URL) + allowed reference list (arXiv IDs or local PDFs)
    │
    ▼
Teacher agent
    Reads the full paper.
    Emits a minimal problem-definition hint:
      - domain and subfield
      - specific technical problem being addressed
      - evaluation criteria (what a good solution looks like)
    Does NOT reveal: approach, key design decisions, results.
    │
    ▼
Student agent
    Receives: hint + allowed reference texts only.
    No external search. No access to the paper itself.
    Task: develop a detailed methodology for the stated problem
          using the allowed references and own reasoning.
    Output: structured methodology description
            (approach, components, design decisions, expected behaviour)
    │
    ▼
Comparison pass
    Compare student's methodology against the actual paper's approach.
    Produce: matched components, diverged components, missed components.
    │
    ▼
Output: report.md
    Contains: hint used, student reconstruction, comparison table,
              verdict (MATCHED / PARTIAL / DIVERGED)
```

### Tool set

| Agent | Allowed tools |
|-------|--------------|
| Teacher | `fetch_paper_text`, `pdf_utils.extract_text_from_pdf` |
| Student | `fetch_paper_text` (allowed refs only), `pdf_utils.extract_text_from_pdf` |
| Comparison | None — pure LLM synthesis |

The student has no search tools. Giving the student web search would undermine the controlled nature of the experiment.

### Build sequence

```
Step 1  cherry-pick infra/ from infra-base
Step 2  agent.py v1 — teacher + student loop (two prompts, one LLM)
Step 3  prompts/teacher.txt  — problem-extraction prompt
        prompts/student.txt  — reconstruction prompt
        prompts/compare.txt  — comparison pass prompt
Step 4  Freeze: agent_reconstruct_v1_0_0.py
Step 5  Git tag: agent-reconstruct-v1.0.0
```

v2+ extensions (deferred): multiple students, hypothesis branching, adversarial challenge sub-agents — only after v1 is frozen and evaluated.

### File layout

```
agent-reconstruct branch
├── agent.py                           ← active implementation
├── agent_reconstruct_v1_0_0.py        ← frozen snapshot
├── prompts/
│   ├── teacher.txt
│   ├── student.txt
│   └── compare.txt
├── infra/                             ← cherry-picked from infra-base
└── README.md
```

---

## 6. Human workflow and CI setup

### Parallel CI

The baseline and agent-track workflows run as **independent GitHub Actions workflows**:

| Workflow | File | Entry point | Triggered by |
|----------|------|-------------|--------------|
| Baseline | `ci.yml` | `review_paper.py` | All branches + manual |
| Agent track | `agent-review.yml` | `agent.py` (per track) | `agent-*` branches + manual |

The two workflows share no jobs and do not depend on each other.

**Jobs inside `agent-review.yml`:**

- **`test-infra`** — runs on every push to `agent-e2e`, `agent-linear`, `agent-reconstruct`; no API key required; infra smoke tests.
- **`agent-review`** — manual dispatch only (`workflow_dispatch`); requires `OPENAI_API_KEY`; runs the full review and publishes `report.md`.

### Triggering an agent review

1. Go to **Actions → Agent Track Review → Run workflow**
2. Fill `paper_url` (e.g. `https://arxiv.org/abs/2006.06138`)
3. Select `track`: `e2e` | `linear` | `reconstruct`
4. Optionally set `model` (default: `gpt-4o`)
5. Click **Run workflow**

The job checks out the `agent-<track>` branch, runs `agent.py`, uploads `report.md` as an artifact, and pushes it to the `agent-reports` branch under `agent-<track>/<paper_id>/report.md`.

### Reports namespace

| Source | Branch | Path |
|--------|--------|------|
| Baseline | `reports` | `<paper_id>/` |
| agent-e2e | `agent-reports` | `agent-e2e/<paper_id>/` |
| agent-linear | `agent-reports` | `agent-linear/<paper_id>/` |
| agent-reconstruct | `agent-reports` | `agent-reconstruct/<paper_id>/` |

### Freezing a snapshot

When a meaningful milestone is reached in any track:

```bash
cp agent.py agent_[track]_v[X]_[Y]_[Z].py   # adjacent frozen copy
# bump AGENT_IMPL_ID in agent.py
git commit -m "freeze: [track] v[X].[Y].[Z]"
git tag agent-[track]-v[X].[Y].[Z]
```

### Cherry-picking an infra improvement

```bash
git cherry-pick <infra-base-commit-hash>
# run track tests to verify
git commit -m "cherry-pick infra: [description] (infra-base@<hash>)"
```

---

## 7. Cross-track comparison protocol

Run all three tracks on the same benchmark paper and record results in a shared `COMPARISON_LOG.md` (maintained on `main`):

| paper_id | track | impl_id | verdict | confidence | notes |
|----------|-------|---------|---------|------------|-------|
| 2006.06138 | e2e | e2e_v1_0_0 | COMBINATION | 0.72 | … |
| 2006.06138 | linear | linear_v1_0_0 | COMBINATION | 0.81 | … |
| 2006.06138 | reconstruct | reconstruct_v1_0_0 | PARTIAL | 0.60 | … |

**Recommended benchmark set:**
- At least one clearly derivative paper (known combination of prior work)
- At least one clearly novel paper (well-cited breakthrough)
- At least one ambiguous paper (mixed signals; tests uncertainty handling)

**A track is winning if its derivation audits are:**
1. More accurate — fewer false NOVEL verdicts for derivative papers
2. More specific — derivation map traces to sections/algorithms, not just paper titles
3. Better calibrated — confidence correlates with actual correctness

This comparison loop is the primary feedback mechanism for evolving each track.
