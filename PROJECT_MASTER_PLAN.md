# Open-Idea-Sourcing — Project Master Plan

> A living architecture + roadmap document.
> Covers the scientific goal, what is already built, what is not,
> and a dual-track architecture — the **baseline mechanical track** (engineering
> correctness and ablation infrastructure) running in parallel with the
> **autonomous innovation track** (max LLM agency, minimal human intervention) —
> with precise guidance on when and why to bring in LangGraph, CrewAI, MCPs, and SDKs.

---

## Part 0 — The Scientific Goal (Not Just the SDE Goal)

### What the project is actually trying to do

This is not a plagiarism detector. It is not a citation recommender.
It is an **automated intellectual-property judge** — one that can answer:

> *"Is this paper genuinely new, or is it derivable — possibly with cosmetic
> re-framing — from a small pool of prior work I can name precisely?"*

The scientific formulation that captures this most cleanly is from Issue #48:

**Treat idea space as a metric space. Define a "distance" between papers
analogous to Wasserstein distance — where the cost of transporting one
paper's idea-mass onto another's measures intellectual derivability.**

- A **near-zero distance** means one paper is essentially a rewrite of the other.
- A **distance near 1** in every direction means the paper occupies genuinely new
  territory in idea-space.
- The **derivation certificate** is the transport plan: which component of A maps
  to which component of B, and what mass remains unmapped (= the novel residual).

### The forward / backward pass framing (Issue #48)

The ultimate evaluation has two dual directions:

| Direction | Process | Analogous to |
|-----------|---------|-------------|
| **Forward pass** | Build the submitted paper from scratch using only prior work as raw material | Supervised reconstruction |
| **Backward pass** | Start from a ground-truth full-credit answer and reduce until only the novel delta remains | Residual after projection |

A high-quality system should be able to meet in the middle — the forward
reconstruction and the backward reduction should converge on the same "novel
residual." Disagreement between the two is a signal of either bad decomposition
or incomplete retrieval.

### Theoretical Foundations (Theory Space)

> *Keep this corner alive as the unifying abstract framework. The concrete SDE
> work above and any parallel theoretical threads both map onto the same
> underlying object.*

The project sits inside a broader abstract structure worth naming precisely,
even if the full formalism is long-horizon:

- **Idea-space as a metric space** — papers are distributions over a concept space;
  "distance" between papers is the minimal transport cost to transform one into the other.
- **Novelty evaluation = error bounding** — how large is the residual after the
  best possible projection onto the span of prior work?
- **Retrieval quality = covering set completeness** — a derivation reasoner is only as
  good as the prior-work corpus it can see. An incomplete covering set always
  under-estimates the derivability of the submitted paper.

This framing unifies:
- The `DerivationCertificate` (the transport plan)
- The `Effort(n)` score per concept-tree node (the pointwise transport cost)
- The quality of the reference corpus (the support of the target measure)

This is why the pipeline bottleneck is fundamentally retrieval (Stage 3): if the
covering set is incomplete, even a perfect derivation reasoner will miss true priors.

### The concrete evaluation spec

For any submitted paper P with concept tree T, the system should produce:

```
DerivationCertificate:
  for each node n in T:
    Sources(n) = { REF-k : REF-k is the most plausible generator of n }
    Effort(n)  = distance from Sources(n) to n
                 (0 = trivial derivation; 1 = genuinely new)

  Novel(P) = { n in T : Effort(n) > threshold }
  Verdict  = f(|Novel(P)| / |T|, max_effort)
```

Every current component of the pipeline is an approximation of one step above.
The roadmap is about making each approximation more accurate and the whole
structure more rigorous.

---

## Part 1 — What Is Already Built (v2.4.0 Honest Inventory)

### Data types

| Type | Purpose | Quality |
|------|---------|---------|
| `ParsedPaper` | title, abstract, full_text, sections, authors | ✅ Good |
| `IdeaDecomposition` | core_concept + concept_tree (ConceptNode) | ⚠️ gpt-4o tends to be verbose/shallow; model matters |
| `ConceptNode` | recursive tree (label, children) | ✅ Good structure; depth is the variable |
| `SimilarityResult` | (paper_id, score, paper) from TF-IDF | ⚠️ TF-IDF is a proxy; misses semantic equivalence |
| `SimilarityAnnotation` | derivation_map + combination_analysis + novel_elements | ⚠️ 1-to-all; derivation_map not fed back into eval |
| `DomainReference` | key field references | ✅ Good for context; not yet used as evidence |
| `NoveltyDimension` | verdict + explanation + REF-N citations | ⚠️ Receives text refs, not structured derivation_map |
| `NoveltyReport` | full output | ✅ Good container; render layer is solid |
| `PipelineContext` | shared state bus | ✅ Good foundation; not yet checkpointable to disk |
| `RunMetadata` | provenance (commit, CI URL, timings) | ✅ Complete |

#### Swapping stage implementations and managing misaligned tests

When an entire stage implementation changes (e.g. swapping verbose multi-field
`IdeaDecomposition` for the current slim `core_concept+concept_tree` form), the
downstream data types change and existing tests break. The correct approach:

1. **Define the stage output as a protocol/interface, not a concrete class.**
   Both implementations satisfy the same interface; code depending on the stage
   output only imports the interface, not the concrete type.

2. **Keep both implementations registered in `REGISTRY` under different keys.**
   Config selects which runs: `stages.decompose.backend = "slim"` vs `"verbose"`.
   Tests for each backend live in `tests/agents/test_decompose_slim.py` etc.

3. **Tests should test the interface contract, not field-level details.**
   `assert decomp.core_concept` is a contract test. `assert decomp.sub_ideas` is
   a field test — only put it in the test file for the `verbose` backend.

4. **The golden test corpus carries the contract.**
   One integration test runs *both* backends on the same paper and asserts that
   the downstream verdict is still produced (not that fields match) — this is the
   cross-backend comparability check.

### Agents (what they actually do vs. what they should do)

| Agent | Actual behaviour | Gap vs. ideal |
|-------|-----------------|---------------|
| `PaperParser` (regex) | Extracts title/abstract/sections heuristically | Brittle on PDFs; often gets title wrong |
| `LLMPaperParser` | LLM extracts structured fields | ✅ Works; retries 3× |
| `DecompositionAgent` | LLM produces concept tree from abstract+full text | Model quality bottleneck: gpt-4o too surface-level |
| `LLMQueryGenerator` | LLM generates 4–6 search queries from decomp | Queries often too generic; needs iterative refinement |
| `OnlineReferenceSearch` | Semantic Scholar: arXiv refs + keyword search | Main pipeline bottleneck; no semantic search |
| `DomainRefFinder` | LLM identifies key field references by name | Returns titles, not papers; lookup often fails |
| `SimilaritySearch` (TF-IDF) | Cosine similarity on bag-of-words | Misses concept-level equivalences with no vocab overlap |
| `DuplicationChecker` | LLM verdict with accumulated context chain | Gets ref list as text; can't reason over `derivation_map` |
| `CombinationChecker` | LLM verdict + prior dup context | Same gap; combination analysis is redone, not imported |
| `EquivalenceChecker` | LLM verdict + prior dup+combo contexts | Correct chain; gap is evidence quality |
| `AnnotationAgent` | 1-to-all derivation_map over full ref pool | ✅ Good design; runs AFTER synthesis (wrong order) |
| `SynthesisAgent` | Final verdict from 3 dimensions | Does not receive `derivation_map` or `novel_elements` |
| `ReportGenerator` | Markdown/PDF/JSON/text | ✅ Solid |

### Infrastructure

| Feature | Status |
|---------|--------|
| `pipeline_config.yaml` + `--config` flag | ✅ |
| Stage 3 sub-stage toggle flags (`--no-online-search`, `--no-user-refs`, `--no-paper-cited-refs`) | ✅ |
| Reasoning model auto-detection | ✅ |
| HTTP retry with backoff | ✅ |
| CI: test + review + artifact + reports-branch | ✅ |
| `copilot-wakeup.yml` — automated Copilot resume after timeout | ✅ added (base branch) |
| `ReferenceStore` source priority dedup (user > paper-cited > online > domain) | ✅ added (base branch) |
| `ReferenceStore.get_all_sources()` — all source tags for a paper | ✅ added (base branch) |
| REF-N Reference Index in every report | ✅ added (base branch) |
| `PipelineContext` shared state bus | ✅ foundation only; no disk checkpoint |
| 533+ unit/integration tests | ✅ (1 flaky batch-naming test) |
| `configs/` named experiment baselines | ❌ not yet |
| Agent registry / `Pipeline` class | ❌ not yet |
| Disk-serialisable `PipelineContext` | ❌ not yet |

---

## Part 2 — Scientific Questions and Falsifiable Hypotheses

> Cross-reference Issue #50: the three ablation axes are (1) atomic model capability,
> (2) prompt design, (3) pipeline structure. Every open problem below lives on at
> least one of these axes, and the "experiment design" column identifies which axis
> it tests and what infra is needed.

The goal is to structure these as real scientific questions — not engineering tasks —
so that each improvement has a testable prediction that can be confirmed or refuted
on the golden test corpus.

---

### H1 — Annotation-evidence gap

**Hypothesis:** The dimension checks (duplication, combination, equivalence) produce
lower-quality verdicts when they receive only a flat reference list vs. when they
receive the structured `derivation_map` from the annotation agent.

**Prediction:** Passing `derivation_map` into the dimension prompts will increase
the fraction of verdicts that a human reviewer agrees with, on the test corpus.

**Experiment:**
- Baseline: current system (no derivation_map in dimension prompts)
- Treatment: system with `{derivation_map}` slot in all dimension prompts
- Metric: human reviewer agreement rate on 10 test papers
- Required infra: `DerivationEvidence` datatype; annotation runs before evaluation
- Config: `stages.evaluate.use_derivation_map = true/false`

**Current gap:** `AnnotationAgent` runs after `SynthesisAgent`. Fix: move it before.

---

### H2 — Retrieval coverage bottleneck

**Hypothesis:** The pipeline's novelty verdict is wrong primarily because the
correct prior work was never retrieved, not because the LLM reasoned incorrectly
over the retrieved set.

**Prediction:** When the gold-standard reference is injected directly (bypassing
retrieval), verdict accuracy jumps significantly even with the same weak LLM.

**Experiment:**
- Baseline: full pipeline on test corpus
- Oracle condition: inject known-correct reference at Stage 3; run rest of pipeline
- Metric: verdict agreement with human ground truth under each condition
- Required infra: `--inject-reference URL` CLI flag; no pipeline changes needed
- Config: `stages.retrieve.inject = [url1, url2]`

**Implication:** If oracle condition produces much better verdicts, the bottleneck
is retrieval quality (confirming H2). If not, the bottleneck is the reasoning quality.

---

### H3 — One-shot vs. iterative retrieval

**Hypothesis:** Iterative query refinement (generate → search → assess → refine →
repeat until coverage sufficient) retrieves more relevant prior work than a
single-shot keyword search.

**Prediction:** After N refinement iterations, cosine similarity between the
best-matched retrieved paper and the submitted paper is higher than single-shot.

**Experiment:**
- Baseline: current single-shot retrieval
- Treatment: LangGraph iterative retrieval loop (3 iterations max)
- Metric: max similarity score of retrieved set; fraction of gold references recovered
- Required infra: LangGraph `StateGraph`; `AssessCoverageNode` with an LLM judge
- Config: `stages.retrieve.backend = "iterative"`, `stages.retrieve.max_iterations = 3`

---

### H4 — Decomposition quality drives downstream quality

**Hypothesis:** The quality of the concept tree (Stage 2) is the primary driver of
annotation and verdict quality — more so than model size at Stage 5.

**Prediction:** A strong reasoning model at Stage 2 (o3/Claude Opus) with a weak
model at Stage 5 will outperform a weak Stage 2 model with a strong Stage 5 model.

**Experiment:**
- Condition A: `decomp_model=o3`, `eval_model=gpt-4o-mini`
- Condition B: `decomp_model=gpt-4o-mini`, `eval_model=o3`
- Condition C: `decomp_model=o3`, `eval_model=o3` (control)
- Metric: human verdict agreement; concept tree depth and coverage scores
- Required infra: `--decomposition-model` flag (already exists); `--model` flag (already exists)
- Config: all three configs checked in as `configs/exp-decomp-o3-eval-mini.yaml` etc.

---

### H5 — Prompt specificity and constraint intensity

**Hypothesis:** More specific, constrained prompts (e.g. "identify the exact
technical bottleneck, not the surface framing") produce better concept trees than
generic prompts, independently of model choice.

**Prediction:** For a fixed model (gpt-4o), replacing the `decomposition.txt`
prompt with a more constrained version will increase concept tree depth and
reduce vocabulary overlap with the abstract.

**Experiment:**
- Baseline: current `decomposition.txt`
- Treatment: stricter prompt that explicitly forbids paraphrasing the abstract
- Metric: concept tree depth; vocabulary overlap (abstract vs. tree text); human rating
- Required infra: `stages.decompose.prompt = "prompts/decomposition_strict.txt"` in config
- Config: `configs/exp-strict-decomp.yaml`

---

### H6 — TF-IDF vs. semantic retrieval

**Hypothesis:** Dense embedding retrieval finds more methodologically equivalent
papers than TF-IDF, especially when papers use different vocabulary for the same method.

**Prediction:** Dense retrieval recovers more of the gold references on the test corpus.

**Experiment:**
- Baseline: TF-IDF rank backend
- Treatment: Ada-002 embedding rank backend
- Metric: recall@10 on gold reference set; max similarity score
- Required infra: `DenseRetriever` in `agents/rank.py`; `stages.rank.backend = "dense"`
- Config: `configs/dense-retrieval.yaml`

---

### H7 — Caching policy (IID re-runs vs. within-pass cache)

**Preference (not a hypothesis):** Each pipeline run should be **independent and
identically distributed** (IID) — no caching across runs by default, so that
re-runs are valid independent samples for measuring variance.

**However:** Within a single iterative retrieval pass (H3), caching is essential —
previously fetched papers must not be re-fetched in loop iteration N+1.

**Implementation target:**
- A **consensus map** — a globally visible, editable dict mapping `(query, source)
  → list[paper_id]` — is maintained within each run and passed across loop iterations.
- The consensus map is serialised to `PipelineContext` and appears in every report
  (so you can see which queries were deduplicated).
- Cross-run caching is **opt-in** only (e.g. `--reuse-retrieval-cache`), never default.

---

### H8 — Automated quality gate accuracy

**Hypothesis:** An LLM-based report checker can classify reports as
`ACCEPTABLE / NEEDS_REVISION` with agreement comparable to a human reviewer.

**Prediction:** The checker's classification agrees with human labels ≥ 80% of the
time on a held-out set of 20 reports (10 acceptable, 10 needing revision).

**Experiment:**
- Baseline: human labels on 20 reports
- Treatment: `ReportCheckerAgent` classification on same reports
- Metric: agreement rate; false-positive and false-negative rates
- Required infra: `agents/check.py`; `prompts/report_check.txt` with scientific goals

---

## Part 3 — Architecture Tracks

The project has **two parallel build tracks**, not a single linear progression.
They run independently and are compared laterally:

| Track | Goal | Philosophy |
|-------|------|-----------|
| **Baseline / Mechanical** | Engineering correctness, modularity, ablation infra | Human-designed pipeline; every stage, prompt, and config explicitly specified by the researcher |
| **Autonomous Innovation** | Minimal human intervention; max LLM agency | LLM agents make most decisions themselves; human specifies the scientific goal, not the procedure |

The baseline track produces reproducible, ablatable results. The autonomous track
explores the outer bound of what the system can do when given maximum freedom.
**Both tracks are scientific instruments** — the comparison between their outputs is
itself a finding.

---

### Baseline Track — Clean sequential pipeline

**Driving question:** Is every stage correctly wired, independently testable, and
fully config-driven?

**What to build:**
- `Pipeline` class: wraps the stage sequence; `run()` + `run_from(stage_name)` for checkpointing
- `agents/` directory: one file per agent; pure functions with typed I/O
- `types.py`: all dataclasses in one place (single source of truth)
- `configs/` directory: named experiment baselines checked into git
- Fix annotation-before-evaluation (H1)
- LangGraph iterative retrieval subgraph (H3) — replaces one-shot search
- MCP tool servers — standardised tool layer callable by any agent

**Framework:** Plain Python for the linear stages; LangGraph for the retrieval loop only.

**What this achieves:**
- Every stage is independently unit-testable
- Swapping one agent (e.g., TF-IDF → dense retrieval) requires one line in config
- Re-running from Stage 5 after a prompt change takes seconds, not minutes
- Two runs are fully described by their `configs/` diff
- Experiments H1–H8 are all runnable via config

---

### Autonomous Innovation Track — Architecture Options

These are **lateral options to build and compare** — not sequential steps.
Each operationalises a different philosophy about how much agency to give LLMs.

#### Option A — Wasserstein Adversarial Reconstruction (operationalises the theory)

**Core idea:** The "Wasserstein distance" between papers is approximated through
an adversarial game, not a single forward pass.

```
[Student Agent]
  Given: only the submitted paper (no prior work)
  Task: reconstruct the paper's key claims from scratch using the fewest
        possible external references
  Constraint: must request references from the Resource Pool Agent;
              each reference has a "cost"

[Resource Pool Agent]
  Given: the full reference corpus
  Task: manage the pool of available references
        Start with nothing; release references when the Student requests them
        Try to find the minimal sufficient set (not just any set)

[Teacher / Evaluator Agent]
  Given: the original paper + Student's reconstruction
  Task: evaluate reconstruction quality at each round
        Decide whether to release a hint (reference), withhold, or terminate
        The game ends when quality meets threshold or budget is exhausted

Result: the "cost" of reconstruction ≈ derivability score
        What can't be reconstructed even with the full pool ≈ the novel residual
```

This is the most direct operationalisation of the Wasserstein formulation.
The game is simple (back-and-forth), autonomous (Student decides what to reconstruct;
Teacher decides what to release), and the output is interpretable.

**Why this is different from the debate architecture:**
- No human-defined evaluation rubric needed — the reconstruction quality is the metric
- The reference pool management is itself an agent's job, not a human pre-selection
- The "derivation certificate" falls out of the game log (what was used to reconstruct what)

**Framework:** LangGraph `StateGraph` with `StudentNode`, `ResourcePoolNode`, `TeacherNode`.

---

#### Option B — Multi-Agent Debate (operationalises multi-perspective cross-checking)

**Core idea:** Different agents approach the paper from different angles and must
reach consensus through structured argument.

```
Librarian Agent    → retrieves and ranks references (fast, cheap model)
Domain Expert      → builds concept tree; assesses derivation (reasoning model)
Adversarial Critic → challenges every derivation claim; demands evidence (reasoning model)
Judge Agent        → resolves debate into final certificate (reasoning model)
Reporter Agent     → renders certificate into human-readable report (fast model)
```

This is a proven pattern for improving reasoning quality on hard tasks.
The key difference from Option A: human pre-defines the roles and rubric; LLMs fill them.
The output quality depends on role design and prompt quality.

**Framework:** CrewAI for role assignment + inter-agent communication; LangGraph for state.

---

#### Option C — Hybrid (baseline wiring + autonomous components)

Run the baseline mechanical pipeline for all stages except retrieval and evaluation;
use the Wasserstein game loop only for retrieval (deciding which references to surface).

This is the most practical near-term step: the autonomous component handles the
hardest sub-problem (which references matter), while the rest remains reproducible.

---

**Build order:**
1. Baseline Track fully working (plain Python Pipeline class) — prerequisite
2. Option C: Wasserstein retrieval game as LangGraph subgraph
3. Option A: Full Wasserstein adversarial reconstruction
4. Option B: Full multi-agent debate
5. Ablation: compare Options A, B, C, and Baseline on same test corpus

---

## Part 4 — Framework Decision Guide

This clarifies the earlier "don't use LangGraph/CrewAI" guidance, which was
wrong for this project's ultimate trajectory.

### Use plain Python when:
- Building a **linear sequential pipeline** (Horizon 1)
- Still **designing the interface** between stages (changing code faster than a framework can keep up)
- **Unit testing individual stages** in isolation (no framework overhead)
- The pipeline has **no cycles or conditional routing**

### Use LangGraph when:
- A stage needs to **loop until a condition is met** (iterative retrieval, SP4)
- You need **conditional routing** between stages based on intermediate results
- You want to **checkpoint state to disk** and resume from any node
- The pipeline has **fan-out / fan-in** patterns (parallel retrieval sub-stages merging)

LangGraph is essentially: `Pipeline.run_from()` + conditional edges + built-in
state persistence. When your `Pipeline` class needs all three of those at once,
use LangGraph directly instead of reinventing it.

### Use CrewAI when:
- You have **multiple distinct agent roles** that interact (debate, critique, specialisation)
- Agents need **persistent memory** across tasks within a session
- The task benefits from **multi-agent adversarial dynamics** (Critic challenging Expert)
- You want a framework that handles **tool assignment per role** without custom plumbing

CrewAI is NOT appropriate when:
- The pipeline is sequential with no inter-agent interaction (Horizon 1 — use plain Python)
- The loop structure is purely a retrieval retry (Horizon 2 — use LangGraph)
- You are still designing the stage interfaces (framework locks you in prematurely)

### Use MCPs when:
- You want a **tool layer callable by any LLM** regardless of framework
- The same tool (e.g., Semantic Scholar search) is used by **multiple agents**
- You want tools to be **reusable across projects** (other corpora, forks)
- You want to hook into **Claude Desktop, Cursor, or other MCP-compatible clients**

MCPs are tool standardisation, not orchestration. Add them when the baseline
Pipeline class is stable and you want the tool layer to outlive any one framework.

### Use the OpenAI Agents SDK / Anthropic SDK when:
- You are building a **single-agent with tools** (simpler than CrewAI for one agent)
- You want **native streaming + tracing** without custom logging
- Your agents are homogeneous (all GPT-4 or all Claude) with no cross-provider mixing

The OpenAI Agents SDK is essentially CrewAI minus the role abstraction.
Use it when you have one agent with many tools; use CrewAI when you have many agents
with distinct roles and inter-agent communication.

### Evolution path for this project

```
Baseline Track:
  plain Python Pipeline class        ← build first; no framework
  + LangGraph retrieval subgraph     ← add when iterative loops needed
  + MCP tool servers                 ← add when multi-agent tool sharing needed

Autonomous Innovation Track (lateral options to compare):
  Option A: LangGraph Wasserstein adversarial game   ← operationalises the theory
  Option B: CrewAI multi-agent debate                ← operationalises multi-perspective checking
  Option C: Hybrid (baseline + autonomous retrieval) ← most practical near-term
```

The Baseline Track is load-bearing — each autonomous option calls into it for the
stages it does not replace. Build the baseline first.

---

## Part 5 — Immediate Build Sequence

Each item is one Copilot session (< 45 min). Each has a clear done-state.
Phases A–C are baseline track. Phase D begins the autonomous track.

### Phase A — Fix the scientific correctness gaps (highest impact, no refactoring needed)

| # | Change | Done-state | Tests hypothesis |
|---|--------|-----------|-----------------|
| A1 | Move `AnnotationAgent` to run before dimension checks | Pipeline log shows annotation before duplication | H1 infra |
| A2 | Add `{derivation_map}` slot to `duplication.txt`, `combination.txt`, `equivalence.txt` | Each dimension prompt receives structured evidence | H1 |
| A3 | Pass `novel_elements` from `SimilarityAnnotation` into synthesis prompt | Synthesis explicitly addresses what is claimed novel | H1 |
| A4 | Add `DerivationCertificate` dataclass; populate from synthesis output | JSON report contains `certificate` field | H1 complete |

### Phase B — Stabilise and modularise (enables everything else)

| # | Change | Done-state | Tests hypothesis |
|---|--------|-----------|-----------------|
| B1 | Move all dataclasses to `types.py` | Every module imports from `open_idea_sourcing.types` | Prerequisite for all |
| B2 | Extract `Pipeline` class with `run()` + `run_from(stage_name)` | `review_paper.py` is ≤ 100 lines | H4/H5 ablation |
| B3 | Move each agent to `agents/` directory | `from open_idea_sourcing.agents.rank import TFIDFRanker` works | H6 prerequisite |
| B4 | Add `configs/` directory with `baseline.yaml`, `offline.yaml`, `no-chain.yaml` | `--config configs/offline.yaml` works; configs are checked in | All experiments |

### Phase C — Quality gate and dense retrieval

| # | Change | Done-state | Tests hypothesis |
|---|--------|-----------|-----------------|
| C1 | Add `prompts/report_check.txt` + `agents/check.py` | `check_quality(report, llm)` returns `ACCEPTABLE/NEEDS_REVISION` | H8 |
| C2 | Add CI `check-quality` job | CI fails on `NEEDS_REVISION`; check result in artifact | H8 infra |
| C3 | Add `--inject-reference` CLI flag | Known gold ref injected; pipeline runs | H2 experiment |
| C4 | Add `DenseRetriever` to `agents/rank.py` + `configs/dense-retrieval.yaml` | Config swap runs end-to-end | H6 |

### Phase D — LangGraph iterative retrieval (Baseline Track completion)

| # | Change | Done-state | Tests hypothesis |
|---|--------|-----------|-----------------|
| D1 | Design retrieval graph nodes as standalone functions | Each node passes unit tests | H3 infra |
| D2 | Wire into a LangGraph `StateGraph` with consensus map | Graph runs end-to-end with loop exit | H3 |
| D3 | Add `configs/iterative-retrieval.yaml`; run ablation vs. single-shot | Quantified recall improvement | H3 confirmed/rejected |

### Phase E — MCP tool layer

| # | Change | Done-state | Tests hypothesis |
|---|--------|-----------|-----------------|
| E1 | Implement `semantic-scholar-mcp` server | Claude Desktop can call `search(query)` | Tool layer |
| E2 | Implement `reference-store-mcp` server | Any LLM can add/query the reference store | Tool layer |
| E3 | Implement `concept-tree-mcp` server | Any LLM can extract or diff concept trees | Tool layer |

### Phase F — Autonomous innovation track

| # | Change | Done-state | Tests hypothesis |
|---|--------|-----------|-----------------|
| F1 | Implement Option C: Wasserstein retrieval game as LangGraph subgraph | Game log appears in report; reconstruction quality tracked | H3 + theory |
| F2 | Implement Option B: CrewAI multi-agent debate | `crew.kickoff(paper)` returns a `NoveltyReport` | Multi-agent |
| F3 | Ablation: Baseline vs. Option A vs. Option B vs. Option C on test corpus | Quantified quality comparison across all tracks | Cross-track comparison |

---

## Part 6 — What Stays Constant Across All Horizons

These do not change regardless of which framework or horizon you are in:

| Invariant | Why it must not change |
|-----------|----------------------|
| `(prompt: str) -> str` LLM callable interface | Every agent, every framework, every model uses this |
| `prompts/*.txt` as the scientific design artefacts | Changing a prompt is changing the scientific hypothesis |
| `PipelineContext` as the state container | Every framework can serialize/deserialize this |
| Typed dataclasses with no side effects | Unit testable at any horizon |
| Provenance in every report (git commit, config, model) | Non-negotiable for scientific reproducibility |

---

## Part 7 — Portability Target

When this pipeline is ready to apply to a new domain (architecture proposal evaluation,
survey completeness checking, grant proposal novelty assessment):

| What to replace | What to keep |
|-----------------|-------------|
| `prompts/*.txt` | All agent code |
| `data/references.json` | `Pipeline` class + all infrastructure |
| `configs/baseline.yaml` | All frameworks (LangGraph, CrewAI, MCPs) |
| `prompts/report_check.txt` | CI workflows |
| `data/test_papers.ndjson` | `review_paper.py` CLI |

Five file changes, zero code changes. That is the portability target.
The framework investment in the Autonomous Innovation Track pays off most here:
the same LangGraph graph, same CrewAI crew, same MCP tool servers — just different
prompts, a different corpus, and a different goals file for the quality checker.
