# Paper Novelty Review — Developer Guide

End-to-end reference for running the paper novelty evaluator locally, via GitHub Actions CI, and adapting the infrastructure to other projects.

---

## 1. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.12+ | `python3 --version` |
| `make` | any | `make --version`; install via Xcode CLT (macOS) or `apt install build-essential` (Linux) |
| OpenAI API key | — | Only needed for LLM evaluation; tests run without it |

---

## 2. First-time Setup (Local)

```bash
# 1. Clone and enter the repo
git clone https://github.com/yulinl2/Open-Idea-Sourcing.git
cd Open-Idea-Sourcing

# 2. Create .venv and install all dependencies
make install

# 3. Add your API key
#    make install copies .env.example → .env automatically
#    Open .env and replace the placeholder:
#      OPENAI_API_KEY=sk-...
```

---

## 3. Reviewing a Paper Locally

All commands assume the virtual environment is active (`source .venv/bin/activate` on macOS/Linux; `.venv\Scripts\Activate.ps1` on Windows) and `.env` contains `OPENAI_API_KEY`.

### Single paper — arXiv URL

```bash
# Markdown report saved to reports/
python review_paper.py https://arxiv.org/abs/2006.06138

# PDF report
python review_paper.py https://arxiv.org/abs/2006.06138 --format pdf
```

### Single paper — local file

```bash
python review_paper.py my_paper.pdf
python review_paper.py my_paper.txt --format text
```

### Batch review from NDJSON file

```bash
# data/test_papers.ndjson — one JSON object per line with "url" or "path" key
python review_paper.py --papers-file data/test_papers.ndjson --format markdown
```

### Offline / no internet mode

```bash
# Skip Semantic Scholar lookup; rely on bundled corpus + any --references file
python review_paper.py my_paper.pdf --no-online-search
```

### Key CLI flags

| Flag | Default | Description |
|---|---|---|
| `--format` | `pdf` | Output format: `text` · `markdown` · `json` · `pdf` |
| `--references FILE` | `data/references.json` | Additional JSON reference corpus (merged with bundled) |
| `--no-online-search` | off | Skip Semantic Scholar API lookup |
| `--top-k N` | `5` | Top-N similar papers passed to the LLM |
| `--model NAME` | `gpt-5.4` | OpenAI model (or `OPENAI_MODEL` env var) |
| `--reports-dir DIR` | `reports` | Output directory for auto-named reports |
| `--output FILE` | — | Exact output path (overrides `--reports-dir`) |
| `--papers-file FILE` | — | NDJSON batch input (mutually exclusive with positional arg) |

---

## 4. Online Reference Search

By default the evaluator queries the [Semantic Scholar Graph API](https://api.semanticscholar.org/) automatically — no API key required.

### How it works

1. **Depth signal** — when the input is an arXiv URL the paper's own bibliography is fetched via `GET /paper/arXiv:{id}/references`. These are the papers the authors cited; the highest-quality signal for detecting near-equivalent prior work.

2. **Breadth signal** — before querying Semantic Scholar, the LLM performs a conceptual digest of the paper and generates 4–6 short queries targeting:
   - The core scientific problem
   - The proposed approach / method
   - Alternative approaches that solve the same problem

   Each query is issued independently; results are merged and deduplicated.

3. **Abstract fallback** — fires as a last resort when both depth and breadth results are sparse.

All online results are added to the reference store before TF-IDF similarity search, so they flow into every subsequent stage.

### Pipeline job log

The **Online reference search** entry in every report's Pipeline Job Log shows the exact arXiv ID and LLM-generated query strings, e.g.:

```
arXiv:2006.06138 + 4 LLM queries: "conformal prediction coverage"; "distribution-free uncertainty quantification"; ...
```

---

## 5. Running via GitHub Actions CI

### One-time setup

Add your OpenAI key as a repository secret:

1. **Settings → Secrets and variables → Actions → New repository secret**
2. Name: `OPENAI_API_KEY` — Value: `sk-...`
3. Save

### Manual trigger (workflow_dispatch)

1. **Actions → CI → Run workflow**
2. Fill in:

   | Input | Default | Description |
   |---|---|---|
   | `paper_url` | *(empty)* | arXiv or direct PDF URL to review |
   | `papers_file` | `test_papers.ndjson` | NDJSON batch file inside `data/` — used when `paper_url` is empty |
   | `references` | `references.json` | JSON reference corpus filename inside `data/` |
   | `output_format` | `markdown` | Report format: `text` · `markdown` · `json` · `pdf` |

   > `paper_url` takes precedence over `papers_file` when both are set.

3. **Run workflow**

### Automatic trigger (push to main)

Every push to `main` automatically runs a review of `data/test_papers.ndjson` using the default inputs.

### Accessing results

| Channel | Where to find it |
|---|---|
| **CI artifact** | Run page → **Artifacts** section → `src-ideas-reports` (zip) |
| **Reports branch** | `reports` branch — persistent, browsable via GitHub |
| **Inline log** | Run page → **Review paper (manual trigger or main merge)** step |

Every report includes a Mermaid Gantt pipeline log, git commit, and CI run URL for full provenance tracing.

---

## 6. Reference Corpus

The bundled corpus `data/references.json` is loaded automatically on every run. It ships with one seed paper (arXiv:1904.06019) and grows as you add entries.

### Format

```json
[
  {
    "id": "vaswani2017",
    "title": "Attention Is All You Need",
    "abstract": "We propose the Transformer architecture based solely on attention mechanisms.",
    "authors": ["Ashish Vaswani", "Noam Shazeer"],
    "year": 2017,
    "venue": "NeurIPS",
    "url": "https://arxiv.org/abs/1706.03762"
  }
]
```

Required fields: `id`, `title`, `abstract`. All others are optional but recommended.

### Adding papers

Pass a supplementary corpus with `--references path/to/more.json`. It is merged on top of the bundled store; no entry is ever removed.

---

## 7. Running Tests

```bash
make test          # verbose
make test-quiet    # summary only
```

Tests stub the LLM and mock all HTTP calls — no API key or internet required.

```
431 passed in 2.4s
```

---

## 8. Using a Custom / Local LLM

The evaluator accepts any `(prompt: str) -> str` callable:

```python
from open_idea_sourcing.novelty_evaluator import NoveltyEvaluator
from open_idea_sourcing.paper_parser import PaperParser
from open_idea_sourcing.report_generator import ReportGenerator

def my_llm(prompt: str) -> str:
    # call ollama, llama.cpp, HuggingFace, etc.
    ...

paper = PaperParser().parse_file("my_paper.pdf")
report = NoveltyEvaluator(llm=my_llm).evaluate(paper)
print(ReportGenerator().generate(report, fmt="markdown"))
```

---

## 9. CI Infrastructure Summary (for Reuse)

This section documents the CI pattern so it can be replicated in forks or adapted to other multi-agent projects.

### Pattern: test → review → artifact → branch

```
push / pull_request → run tests (jobs: test)
workflow_dispatch / push to main → run tests → review paper(s) (jobs: test, review)
  review step:
    1. Install deps
    2. python review_paper.py ... → writes to reports/
    3. Upload reports/ as artifact "src-ideas-reports"
    4. Publish reports/ to the "reports" branch via git worktree
```

### Key components

| File | Role |
|---|---|
| `.github/workflows/ci.yml` | Test + paper-review workflow; `workflow_dispatch` inputs drive `review_paper.py` flags |
| `.github/workflows/release.yml` | Triggered by `v*` tags; verifies version, extracts changelog, creates GitHub Release |
| `review_paper.py` | CLI entry point; outputs to `reports/` by default |
| `data/test_papers.ndjson` | Default batch file for push-triggered runs |
| `reports` branch | Persistent, scrollable report store; one commit per CI run |

### Adapting to a new project (e.g. OpenNovelty fork)

Minimum copy set:

```
open_idea_sourcing/     → replace with your evaluation modules
review_paper.py         → replace with your orchestration CLI
requirements.txt        → update deps
.github/workflows/ci.yml → update inputs / script call
data/                   → seed corpus + batch file
```

No changes needed to the artifact upload or reports-branch push logic — those are project-agnostic.

### Adapting to a general multi-agent project (e.g. HAN theory ↔ architecture dev)

The pattern generalises to any pipeline that:
1. Takes a document / artifact as input
2. Runs a sequence of LLM (or non-LLM) analysis passes
3. Produces a structured report

Replace:
- `review_paper.py` with your pipeline orchestrator
- `data/test_papers.ndjson` with your default batch input
- The `src-ideas-reports` artifact name with your project's name
- The `reports` branch strategy with your desired persistence layer

The `workflow_dispatch` input schema, `[skip ci]` guard on the docs workflow, and reports-branch worktree approach are all reusable without modification.

---

## 10. Releasing a New Version

```bash
# 1. Update CHANGELOG.md — move [Unreleased] items to a new [x.y.z] section
# 2. Bump open_idea_sourcing/__init__.py: __version__ = "x.y.z"
# 3. Open a PR with those two changes and merge to main
# 4. Create and push the tag from main:
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

The `release.yml` workflow fires on the tag push and:
- Runs all tests (fails fast)
- Verifies `__version__` matches the tag
- Extracts the changelog section for the release body
- Creates a GitHub Release (pre-release if tag contains a hyphen)
