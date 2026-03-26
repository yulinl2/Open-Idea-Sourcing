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

### Recognising the Architecture You Already Have

The current pipeline is already a multi-agent system in the functional sense:

| Stage | Agent | Input | Output |
|-------|-------|-------|--------|
| 1 | PaperParser / LLMPaperParser | Raw PDF/text | `ParsedPaper` |
| 2 | DecompositionAgent (LLM) | `ParsedPaper` | `IdeaDecomposition` |
| 3a | QueryGenerator (LLM) | `IdeaDecomposition` | `list[str]` queries |
| 3b | SemanticScholar API | queries + arXiv ID | `list[Paper]` |
| 3c | DomainRefFinder (LLM) | paper + similar papers | `list[DomainReference]` |
| 4 | SimilaritySearch (TF-IDF) | query vs corpus | `list[SimilarityResult]` |
| 5a | DuplicationChecker (LLM) | paper + refs | verdict + explanation |
| 5b | CombinationChecker (LLM) | paper + refs + dup | verdict + explanation |
| 5c | EquivalenceChecker (LLM) | paper + refs + dup + combo | verdict + explanation |
| 5d | SynthesisAgent (LLM) | 3 verdicts | final verdict |
| 6 | AnnotationAgent (LLM) | paper + top refs | `list[SimilarityAnnotation]` |

`PipelineContext` is already the shared state bus. The architecture is sound. The gap is in making it fully modular so each agent is independently swappable and independently testable.

### The Four Properties of a Swappable Agent

An agent in this system should be:

1. **Stateless** — takes inputs as arguments, returns outputs, no side effects
2. **Single-callable interface** — `(context: PipelineContext) -> PipelineContext` or equivalent
3. **Config-described** — which agent runs at each stage is declared in `pipeline_config.yaml`, not hardcoded in `_review_one()`
4. **Individually testable** — can be called with a mock LLM and stubbed input with no other agents running

Right now agents 5a–5d are hardcoded method calls in `NoveltyEvaluator`. The next step is to extract each as a standalone callable:

```python
# Today (entangled):
dup = self._check_duplication(paper, refs, ...)
combo = self._check_combination(paper, refs, prior_dup=dup, ...)

# Target (swappable):
dup_agent   = registry.get("duplication",  config)   # loads prompt, model from config
combo_agent = registry.get("combination",  config)
dup_result   = dup_agent(ctx)
combo_result = combo_agent(ctx)   # ctx now contains dup_result
```

### The Agent Registry Pattern

```python
# open_idea_sourcing/agent_registry.py

AGENTS = {
    "parse":        PaperParserAgent,
    "decompose":    DecompositionAgent,
    "retrieve":     RetrievalAgent,
    "similarity":   SimilarityAgent,
    "duplication":  DuplicationAgent,
    "combination":  CombinationAgent,
    "equivalence":  EquivalenceAgent,
    "synthesis":    SynthesisAgent,
    "annotate":     AnnotationAgent,
    "check_report": ReportCheckerAgent,   # ← the Q1.2 module plugs in here
}

def build_pipeline(config: PipelineConfig) -> list[Agent]:
    return [AGENTS[name](config) for name in config.stages.enabled]
```

This makes the pipeline itself a config artifact. Ablation = change which agents are in `config.stages.enabled`.

### What NOT to Use

| Tool | Avoid Because |
|------|--------------|
| LangChain | Hides agent boundaries; hard to unit-test individual steps; heavy dependency |
| AutoGen conversational loop | Good for open-ended dialogue agents, overkill for a deterministic evaluation pipeline |
| CrewAI | Role-based framework designed for collaborative tasks, not sequential analysis |
| LangGraph | Useful if you need dynamic branching between agents; premature here |

**DO:** Keep agents as plain Python callables with typed inputs/outputs. Add an orchestration framework only when the routing logic becomes too complex to express as a linear stage list.

### When to Introduce Parallelism

The dimension checks (duplication, combination, equivalence) are currently sequential because each feeds context into the next (v2.3 accumulated context chain). This is correct — don't parallelize them.

Parallelize across these boundaries instead:

```
retrieve (bundled) ──┐
retrieve (online)  ──┤── merge → similarity → [evaluate chain]
retrieve (domain)  ──┘
```

The three retrieval sub-agents are already independently runnable and don't share state. Running them concurrently with `asyncio.gather` or `ThreadPoolExecutor` is a legitimate performance win that doesn't compromise ablation clarity.

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

The current system is architecturally ready. The next phase is **operationalisation**:

1. **Flatten `_review_one()` into a config-driven stage runner** — the list of stages lives in the config, not in 600 lines of Python.
2. **Add `configs/` directory** — one file per known-good experiment baseline. These replace PR descriptions as the record of "what was the exact setup."
3. **Add `ReportCheckerAgent`** — closes the human-in-the-loop for quality validation. The scientific goals are a prompt file, not tribal knowledge.
4. **Add `ci-retry.yml`** — auto-retries flaky CI review runs so transient API errors don't require human intervention.
5. **Atomic issues** — each Copilot session targets one module, one stage, one prompt. The checklist in the PR description is the session plan; `report_progress` commits are its checkpoints.

The system then becomes self-auditing: every run is traceable to a config file, every report is graded by the quality checker, every failure is retried automatically, and every module is individually ablatable without touching adjacent code.
