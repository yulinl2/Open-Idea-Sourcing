# Open-Idea-Sourcing

> **An AI-powered academic paper novelty evaluator.**  
> Designed to produce *defensible, evidence-backed* verdicts on originality — replicating what a senior reviewer does when cross-checking a submission against the literature.

[![CI](https://github.com/yulinl2/Open-Idea-Sourcing/actions/workflows/ci.yml/badge.svg)](https://github.com/yulinl2/Open-Idea-Sourcing/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What It Does

The system goes beyond plagiarism detection. It answers the harder question: *"If I strip away the notation, framing, and jargon — what is actually new here?"*

| Capability | Description |
|---|---|
| **Idea decomposition** | Parses the paper into core concept, sub-ideas, assumptions, and limitations before any comparison |
| **Online reference search** | Queries the [Semantic Scholar](https://www.semanticscholar.org/) public API using LLM-generated conceptual queries — surfaces work that is conceptually equivalent, not merely keyword-similar |
| **Bundled reference corpus** | Ships with `data/references.json`; loaded automatically without any configuration |
| **TF-IDF similarity search** | Finds the most related papers in the combined (bundled + online) corpus |
| **Per-paper annotation** | LLM analysis of overlap, differences, and derivation for each top-matched reference |
| **Multi-axis novelty evaluation** | Three independent passes: Direct Duplication · Simple Combination · Methodological Equivalence |
| **Evidence-backed synthesis** | Holistic verdict aggregating all dimensions with supporting context |
| **Domain references** | LLM-identified key literature that contextualises the paper in its field |
| **Rich reports** | Markdown / PDF / JSON / text; collapsible sections, Mermaid diagrams, pipeline log, clickable citations |

---

## Primary Workflow: GitHub Actions CI

The intended daily-use interface is **GitHub Actions**, not the CLI. Trigger a review from the repo's Actions tab:

1. Go to **Actions → CI → Run workflow**
2. Fill in `paper_url` (e.g. `https://arxiv.org/abs/2006.06138`) or leave blank to use the default batch file
3. Optionally set `output_format` (default: `markdown`)
4. Click **Run workflow**

The job will:
- Download and parse the paper
- Query Semantic Scholar for related work (LLM-generated conceptual queries + arXiv reference list)
- Run the full evaluation pipeline
- Upload the report as a **CI artifact** (`src-ideas-reports`)
- Push the report to the `reports` branch for persistent browsing

Every run record includes: git commit, CI run URL, model, timestamp, and a Mermaid Gantt pipeline log — giving full provenance for every report.

---

## Local Quick Start

### Install

```bash
git clone https://github.com/yulinl2/Open-Idea-Sourcing.git
cd Open-Idea-Sourcing
make install          # creates .venv, installs deps, copies .env.example → .env
make install-hooks    # enables local pre-commit / pre-push guardrails
```

Then open `.env` and set your API key:

```bash
OPENAI_API_KEY=sk-...
```

### Local Workflow Guardrails

To catch workflow mistakes before commit/push:

```bash
make install-hooks
make test-workflows
```

The hooks currently block known breaking patterns in GitHub workflow files,
including:

- unsupported `permissions: workflows:` entries
- tab indentation in workflow YAML
- `workflow_dispatch` inputs with `options:` but no `type: choice`
- `gh workflow run agent-review.yml` calls that omit `--ref main`
- staged generated junk such as `.venv/`, `__pycache__/`, `*.pyc`, and shell-redirect artifacts like `=6.0`
- pushes from `main` / `copilot/*` branches whose history is not rooted in `origin/main`

### VS Code One-Click Workflow Dispatch

This repo now includes a workspace-scoped Copilot custom agent and prompt for
dispatching the agent-track workflow from chat:

- Agent: `.github/agents/agent-track-dispatcher.agent.md`
- Prompt: `.github/prompts/run-agent-track-workflow.prompt.md`

In VS Code chat, use:

```text
/ci-review track=all paper_url=https://arxiv.org/abs/2006.06138 model=gpt-5.4
/ci-one-off fix-gitignore
/ci-one-off sync-agent-review-workflow branches='infra-base agent-e2e' dry_run=true
/ci-one-off housekeeping-reports target_branch=agent-reports
```

`/ci-review` dispatches `agent-review.yml` directly and supports
`track=all|e2e|linear|reconstruct`.

`/ci-one-off` dispatches `agent-track-workflows.yml` and is maintenance-only.

The one-off command accepts arguments such as:

```text
fix-gitignore
sync-agent-review-workflow dry_run=true
housekeeping-reports target_branch=agent-reports
```

The dispatcher always uses `--ref main` on workflow dispatch commands to avoid
the recurring default-branch lookup failure.

PR comment formatting tip:
- To avoid broken markdown from escaped newlines, post PR comments with:
  `scripts/post_pr_comment.sh <pr-number> --repo owner/repo --body-file /path/to/comment.md`
- You can also pipe stdin:
  `cat /path/to/comment.md | scripts/post_pr_comment.sh <pr-number> --repo owner/repo`
- To fix an already-posted comment in place:
  `scripts/post_pr_comment.sh --edit-comment-id <comment-id> --repo owner/repo --body-file /path/to/comment.md`
- By default the helper formats agent-posted comments with a visible badge:
  ```text
  ## ✨🤖 Copilot via VS Code ✨

  **AI-assisted PR update**

  ---
  ```
- To post without the badge, add `--as-user` (or `--plain`).

Important for one-off sync operation:
- `sync-agent-review-workflow` updates `.github/workflows/agent-review.yml` on orphan branches.
- GitHub's default `GITHUB_TOKEN` often cannot push workflow-file changes.
- Configure repo secret `ORPHAN_WORKFLOW_PUSH_TOKEN` before running this operation.
- Recommended token scopes:
  - classic PAT: `repo` + `workflow`
  - fine-grained PAT: repository `Contents: Read and write` + `Workflows: Read and write`

What is PAT?
- PAT means Personal Access Token: a GitHub token you create in your account settings.
- In this repo, PAT is needed only for operations that write `.github/workflows/*.yml` via Actions automation.
- For normal review dispatch and most code/report writes, default `GITHUB_TOKEN` is enough.

Why `fix-gitignore` may not disappear immediately:
- `fix-gitignore` can still apply `.gitignore` updates without a PAT.
- But auto-retire edits `agent-track-workflows.yml` (a workflow file), which needs PAT-level workflow write access.
- If `ORPHAN_WORKFLOW_PUSH_TOKEN` is missing, the run now shows an explicit summary note and skips retirement.

Deferred cloud option:
If one-click dispatch is ever needed on GitHub.com rather than VS Code, the
recommended implementation is a comment-triggered Actions workflow that listens
to PR comments such as `/agent-track fix-gitignore` and then dispatches
`agent-track-workflows.yml` with validated inputs. This is intentionally not
enabled yet; keep the current repo-local VS Code agent as the primary path.

### Review a Paper

```bash
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\Activate.ps1      # Windows PowerShell

# Single paper — Markdown report saved to reports/
python review_paper.py https://arxiv.org/abs/2006.06138

# Single PDF — PDF report
python review_paper.py my_paper.pdf

# Disable online search (offline / fast mode)
python review_paper.py my_paper.pdf --no-online-search

# Batch review from NDJSON file
python review_paper.py --papers-file data/test_papers.ndjson --format markdown
```

### Common Options

| Flag | Default | Description |
|---|---|---|
| `--format` | `pdf` | Output format: `text` · `markdown` · `json` · `pdf` |
| `--references FILE` | `data/references.json` | Additional JSON reference corpus (merged with bundled) |
| `--no-online-search` | off | Skip Semantic Scholar lookup (offline / debugging) |
| `--top-k N` | `5` | Number of similar papers to surface |
| `--model NAME` | `gpt-5.4` | OpenAI model (or `OPENAI_MODEL` env var) |
| `--reports-dir DIR` | `reports` | Output directory for auto-named report files |
| `--output FILE` | — | Write to an exact path instead of `--reports-dir` |
| `--papers-file FILE` | — | NDJSON batch file (mutually exclusive with positional arg) |

---

## Pipeline Architecture (v1.3.0)

```
[Stage 1 — Ingest]
  Input:  paper URL / file path
  Output: ParsedPaper {title, abstract, full_text, source_url}
  Agent:  PaperParser

[Stage 2 — Understand]  ← runs inside evaluate(); long-term: extract before Stage 3
  Input:  ParsedPaper
  Output: IdeaDecomposition {core_concept, sub_ideas, assumptions, limitations}
  Agent:  LLM (decomposition prompt)

[Stage 3 — Retrieve]    ← four sub-stages, each independently togglable
  Input:  ParsedPaper
  3a. BundledReferenceSearch  — TF-IDF over data/references.json
  3b. OnlineReferenceSearch   — Semantic Scholar: arXiv refs (depth) + LLM queries (breadth)
  3c. LLMQueryGenerator       — conceptual queries from paper content
  3d. DomainRefFinder         — LLM identifies key domain references ← moved from 5d
  Output: ReferenceStore (merged, deduplicated) + list[DomainReference]

[Stage 4 — Compare]
  Input:  ParsedPaper + top-K from ReferenceStore
  Output: list[SimilarityAnnotation] {paper, score, overlap, differences, derivation}
  Agent:  LLM (annotation prompt)

[Stage 5 — Evaluate]    ← three independent passes
  Input:  ParsedPaper + IdeaDecomposition + list[SimilarityAnnotation]
  5a. DuplicationCheck  → {verdict, explanation}
  5b. CombinationCheck  → {verdict, explanation}
  5c. EquivalenceCheck  → {verdict, explanation}
  Agent:  LLM (dimension prompts)

[Stage 6 — Synthesize]
  Input:  Stage 5 outputs
  Output: {overall_verdict, summary, confidence}
  Agent:  LLM (synthesis prompt)

[Stage 7 — Render]
  Input:  all of the above
  Output: Markdown / JSON / PDF / text report
  Agent:  ReportGenerator
```

**Remaining gaps vs. ideal long-term architecture:**

| Gap | Impact | Status |
|---|---|---|
| Stage 2 (IdeaDecomposition) still inside `evaluate()` | Can't pass decomposition context to query generation at Stage 3c | Deferred — next major refactor |
| Stage 4 (Annotation) runs after Synthesis, not before Stage 5 | Evaluation passes don't receive per-paper evidence context | Deferred — next major refactor |
| Evidence IDs not yet in evaluation prompts | Verdicts are not explicitly citation-linked | Highest-priority scientific unlock |
| `evaluate()` still monolithic | Can't swap/skip individual passes; test isolation limited | Deferred — extract `Pipeline` class |

**Key design principles (long-term direction):**

| Principle | Why |
|---|---|
| **Each stage = pure function with typed I/O** | Independently testable, swappable without touching adjacent stages |
| **LLM prompts are data, not code** | Independently versioned, A/B testable, diffable in git |
| **LLM protocol is injected** | Any model (OpenAI, Anthropic, local) slots in without changing pipeline code |
| **Each retrieval sub-stage independently togglable** | `--no-online-search` etc.; useful for debugging and ablation |
| **Evidence IDs in every LLM output** | Machine-readable citation linking; enables evidence audit trail in report *(in progress)* |
| **PipelineContext as shared bus** | Replace 8+ function params with one context object; easy to inspect mid-run |

---

## Codebase Layout

```
open_idea_sourcing/
├── __init__.py           Package version
├── paper_parser.py       Stage 1 — parse PDF/text → ParsedPaper
├── novelty_evaluator.py  Stages 2, 4, 5, 6 — LLM evaluation pipeline; exposes find_domain_references (3d)
├── online_search.py      Stage 3b+3c — Semantic Scholar API client + LLM query generation
├── reference_store.py    Reference corpus (load, save, add, iterate)
├── similarity_search.py  Stage 3a — TF-IDF cosine similarity
└── report_generator.py   Stage 7 — Markdown / JSON / PDF rendering

data/
└── references.json       Bundled baseline reference corpus

docs/
├── PROJECT_INSTRUCTIONS_AGENT.md  Agent-track charter (read before touching agent branches)
├── AGENT_TRACK_ROADMAP.md         Per-branch implementation roadmap
├── WORKFLOW_GUIDE.md              End-to-end developer guide for CI, local runs, and releases
└── CHANGELOG.md                   Release history (Keep-a-Changelog format)

review_paper.py           CLI entry point (orchestrates all stages)
tests/                    Unit + integration tests (417 total, no live API calls)
.github/
├── AGENT_INSTRUCTIONS.md          Canonical rules for AI coding agents (branch hygiene, git hygiene)
├── copilot-instructions.md        Auto-applied condensed rules (read by GitHub Copilot automatically)
└── workflows/
    ├── ci.yml                     Test + paper-review workflow (workflow_dispatch + push)
    └── release.yml                Automated GitHub Release on v* tags
```

---

## Testing

All tests run without an API key — the LLM is stubbed with canned responses.

```bash
make test          # verbose
make test-quiet    # summary only
```

```bash
431 passed in 2.4s
```

---

## Bring Your Own LLM

The evaluator accepts any `(prompt: str) -> str` callable:

```python
from open_idea_sourcing.novelty_evaluator import NoveltyEvaluator
from open_idea_sourcing.paper_parser import PaperParser

def my_llm(prompt: str) -> str:
    # call any local or remote model
    ...

paper = PaperParser().parse_file("paper.pdf")
report = NoveltyEvaluator(llm=my_llm).evaluate(paper)
print(report.overall_verdict)
```

---

## FAQ

**Q: Do I need to provide reference papers?**  
No. The bundled corpus (`data/references.json`) is loaded automatically, and Semantic Scholar is queried online for each run. You can optionally point `--references` at your own JSON corpus.

**Q: Can I run without internet access?**  
Yes — pass `--no-online-search` to skip the Semantic Scholar step and rely solely on the bundled corpus and any `--references` file.

**Q: How do I add my own reference papers?**  
Create a JSON file following the `ReferencePaper` schema (fields: `id`, `title`, `abstract`, `authors`, `year`, `venue`, `url`) and pass it with `--references path/to/refs.json`. It is merged on top of the bundled corpus.

**Q: What is `make`? Do I need it?**  
`make` is a standard build tool. Check with `make --version`.  
- macOS: `xcode-select --install`  
- Ubuntu/Debian: `sudo apt install build-essential`

**Q: How do I check my Python version?**  
`python3 --version` — this project requires Python 3.12+.

---

## License

MIT © 2026 Yulin Li
