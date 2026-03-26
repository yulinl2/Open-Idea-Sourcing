# Multi-Agent Research Pipeline — Dev Strategy Guide

A strategic reference for building modular, ablation-friendly, automatable multi-agent research systems. Written as a reflection on the v2 workflow and a prescription for the next phase.

---

## The Core Insight: Two Orthogonal Axes of Growth

Most research pipelines collapse two very different concerns into the same commit:

| Axis | Question | Changes When |
|------|----------|--------------|
| **Workflow dev** | *Is the pipeline correctly wired?* | Architecture, module boundaries, config schema, agent interfaces |
| **Performance tuning** | *Are the right choices being made?* | Prompts, models, thresholds, retrieval strategies |

**DO:** Treat these as separate PRs, separate branches, separate issues.  
**DON'T:** Tune prompts in the same commit that rewires the pipeline. You lose the ability to attribute a result change to either cause.

The moment they entangle — as in PR #49 — intermediate versions cease to be meaningful comparison points. Config-driven ablation is the remedy.

---

## Part 1 — Config-Driven Ablation Design

### The Goal

Every parameter and algorithmic choice should be swappable through `pipeline_config.yaml` — with zero code changes — so that any two runs are fully described by their config file diff.

### The Hierarchy

```
pipeline_config.yaml          ← baseline defaults (checked in)
  └── CLI flags                ← per-run overrides (logged in report)
        └── env vars           ← CI/secrets overrides (never in code)
              └── hardcoded    ← never (ban this)
```

**Rule:** If you find yourself editing a constant in source to try a variant, that constant belongs in the config.

### What Belongs in the Config (and Doesn't Yet)

Today `pipeline_config.yaml` covers model names, similarity thresholds, and toggle flags. The next layer:

```yaml
# pipeline_config.yaml — next-phase additions

stages:
  parse:
    backend: llm          # llm | regex | hybrid
  decompose:
    model: gpt-4o         # independent model slot
    depth: auto           # auto | 2 | 3 | 4
  retrieve:
    sources:
      bundled: true
      paper_cited: true
      online: true
      domain: true
    max_results_per_source: 20
    since_year: null
  evaluate:
    dimensions: [duplication, combination, equivalence]   # reorder or drop
    chain_prior_context: true   # accumulated-context chain (v2.3 behaviour)
    model: gpt-4o
  annotate:
    enabled: true
    model: gpt-4o

prompts:
  decomposition: prompts/decomposition.txt    # swap prompt file, not code
  duplication:   prompts/duplication.txt
  combination:   prompts/combination.txt
  equivalence:   prompts/equivalence.txt
```

This way an ablation study looks like:

```bash
# Variant A — full pipeline
python review_paper.py paper.pdf --config configs/full.yaml

# Variant B — no accumulated context chain
python review_paper.py paper.pdf --config configs/no_chain.yaml

# Variant C — regex parser only
python review_paper.py paper.pdf --config configs/regex_parse.yaml
```

Each config file is a git-tracked artifact. The report already embeds `git_commit` and config; adding `config_file` to `RunMetadata` closes the provenance loop completely.

### Versioning the Config, Not Just the Code

**DO:** Tag a config file alongside a code version when you freeze a known-good combination.  
**DO:** Store a `configs/` directory of named ablation configs alongside the code.  
**DON'T:** Change `pipeline_config.yaml` defaults without a corresponding CHANGELOG entry — those defaults are the implicit v-N baseline.

---

## Part 2 — Automating Copilot Session Continuity (Q1.1)

### The Problem

Copilot coding agent sessions time out after ~1 hour of inactivity. The human workflow devolves to:

```
wait 1h → notice timeout → type "↑ @copilot 👀 Keep on going" → repeat
```

### Why Full Automation Is the Wrong Frame

The timeout exists because Copilot is making *decisions* — not just executing deterministic steps. A session that ran for an hour before timing out has already diverged in ways that need human review before continuing. Blindly auto-resuming carries the same risk as auto-merging: you get progress, but you lose visibility.

**The better frame: shrink the unit of work so it fits in one session.**

### Strategies

#### 1. Atomic issue decomposition (highest leverage)

Break issues into single-session tasks: one PR per logical change, each completable in < 45 minutes of agent work.

```
BAD:  "Build v2 pipeline with online search, config system, and better prompts"
GOOD: 
  - "Add pipeline_config.yaml and --config flag" (45 min)
  - "Wired --no-bundled-refs and --no-paper-cited-refs toggle flags" (30 min)
  - "Accumulated context chain in dimension checks" (30 min)
```

Each issue has a clear done-state the agent can verify by running tests. The agent stops naturally when done rather than timing out mid-task.

#### 2. Checkpoint-and-resume via `report_progress`

The `report_progress` tool already commits work incrementally. Structure agent instructions so each logical unit ends with `report_progress`. Then a resume prompt is cheap:

```
@copilot The previous session timed out after completing steps 1-3.
Steps 4-6 remain (see checklist in PR description). Please continue.
```

This is the "keep going" button — but now it's meaningful context, not a blind retry.

#### 3. GitHub Actions retry for flaky CI (the actual automation target)

The genuine automation opportunity is not retrying Copilot sessions — it's retrying *CI jobs* that fail due to transient API errors (Semantic Scholar 429, OpenAI timeout):

```yaml
# In ci.yml — add to the review job steps:
- name: Review paper(s) with retry
  uses: nick-fields/retry@v3
  with:
    timeout_minutes: 15
    max_attempts: 3
    retry_on: error
    command: python review_paper.py ...
```

The pipeline already has `_http_get()` retry logic for HTTP 429. The CI wrapper adds an outer retry for full-step failures (network timeout, LLM rate limit mid-run).

#### 4. Scheduled re-run of failed CI

For the case where a run fails and no human is watching:

```yaml
# .github/workflows/retry-failed.yml
on:
  schedule:
    - cron: '0 */2 * * *'   # every 2 hours

jobs:
  retry-failed:
    runs-on: ubuntu-latest
    steps:
      - name: Re-run failed workflow jobs
        uses: actions/github-script@v7
        with:
          script: |
            const runs = await github.rest.actions.listWorkflowRuns({
              owner: context.repo.owner,
              repo: context.repo.repo,
              workflow_id: 'ci.yml',
              status: 'failure',
              per_page: 5,
            });
            for (const run of runs.data.workflow_runs) {
              await github.rest.actions.reRunFailedJobs({
                owner: context.repo.owner,
                repo: context.repo.repo,
                run_id: run.id,
              });
            }
```

---

## Part 3 — Automated Report Quality Checking (Q1.2)

### The Problem

Today the quality-check loop is:

```
Copilot generates code → CI runs test paper → human reads report → human decides if OK
```

The bottleneck is the human read. The scientific goals are fuzzy (not unit-testable), but they *can* be expressed as a prompt.

### The Meta-Evaluation Agent

Add a CI job that runs after `review` and feeds the generated report back to an LLM with a scientific-goals checklist:

```
REPORT QUALITY CHECKER
======================
Scientific goals:
1. The novelty verdict must be evidence-backed (cite specific prior work).
2. The decomposition must reflect the paper's actual core contribution.
3. The combination check must distinguish "uses X + Y" from "derives new insight from X + Y".
4. The equivalence check must flag mathematical/algorithmic reframings, not just surface similarity.
5. The pipeline job log must show all 4 retrieval sources were attempted.

For each goal: PASS / PARTIAL / FAIL + 1-sentence reason.
Overall: ACCEPTABLE | NEEDS_REVISION

Report to evaluate:
{report_content}
```

The checker's output becomes a CI artifact and can gate the workflow (fail the job if `NEEDS_REVISION`).

### Encapsulating the Module

The quality-checker follows the same pattern as every other agent in the pipeline:

```python
# open_idea_sourcing/report_checker.py

def check_report_quality(
    report: str,
    goals: str,          # loaded from prompts/report_check.txt
    llm: LLMCallable,
) -> ReportCheckResult:
    ...
```

```yaml
# In ci.yml:
  check-quality:
    needs: review
    runs-on: ubuntu-latest
    steps:
      - name: Download report artifact
        uses: actions/download-artifact@v4
        with:
          name: src-ideas-reports
          path: reports/

      - name: Check report quality
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python -c "
          import glob, sys
          from open_idea_sourcing.report_checker import check_report_quality, build_llm
          llm = build_llm()
          for f in glob.glob('reports/*.md'):
              result = check_report_quality(open(f).read(), llm=llm)
              print(result.summary)
              if result.verdict == 'NEEDS_REVISION':
                  sys.exit(1)
          "
```

### Max Reusability

The module is reusable without modification if:
- `goals` is a parameter (not hardcoded) — load from `prompts/report_check.txt`
- `llm` is a parameter — same `(str) -> str` interface as every other agent
- `ReportCheckResult` is a dataclass — same pattern as `NoveltyResult`

Any future pipeline that produces a structured text report can plug in the same checker with a different goals file.

---

## Part 4 — Multi-Agent Architecture for Research Pipelines (Q2)

### The Three-Horizon Vision

The project is not just a sequential evaluation pipeline. The ultimate form — derived
from the Wasserstein distance / forward-backward pass framing in Issue #48 — is a
**multi-agent debate network** where specialised agents with different roles collaborate
to produce a derivation certificate. The path there is through three horizons, each a
prerequisite for the next.

**See `PROJECT_MASTER_PLAN.md` for the full three-horizon breakdown.**
This section focuses on the mechanics: which framework to reach for and when.

---

### Horizon 1 — Plain Python `Pipeline` class (now)

The current pipeline is already a multi-agent system in the functional sense:

| Stage | Agent | Input | Output |
|-------|-------|-------|--------|
| 1 | PaperParser / LLMPaperParser | Raw PDF/text | `ParsedPaper` |
| 2 | DecompositionAgent (LLM) | `ParsedPaper` | `IdeaDecomposition` |
| 3a–3e | Retrieval sub-agents (parallel) | paper + decomp | `ReferenceStore` |
| 4 | SimilaritySearch (TF-IDF) | query vs corpus | `list[SimilarityResult]` |
| **5** | **AnnotationAgent (LLM)** | **paper + refs** | **`DerivationEvidence`** ← runs BEFORE 6 |
| 6a | DuplicationChecker (LLM) | paper + refs + derivation | verdict |
| 6b | CombinationChecker (LLM) | paper + refs + derivation + dup | verdict |
| 6c | EquivalenceChecker (LLM) | paper + refs + derivation + dup + combo | verdict |
| 7 | SynthesisAgent (LLM) | 3 verdicts + novel_elements | `DerivationCertificate` |
| 8 | ReportGeneratorAgent | certificate + metadata | report |
| 9 | ReportCheckerAgent | report | `ACCEPTABLE/NEEDS_REVISION` |

`PipelineContext` is the shared state bus. The gap is in making it fully modular.

### The Four Properties of a Swappable Agent

1. **Stateless** — takes inputs as arguments, returns outputs, no side effects
2. **Single-callable interface** — `(context: PipelineContext) -> PipelineContext` or equivalent
3. **Config-described** — which agent runs at each stage is declared in `pipeline_config.yaml`
4. **Individually testable** — callable with a mock LLM and stubbed input, no other stages running

### The Agent Registry Pattern

```python
# open_idea_sourcing/pipeline.py

REGISTRY = {
    "parse":       PaperParserAgent,       # or LLMPaperParserAgent via config
    "decompose":   DecompositionAgent,
    "retrieve":    RetrievalAgent,         # wraps all 3a–3e sub-agents
    "rank":        TFIDFRanker,            # or DenseRetriever via config
    "annotate":    AnnotationAgent,        # MUST run before evaluate
    "duplication": DuplicationAgent,
    "combination": CombinationAgent,
    "equivalence": EquivalenceAgent,
    "synthesize":  SynthesisAgent,
    "render":      ReportGeneratorAgent,
    "check":       ReportCheckerAgent,
}

class Pipeline:
    def __init__(self, config: PipelineConfig, llm: LLMCallable):
        self.stages = [REGISTRY[name](config, llm) for name in config.stages.enabled]

    def run(self, source: str) -> NoveltyReport:
        ctx = PipelineContext.empty()
        for stage in self.stages:
            ctx = stage.run(ctx)
        return ctx.report

    def run_from(self, ctx: PipelineContext, stage_name: str) -> NoveltyReport:
        """Resume from a checkpoint — invaluable for prompt tuning."""
        start = next(i for i, s in enumerate(self.stages) if s.name == stage_name)
        for stage in self.stages[start:]:
            ctx = stage.run(ctx)
        return ctx.report
```

`run_from()` is the ablation primitive: change a prompt file → `run_from("duplication")` →
result in seconds, not minutes.

---

### Horizon 2 — LangGraph for iterative retrieval loops

**When you hit this:** The one-shot query-search-done pattern is producing
insufficient coverage. You need: generate queries → search → assess → refine → repeat.

LangGraph is the right tool because:
- The loop has a **conditional exit** (exit when coverage score is sufficient)
- State accumulates across iterations (previously-seen refs, previous query attempts)
- Each node is a pure function; the graph handles the looping and state

```python
from langgraph.graph import StateGraph, END

retrieval_graph = StateGraph(RetrievalState)
retrieval_graph.add_node("generate_queries", generate_queries_node)
retrieval_graph.add_node("search",           search_node)
retrieval_graph.add_node("assess_coverage",  assess_coverage_node)
retrieval_graph.add_node("refine_queries",   refine_queries_node)

retrieval_graph.add_edge("generate_queries", "search")
retrieval_graph.add_edge("search",           "assess_coverage")
retrieval_graph.add_conditional_edges(
    "assess_coverage",
    lambda s: END if s.coverage_sufficient else "refine_queries"
)
retrieval_graph.add_edge("refine_queries",   "search")
```

This subgraph replaces the `RetrievalAgent` stage in the `Pipeline`. Everything else
in the pipeline is unchanged — the subgraph still receives a `PipelineContext` and
returns one.

**MCP tool servers alongside LangGraph:**
Expose Semantic Scholar, arXiv fetch, and the reference store as MCP servers.
Every node in the LangGraph graph, and every CrewAI agent in Horizon 3, calls the
same tool layer. The tools are implemented once.

---

### Horizon 3 — CrewAI multi-agent debate

**When you hit this:** Single-agent evaluation quality has plateaued. The
forward/backward pass convergence design requires genuinely independent agents
arguing from different starting points.

**Why CrewAI here (not LangGraph):**
- CrewAI's **role + backstory** model shapes each LLM's reasoning orientation
  without prompt engineering gymnastics
- The `Critic Agent` challenging the `Domain Expert`'s verdict is a natural
  CrewAI task delegation pattern
- CrewAI's built-in memory and tool assignment handles coordination so you focus
  on the science

```python
from crewai import Agent, Task, Crew

librarian = Agent(
    role="Research Librarian",
    goal="Find every plausible prior work for this paper, exhaustively",
    backstory="You are a specialist at navigating academic databases...",
    tools=[semantic_scholar_tool, arxiv_tool, reference_store_tool],
    llm="gpt-4o-mini",   # fast + cheap for retrieval
)

domain_expert = Agent(
    role="Domain Expert",
    goal="Build the concept tree and trace derivation from prior work",
    backstory="You are a senior researcher who can recognise when a paper...",
    tools=[concept_tree_tool],
    llm="o3",            # reasoning model for deep decomposition
)

critic = Agent(
    role="Adversarial Critic",
    goal="Find every flaw in the expert's derivation claims; demand evidence",
    backstory="You are a hard-nosed reviewer who rejects hand-waving...",
    tools=[semantic_scholar_tool],
    llm="o3",
)

judge = Agent(
    role="Final Judge",
    goal="Produce the definitive derivation certificate from the expert-critic debate",
    backstory="You are a senior programme chair...",
    tools=[],            # no tools; pure reasoning
    llm="o3",
)
```

The forward/backward pass from Issue #48 maps directly:
- **Domain Expert** runs the forward pass: builds the paper from prior work
- **Critic** runs the backward pass: reduces from ground truth, challenges the forward claims
- **Judge** reconciles the two into the derivation certificate

---

### When to Use Which Framework (Decision Table)

| Situation | Framework | Why |
|-----------|-----------|-----|
| Linear sequential pipeline | **Plain Python** | No routing complexity; fastest to iterate |
| Retrieval loop with conditional exit | **LangGraph** | Conditional edges + state across iterations |
| State checkpointing / resume from node | **LangGraph** | Built-in state persistence |
| Parallel fan-out / fan-in | **LangGraph** | Native parallel node execution |
| Multiple distinct agent *roles* interacting | **CrewAI** | Role + backstory shapes reasoning; inter-agent memory |
| Multi-agent debate / critique | **CrewAI** | Task delegation and adversarial dynamics |
| Tool callable by any LLM / any framework | **MCP server** | Standardised protocol; write once, call everywhere |
| Single agent with many tools | **OpenAI Agents SDK** | Simpler than CrewAI for single-agent |
| Cross-provider agent (GPT + Claude together) | **CrewAI** | LLM-agnostic role assignment |

**LangGraph ≠ CrewAI.** They are complementary:
- LangGraph = graph execution engine (handles *when* and *how* stages run)
- CrewAI = agent role manager (handles *who* is doing *what* and *why*)
- In Horizon 3: LangGraph handles the retrieval subgraph; CrewAI handles the debate network

**What NOT to use:**
- **LangChain** as an orchestrator: hides agent boundaries; hard to unit-test; heavy dependency. Use it only for specific utilities (e.g., document loaders) not as the pipeline backbone.
- **AutoGen** conversational loop: designed for open-ended multi-turn dialogue; overkill for structured evaluation with defined stage outputs.

### When to Introduce Parallelism

The dimension checks (duplication, combination, equivalence) are sequential because
each feeds context into the next — do not parallelize them.

Parallelize here:

```
retrieve (bundled)     ──┐
retrieve (paper-cited) ──┤── merge → rank → annotate → [evaluate chain]
retrieve (online)      ──┤
retrieve (domain)      ──┘
```

In LangGraph this is a native parallel fan-out. In plain Python (Horizon 1),
`asyncio.gather` or `ThreadPoolExecutor` suffices.

---

## Part 5 — DOs and DON'Ts for the Next Phase

### Architecture

| ✅ DO | ❌ DON'T |
|-------|---------|
| One agent = one file + one prompt template | Bundle multiple analysis passes into one LLM call |
| Every agent interface: `(ctx: PipelineContext) -> PipelineContext` | Pass raw strings between stages — always use typed dataclasses |
| PipelineContext as the single source of truth at runtime | Write results to module-level variables |
| Config file describes the pipeline; code executes it | Hardcode stage order or model names in the orchestrator |
| Extract a prompt to `.txt` the first time it exceeds 3 lines | Inline prompts in Python source |

### Ablation

| ✅ DO | ❌ DON'T |
|-------|---------|
| One config file per experiment; check it in | Run experiments by editing source and not recording what changed |
| Record `config_file` in `RunMetadata` | Rely on git blame to reconstruct which config produced which result |
| Name configs descriptively: `configs/no-chain_regex-parse.yaml` | Name configs `config2.yaml`, `config_new.yaml` |
| Keep `pipeline_config.yaml` as the known-good baseline | Change defaults between experiments without a CHANGELOG entry |

### Development Flow

| ✅ DO | ❌ DON'T |
|-------|---------|
| Separate PRs for pipeline wiring vs. performance tuning | Mix architectural changes with prompt tweaks in one PR |
| Write an atomic issue per Copilot session (< 45 min of work) | Write issues that span multiple architectural layers |
| Gate CI on both unit tests AND the report quality checker | Merge when tests pass but the actual report output is degraded |
| Treat the report quality checker as a first-class CI job | Read reports manually as the sole quality signal |
| Use `--no-online-search --no-bundled-refs` etc. for fast iteration | Always run the full pipeline during development |

### Versioning

| ✅ DO | ❌ DON'T |
|-------|---------|
| Bump version + CHANGELOG together in one PR before tagging | Tag from a stale commit or without a changelog entry |
| Use semantic versioning: MAJOR for interface breaks, MINOR for new features, PATCH for fixes | Use version numbers as sequential PR labels |
| Preserve intermediate minor versions (`2.1`, `2.2`, `2.3`) as release tags | Let intermediate states exist only as commit SHAs |

---

## Summary: The Next Phase Paradigm

The system has three horizons. **Do not skip ahead — each is load-bearing.**

**Horizon 1 — Clean sequential pipeline (now):**
1. Extract `Pipeline` class with `run_from()` — the ablation primitive
2. Move agents to `agents/` directory — one file, one prompt, one test
3. Add `configs/` directory — one file per experiment baseline
4. Fix annotation-before-evaluation ordering (biggest correctness gap)
5. Add `ReportCheckerAgent` — closes the quality-gate loop

**Horizon 2 — Iterative loops + tool ecosystem:**
1. Replace one-shot retrieval with a LangGraph iterative subgraph
2. Expose Semantic Scholar, arXiv, and reference store as MCP servers
3. Add dense retrieval as a swappable rank backend

**Horizon 3 — Multi-agent debate (the ultimate form):**
1. CrewAI crew: Librarian + Domain Expert + Critic + Judge + Reporter
2. Forward pass (Domain Expert) + backward pass (Critic) converge on derivation certificate
3. The Wasserstein distance formulation becomes operational

The system then becomes self-improving: every run produces a traceable certificate,
every report is graded by the quality checker, every retrieval gap triggers a
refined query loop, and every hard case routes to the multi-agent debate network.
