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
| `infra/tool_registry.py` | Thin registry mapping tool names to callable wrappers; records which tools were invoked per run. |
| `infra/search_tools.py` | Semantic Scholar thin client + arXiv thin client. No LLM logic; pure I/O. |
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

### Methodology

```
[Input]  paper URL or local PDF
    │
    ▼
[Agent loop]
    The agent is given the paper text and a tool set.
    It autonomously decides:
      - which searches to run (S2 keyword, arXiv citation, domain concept)
      - how many comparison rounds to perform
      - when it has enough evidence to produce a verdict
    No external orchestrator imposes stage order.
    │
    ▼
[Output]  report.md
    Contains: derivation audit, derivation map, residual novelty verdict
```

### Tool set (cherry-picked from infra-base)

- `search_semantic_scholar(query)` — keyword + citation search
- `search_arxiv(query)` — arXiv abstract search
- `fetch_paper_text(url_or_path)` — PDF/HTML ingestion
- `record_tool_call(name, args, result)` — audit trail

### Build sequence

```
Step 1  cherry-pick infra/ from infra-base
Step 2  agent.py v1 — basic tool-using loop, 3-5 search calls, single verdict
Step 3  report.md template — YAML front matter + required sections
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
         Sources: S2 keyword, S2 citation list, arXiv, domain concept lookup
         Rule:   each source independently toggleable; dedup by paper_id

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

## 5. agent-reconstruct — reconstruction and discovery track

### Scientific purpose

This is the **real discovery track**. It drops the fixed stage ordering and instead
lets the agent dynamically choose its reconstruction strategy — branching hypotheses,
running debate rounds between sub-agents, or iteratively deepening its search on the
highest-impact derivation paths.

The goal is to find the best possible answer to: *"What is the irreducible residual
contribution of this paper?"* — not to produce a clean audit trail (that is
`agent-linear`'s job).

### Design principles

- No fixed stage sequence; agent plans its own search strategy
- Multiple reconstruction hypotheses may be explored in parallel
- Sub-agents can debate or challenge each other's derivation claims
- The final report may expose the reconstruction process itself (showing which
  hypotheses were explored and why some were abandoned)
- Aggressive evolution is expected; frozen snapshots preserve milestones

### Reconstruction strategy options

The agent may employ any combination of:

| Strategy | Description |
|----------|-------------|
| **Bottom-up decomposition** | Start from atomic technical claims and search for sources of each |
| **Top-down elimination** | Start from the claimed contribution and progressively show it is derivable |
| **Hypothesis branching** | Maintain multiple derivation hypotheses; evaluate each with evidence |
| **Adversarial challenge** | One sub-agent argues novelty, another argues derivability; synthesise |
| **Iterative deepening** | First pass identifies high-signal components; second pass deep-dives them |
| **Domain anchor search** | Anchor on domain-specific technical vocabulary to find conceptually equivalent prior work |

### Debate sub-agent structure (optional, v2+)

```
Reconstructor agent      — builds derivation hypotheses
    │
    ├─ calls ─► SearchAgent     — retrieves candidate prior-work evidence
    ├─ calls ─► ChallengerAgent — challenges each derivation claim
    └─ calls ─► JudgeAgent      — weighs competing claims, produces verdict
```

This is not a fixed architecture. It may evolve, be replaced, or be abandoned
based on what actually produces better derivation audits.

### Build sequence

```
Step 1  cherry-pick infra/ from infra-base
Step 2  agent.py v1 — single-agent reconstruction loop (no debate)
        Focus: better decomposition of technical units than agent-e2e/linear
Step 3  prompts/reconstruct.txt — reconstruction-specific prompt
Step 4  Freeze: agent_reconstruct_v1_0_0.py
Step 5  agent.py v2 — hypothesis branching; multiple derivation paths explored
Step 6  agent.py v3 — debate sub-agents (if v2 shows promising signal)
Step 7  Git tag at each meaningful milestone
```

### File layout

```
agent-reconstruct branch
├── agent.py                           ← active implementation
├── agent_reconstruct_v1_0_0.py        ← frozen snapshot
├── hypotheses/                        ← runtime; gitignored
├── prompts/
│   ├── system.txt
│   ├── reconstruct.txt
│   ├── challenger.txt                 ← added in v3
│   └── judge.txt                      ← added in v3
├── infra/                             ← cherry-picked from infra-base
└── README.md
```

### Evolution philosophy

This track is allowed to **fail loudly**. If a sub-agent structure does not
produce better derivation audits than `agent-linear`, that is a useful finding.
Freeze the failed snapshot, document the finding in a `FINDINGS.md`, and try a
different approach. Do not delete failed experiments — they are data.

---

## 6. Human workflow

### Triggering a run (all tracks)

Runs are triggered via GitHub Actions, same as the programmatic pipeline.

1. Go to **Actions → [track name] → Run workflow**
2. Fill in `paper_url` (arXiv abstract URL or direct PDF)
3. Select `model` (default: as configured per track)
4. Click **Run workflow**

The CI job will:
- Run `agent.py` with the provided paper
- Upload `report.md` as a CI artifact
- Push `report.md` to the `reports` branch under `reports/[track]/[paper_id]/report.md`

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

1. Find the three `report.md` files under `reports/[track]/[paper_id]/`
2. Compare `final_verdict` and `confidence` in YAML front matter
3. Compare `derivation_map` sections for agreement and disagreement
4. Compare `residual_novelty` for depth and specificity

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
