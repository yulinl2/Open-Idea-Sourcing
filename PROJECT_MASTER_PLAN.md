# Open-Idea-Sourcing — Project Master Plan

> A living architecture + roadmap document.
> Covers the scientific goal, what is already built, what is not,
> and a three-horizon architecture from today's mechanical baseline
> to the ultimate multi-agent form — with precise guidance on when
> and why to bring in LangGraph, CrewAI, MCPs, and SDKs.

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

### The HAN theory connection

The parallel theoretical thread (Issue #48 meeting notes) frames this as:

> Post as a statistical error-bounding problem against *some target logical
> function* over some *abstract concept space* with basic distance metrics.

This means:
- Idea-space = an abstract concept space with a distance metric
- Novelty evaluation = estimating the error of the "is this derivable?" classifier
- Retrieval quality = completeness of the covering set for the relevant region

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
| Stage 3 sub-stage toggle flags | ✅ |
| Reasoning model auto-detection | ✅ |
| HTTP retry with backoff | ✅ |
| CI: test + review + artifact + reports-branch | ✅ |
| `PipelineContext` shared state bus | ✅ foundation only; no disk checkpoint |
| 533 unit/integration tests | ✅ (1 flaky batch-naming test) |
| `configs/` named experiment baselines | ❌ not yet |
| Agent registry / `Pipeline` class | ❌ not yet |
| Disk-serialisable `PipelineContext` | ❌ not yet |

---

## Part 2 — Open Problems (Ordered by Scientific Impact)

### SP1 — Annotation before evaluation (Stage ordering bug)
`AnnotationAgent` runs *after* `SynthesisAgent`. The dimension checks therefore
never receive the `derivation_map`. This is the biggest correctness gap.
**Fix: run Stage 5 (Annotate) before Stage 6 (Evaluate).**

### SP2 — Derivation map is disconnected from verdict logic
The `derivation_map` in `SimilarityAnnotation` is the closest thing we have to the
derivation certificate, but it is rendered in the report and then discarded. The
dimension prompts receive only a flat REF-N reference list. The verdict can say
"HIGH duplication" without citing a specific concept-tree node.
**Fix: pass `DerivationEvidence` as structured input into each dimension prompt.**

### SP3 — TF-IDF cannot find semantic equivalence
Score 0.40 over a known-identical reference vs. <0.30 over 10 searched refs
(Issue #48 empirical data) shows TF-IDF works when the right ref is present but
cannot surface it from a cold corpus. The system needs a semantic similarity
channel — either dense embeddings or an LLM-based ranker that can match
"weighted conformal prediction" to "distribution-free uncertainty quantification."
**Fix: add dense retrieval as an optional rank backend.**

### SP4 — Retrieval is one-shot, not iterative
The current query → search → done flow cannot refine when results are sparse
or off-topic. The ideal loop is:
```
generate queries → search → assess coverage → if insufficient → refine queries → search again
```
This is a **cycle**, not a pipeline step. Plain Python cannot express this
naturally; this is the first place where a graph execution framework (LangGraph)
earns its keep.

### SP5 — Decomposition quality is model-dependent and not verified
gpt-4o produces verbose, surface-level trees. The tree drives everything
downstream. There is no step that validates whether the tree correctly identifies
the *real technical bottleneck* vs. the surface framing.
**Fix: add a decomposition critic pass (or use a reasoning model specifically for this).**

### SP6 — No caching of expensive operations
Every re-run re-calls all LLMs and re-fetches all online papers, even when the
paper content has not changed. For iterative development (tune prompt → re-run →
compare), this wastes ~80% of wall time and API cost.
**Fix: content-hash caching for LLM calls and HTTP responses.**

### SP7 — No automated quality gate
Report quality validation is currently human-only. There is no automated check
that the report meets the scientific goals.

### SP8 — No `configs/` experiment baseline directory
Cannot reproduce a specific experimental configuration without reconstructing
CLI flags from memory.

---

## Part 3 — Three-Horizon Architecture

The system should evolve through three distinct horizons. Each horizon is a
prerequisite for the next. **Do not skip ahead — the intermediate architecture
is load-bearing, not just scaffolding.**

---

### Horizon 1 — Clean sequential pipeline (now → ~1 month)

**Driving question:** Is every stage correctly wired and independently testable?

**What to build:**
- `Pipeline` class: wraps the stage sequence; `run()` + `run_from(stage_name)` for checkpointing
- `agents/` directory: one file per agent; pure functions with typed I/O
- `types.py`: all dataclasses in one place (single source of truth)
- `configs/` directory: named experiment baselines checked into git
- Fix SP1 (annotation order) and SP2 (derivation map in eval prompts)
- Add content-hash caching (SP6)

**Framework:** Plain Python. No orchestration framework needed.
The linear stage sequence with `PipelineContext` is sufficient.
Adding LangGraph here would be premature and would slow iteration.

**What this horizon achieves:**
- Every stage is independently unit-testable
- Swapping one agent (e.g., TF-IDF → dense retrieval) requires changing one line in config
- Re-running from Stage 5 after a prompt change takes seconds, not minutes
- Two runs are fully described by their `configs/` diff

---

### Horizon 2 — Iterative loops + tool ecosystem (1–3 months)

**Driving question:** Can the system refine its own understanding through cycles?

**What to build:**

**LangGraph for iterative retrieval (SP4):**

```
[DecomposeNode] → [GenerateQueriesNode] → [SearchNode]
                         ↑                      ↓
                  [RefineQueriesNode] ←  [AssessCoverageNode]
                                              ↓ (sufficient)
                                       [RankNode] → ...
```

LangGraph is the right tool here because:
- The retrieval loop has **conditional exit** (exit when coverage is sufficient)
- State accumulates across iterations (previously-found refs, previous queries)
- Each node is a pure function; the graph is the orchestration — this is exactly
  LangGraph's model

**MCP tool servers:**
Expose the core retrieval capabilities as [Model Context Protocol](https://modelcontextprotocol.io/) servers so any LLM agent (Claude, GPT-4, local) can call them:

```
MCP servers to build:
  semantic-scholar-mcp    → search(query), get_paper(id), get_references(id)
  arxiv-mcp               → fetch_paper(url), get_abstract(id)
  reference-store-mcp     → add(paper), search(query, threshold), get_source(id)
  concept-tree-mcp        → extract(paper_text), validate(tree), diff(tree_a, tree_b)
```

Benefits:
- Any agent in the system can call these tools without knowing their implementation
- Claude Desktop / GPT-4 function calling can use the same tool layer
- The tool layer becomes reusable across other projects (e.g., HAN theory corpus search)
- Decouples tool implementation from agent orchestration

**Dense retrieval (SP3):**
Add `DenseRetriever` as a swappable rank backend using OpenAI Ada-002 embeddings
or a BGE model. Config-driven: `stages.rank.backend = "dense"`.

**Decomposition critic (SP5):**
Add a second LLM pass that critiques the concept tree: "Does this tree identify
the *real* technical bottleneck, or is it paraphrasing the abstract?" — using a
stronger or different model (o3, Claude Opus).

**What this horizon achieves:**
- Retrieval quality improves through iteration (biggest quality bottleneck addressed)
- Any LLM can plug into the tool layer via MCP
- Decomposition quality is validated, not just generated
- LangGraph graph is the config-addressable equivalent of the current `_review_one()` function

---

### Horizon 3 — Multi-agent debate network (3–6 months)

**Driving question:** Can a network of specialized agents produce verdicts that
are more reliable than any single agent?

**The architecture:**

```
                    ┌─────────────────────────────┐
                    │     Orchestrator Agent       │
                    │  (CrewAI / LangGraph router) │
                    └───┬─────────┬─────────┬──────┘
                        │         │         │
              ┌─────────▼─┐  ┌────▼──────┐  ┌─▼──────────────┐
              │ Librarian │  │  Domain   │  │    Critic      │
              │  Agent    │  │  Expert   │  │    Agent       │
              │           │  │  Agent    │  │                │
              │ Retrieves │  │ Evaluates │  │ Challenges     │
              │ & ranks   │  │ derivation│  │ verdicts;      │
              │ references│  │ & novelty │  │ requests more  │
              └─────────┬─┘  └────┬──────┘  └─┬──────────────┘
                        │         │             │
                        └────┬────┘             │
                             ▼                  │
                    ┌────────────────┐           │
                    │ Judge Agent   │ ◄──────────┘
                    │               │
                    │ Final verdict │
                    │ + certificate │
                    └───────────────┘
```

**Why CrewAI here:**
- The multi-agent debate pattern maps naturally to CrewAI's **role-based task assignment**
- Each agent has a distinct *role*, *goal*, and *backstory* that shapes its LLM behaviour
- CrewAI's built-in memory, tool assignment, and inter-agent communication handles the
  coordination logic so you can focus on the scientific roles, not the plumbing
- The `Critic Agent` challenging the `Domain Expert Agent`'s verdict is exactly the
  "multi-agent debate improves accuracy" pattern that research has shown works for
  hard reasoning tasks

**Agent roles:**

| Agent | Role | Primary tool(s) | LLM recommendation |
|-------|------|-----------------|-------------------|
| **Librarian** | Retrieve and rank references exhaustively | `semantic-scholar-mcp`, `reference-store-mcp` | Fast/cheap (GPT-4o-mini) |
| **Domain Expert** | Build the concept tree; assess derivation | `concept-tree-mcp`, full paper text | Reasoning (o3, Claude Opus) |
| **Critic** | Challenge derivation claims; request more evidence | All MCP tools | Reasoning (o3) |
| **Judge** | Synthesise debate → final certificate | None (reasoning only) | Reasoning (o3) |
| **Reporter** | Render the certificate into a human-readable report | None (generation only) | Fast (GPT-4o) |

**What this horizon achieves:**
- The forward/backward pass design from Issue #48 is implementable:
  - Domain Expert does the forward pass (build from prior work)
  - Critic does the backward pass (reduce from ground truth)
  - Judge reconciles the two
- Multi-agent debate on hard cases improves verdict quality beyond single-agent
- The Wasserstein distance intuition becomes operational: each agent's transport
  plan is a component of the overall derivation certificate

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
- You want tools to be **reusable across projects** (HAN theory corpus, OpenNovelty fork)
- You want to hook into **Claude Desktop, Cursor, or other MCP-compatible clients**

MCPs are tool standardisation, not orchestration. Use them from Horizon 2 onwards
as the "instrument panel" that all agents plug into.

### Use the OpenAI Agents SDK / Anthropic SDK when:
- You are building a **single-agent with tools** (simpler than CrewAI for one agent)
- You want **native streaming + tracing** without custom logging
- Your agents are homogeneous (all GPT-4 or all Claude) with no cross-provider mixing

The OpenAI Agents SDK is essentially CrewAI minus the role abstraction.
Use it when you have one agent with many tools; use CrewAI when you have many agents
with distinct roles and inter-agent communication.

### Evolution path for this project

```
Horizon 1:  plain Python Pipeline class        ← build this first; no framework
Horizon 2:  LangGraph retrieval subgraph       ← add when iterative loops needed
            + MCP tool servers                 ← add alongside LangGraph
Horizon 3:  CrewAI multi-agent debate          ← add when multi-role interaction needed
            on top of LangGraph infrastructure ← LangGraph handles state; CrewAI handles roles
```

Do NOT skip Horizon 1. The `Pipeline` class from Horizon 1 becomes the
"inner loop" that each CrewAI agent calls in Horizon 3. Building Horizon 3
without Horizon 1 means each agent is calling the same 500-line monolith.

---

## Part 5 — Immediate Build Sequence

Each item is one Copilot session (< 45 min). Each has a clear done-state.

### Phase A — Fix the scientific correctness gaps (highest impact, no refactoring needed)

| # | Change | Done-state | Fixes |
|---|--------|-----------|-------|
| A1 | Move `AnnotationAgent` to run before dimension checks | Pipeline log shows annotation before duplication | SP1 |
| A2 | Add `{derivation_map}` slot to `duplication.txt`, `combination.txt`, `equivalence.txt` | Each dimension prompt receives structured evidence | SP2 |
| A3 | Pass `novel_elements` from `SimilarityAnnotation` into synthesis prompt | Synthesis explicitly addresses what is claimed novel | SP2 |
| A4 | Add `DerivationCertificate` dataclass; populate from synthesis output | JSON report contains `certificate` field | SP2 complete |

### Phase B — Stabilise and modularise (enables everything else)

| # | Change | Done-state | Fixes |
|---|--------|-----------|-------|
| B1 | Move all dataclasses to `types.py` | Every module imports from `open_idea_sourcing.types` | Prerequisite for C* |
| B2 | Extract `Pipeline` class with `run()` + `run_from(stage_name)` | `review_paper.py` is ≤ 100 lines | SP6 unlock, H2 prerequisite |
| B3 | Move each agent to `agents/` directory | `from open_idea_sourcing.agents.rank import TFIDFRanker` works | Enables SP3 |
| B4 | Add `configs/` directory with `baseline.yaml`, `offline.yaml`, `no-chain.yaml` | `--config configs/offline.yaml` works; configs are checked in | SP8 |
| B5 | Content-hash LLM/HTTP cache using `functools.lru_cache` or `diskcache` | Re-running same paper skips all API calls | SP6 |

### Phase C — Quality gate and dense retrieval (science unlocks)

| # | Change | Done-state | Fixes |
|---|--------|-----------|-------|
| C1 | Add `prompts/report_check.txt` + `agents/check.py` | `check_quality(report, llm)` returns `ACCEPTABLE/NEEDS_REVISION` | SP7 |
| C2 | Add CI `check-quality` job | CI fails on `NEEDS_REVISION`; check result in artifact | SP7 complete |
| C3 | Add `DenseRetriever` stub to `agents/rank.py` | `--config configs/dense-retrieval.yaml` runs (via stub) | SP3 prerequisite |
| C4 | Implement Ada-002 dense retrieval | Config `stages.rank.backend = "dense"` produces real results | SP3 |

### Phase D — LangGraph iterative retrieval (Horizon 2)

| # | Change | Done-state | Fixes |
|---|--------|-----------|-------|
| D1 | Design retrieval graph nodes as standalone functions | Each node passes unit tests | SP4 prerequisite |
| D2 | Wire nodes into a LangGraph `StateGraph` | Graph runs end-to-end with loop exit | SP4 |
| D3 | Replace `retrieve()` stage in `Pipeline` with LangGraph subgraph | Full pipeline runs; retrieval is now iterative | SP4 complete |

### Phase E — MCP tool layer (Horizon 2)

| # | Change | Done-state | Fixes |
|---|--------|-----------|-------|
| E1 | Implement `semantic-scholar-mcp` server | Claude Desktop can call `search(query)` | Tool layer |
| E2 | Implement `reference-store-mcp` server | Any LLM can add/query the reference store | Tool layer |
| E3 | Implement `concept-tree-mcp` server | Any LLM can extract or diff concept trees | Tool layer |

### Phase F — Multi-agent debate (Horizon 3)

| # | Change | Done-state | Fixes |
|---|--------|-----------|-------|
| F1 | Define CrewAI crew with Librarian + Domain Expert + Critic + Judge + Reporter roles | `crew.kickoff(paper)` returns a `NoveltyReport` | H3 |
| F2 | Connect each agent to the appropriate MCP tools | Librarian calls `semantic-scholar-mcp`; Expert calls `concept-tree-mcp` | H3 |
| F3 | Implement forward/backward pass in Domain Expert + Critic | Agent produces explicit transport plan | Wasserstein formulation |
| F4 | Ablation: single-agent (Horizon 1 pipeline) vs. multi-agent debate on same test corpus | Quantified quality comparison | Proof of value |

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

When this pipeline is ready to apply to a new domain (HAN theory paper review,
architecture proposal evaluation, survey completeness check):

| What to replace | What to keep |
|-----------------|-------------|
| `prompts/*.txt` | All agent code |
| `data/references.json` | `Pipeline` class + all infrastructure |
| `configs/baseline.yaml` | All frameworks (LangGraph, CrewAI, MCPs) |
| `prompts/report_check.txt` | CI workflows |
| `data/test_papers.ndjson` | `review_paper.py` CLI |

Five file changes, zero code changes. That is the portability target.
The framework investment in Horizons 2–3 pays off most here: the same
LangGraph graph, same CrewAI crew, same MCP tool servers — just different
prompts and a different corpus.
