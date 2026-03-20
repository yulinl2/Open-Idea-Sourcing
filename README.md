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
```

Then open `.env` and set your API key:

```bash
OPENAI_API_KEY=sk-...
```

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
| `--model NAME` | `gpt-4o` | OpenAI model (or `OPENAI_MODEL` env var) |
| `--reports-dir DIR` | `reports` | Output directory for auto-named report files |
| `--output FILE` | — | Write to an exact path instead of `--reports-dir` |
| `--papers-file FILE` | — | NDJSON batch file (mutually exclusive with positional arg) |

---

## Pipeline Architecture (v1.2.0)

```
[Stage 1 — Ingest]
  Input:  paper URL / file path
  Output: PaperDigest {title, abstract, full_text, source_url, arxiv_id}
  Agent:  PaperParser

[Stage 2 — Understand]
  Input:  PaperDigest
  Output: IdeaDecomposition {core_concept, sub_ideas, assumptions, limitations}
  Agent:  LLM (decomposition prompt)

[Stage 3 — Retrieve]       ← three sub-stages, each independently togglable
  Input:  PaperDigest + IdeaDecomposition
  3a. BundledReferenceSearch  — TF-IDF over data/references.json
  3b. OnlineReferenceSearch   — Semantic Scholar: arXiv refs (depth) + LLM queries (breadth)
  3c. LLMQueryGenerator       — conceptual queries from paper content
  Output: ReferenceStore (merged, deduplicated)

[Stage 4 — Compare]
  Input:  PaperDigest + top-K from ReferenceStore
  Output: list[SimilarityAnnotation] {paper, score, overlap, differences, derivation}
  Agent:  LLM (annotation prompt)

[Stage 5 — Evaluate]       ← three independent passes
  Input:  PaperDigest + IdeaDecomposition + list[SimilarityAnnotation]
  5a. DuplicationCheck    → {verdict, explanation}
  5b. CombinationCheck    → {verdict, explanation}
  5c. EquivalenceCheck    → {verdict, explanation}
  5d. DomainRefFinder     → list[DomainReference]   (→ Stage 3d in future)
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

**Key design principles (long-term direction):**

| Principle | Why |
|---|---|
| **Each stage = pure function with typed I/O** | Independently testable, swappable without touching adjacent stages |
| **LLM prompts are data, not code** | Independently versioned, A/B testable, diffable in git |
| **LLM protocol is injected** | Any model (OpenAI, Anthropic, local) slots in without changing pipeline code |
| **Each retrieval sub-stage independently togglable** | `--no-online-search` etc.; useful for debugging and ablation |
| **Evidence IDs in every LLM output** | Machine-readable citation linking; enables audit trail in report *(in progress)* |

---

## Codebase Layout

```
open_idea_sourcing/
├── __init__.py           Package version
├── paper_parser.py       Stage 1 — parse PDF/text → ParsedPaper
├── novelty_evaluator.py  Stages 2, 4, 5, 6 — LLM evaluation pipeline
├── online_search.py      Stage 3b — Semantic Scholar API client + LLM query generation
├── reference_store.py    Reference corpus (load, save, add, iterate)
├── similarity_search.py  Stage 3a — TF-IDF cosine similarity
└── report_generator.py   Stage 7 — Markdown / JSON / PDF rendering

data/
└── references.json       Bundled baseline reference corpus

review_paper.py           CLI entry point (orchestrates all stages)
tests/                    Unit + integration tests (417 total, no live API calls)
.github/workflows/
├── ci.yml                Test + paper-review workflow (workflow_dispatch + push)
└── release.yml           Automated GitHub Release on v* tags
```

---

## Testing

All tests run without an API key — the LLM is stubbed with canned responses.

```bash
make test          # verbose
make test-quiet    # summary only
```

```bash
417 passed in 2.4s
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
