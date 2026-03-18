# Paper Novelty Review — Developer Guide

End-to-end reference for running the paper novelty evaluator locally or via GitHub Actions.

---

## 1. Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.12+ | Check with `python3 --version` |
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
#    make install creates .env from .env.example automatically
#    Open .env and replace the placeholder:
#      OPENAI_API_KEY=sk-...
```

---

## 3. Reviewing a Paper Locally

All commands assume the virtual environment is active and `.env` contains `OPENAI_API_KEY`.

macOS/Linux activation:

```bash
source .venv/bin/activate
```

Windows activation:

```powershell
.venv\Scripts\Activate.ps1
```

```bat
.venv\Scripts\activate.bat
```

### From a local file

```bash
# PDF report saved to reports/ (default format)
python review_paper.py my_paper.pdf

# Plain-text or JSON
python review_paper.py my_paper.pdf --format text
python review_paper.py my_paper.pdf --format json > report.json

# With a reference corpus (see Section 7)
python review_paper.py my_paper.pdf --references refs.json
```

### From an arXiv URL

The CLI auto-converts `/abs/` links to `/pdf/` and cleans up the temp file afterwards.

```bash
# Abstract URL — automatically rewritten to PDF URL
python review_paper.py https://arxiv.org/abs/2006.06138

# Direct PDF URL
python review_paper.py https://arxiv.org/pdf/2006.06138v2

# Save the report
python review_paper.py https://arxiv.org/abs/2006.06138 > report.md
```

Only `https://` URLs are accepted.

### Key CLI flags

| Flag | Default | Description |
|---|---|---|
| `--format` | `pdf` | Output format: `text`, `markdown`, `json`, `pdf` |
| `--output FILE` | none | Write the report to this exact file path (overrides `--reports-dir`) |
| `--reports-dir DIR` | `reports` | Directory where auto-named reports are written |
| `--references FILE` | none | JSON reference corpus to compare against |
| `--save-references FILE` | none | Persist the current reference store to a JSON file |
| `--top-k N` | `5` | Max similar reference papers passed to the LLM |
| `--model NAME` | `gpt-4o` | OpenAI model (or set `OPENAI_MODEL` env var) |
| `--no-online-search` | off | Disable automatic Semantic Scholar lookup (use for offline runs) |
| `--papers-file FILE` | none | NDJSON batch file; each line must have a `url` or `path` key |

---

## 4. Online Reference Search

By default, `review_paper.py` automatically queries the **Semantic Scholar** public API to discover related papers before the LLM evaluation stages.  No API key or local corpus is required.

### How it works

1. The paper title is sent as a search query (high-precision results).
2. If fewer than five results are returned, a second query uses the opening terms of the abstract (higher recall).
3. Duplicates are removed by paper ID.
4. Fetched papers are merged with any `--references` corpus and ranked by TF-IDF cosine similarity so only the most relevant papers reach the LLM.

### Disable online search

```bash
python review_paper.py my_paper.pdf --no-online-search
```

Use this flag when running offline or when you want to control the reference corpus entirely through `--references`.

---

## 5. Batch Mode

Review several papers in one command using an [NDJSON](https://ndjson.org/) file:

```bash
python review_paper.py --papers-file data/test_papers.ndjson --format pdf
```

Each line in the file must be a JSON object with a `url` **or** `path` key:

```jsonl
{"url": "https://arxiv.org/abs/2006.06138"}
{"url": "https://arxiv.org/abs/1706.03762"}
{"path": "papers/draft.pdf"}
```

Reports are saved automatically to `--reports-dir` (default: `reports/`).  
The `--output` flag is not compatible with batch mode; use `--reports-dir` instead.

---

## 6. Running via GitHub Actions

### One-time repository setup

1. Go to **Settings → Secrets and variables → Actions → New repository secret**
2. Name: `OPENAI_API_KEY` — Value: your `sk-...` key
3. Save

> The workflow reads this secret automatically; you never type the key into the UI.

### Triggering a run

1. Open the repository on GitHub and click the **Actions** tab
2. In the left sidebar click **CI**
3. Click the grey **"Run workflow"** button (top-right of the runs table)
4. In the branch dropdown, select the branch that contains the workflow file  
   (e.g. `copilot/add-ai-paper-review-system` while on a PR, or `main` after merging)
5. Fill in the inputs:

   | Input | Required | Example |
   |---|---|---|
   | `paper_url` | yes (if no `paper_path`) | `https://arxiv.org/abs/2006.06138` |
   | `paper_path` | yes (if no `paper_url`) | `papers/draft.pdf` (repo-relative) |
   | `output_format` | no | `markdown` *(default)* |
   | `references_path` | no | `references/corpus/` (repo-relative; overrides default corpus) |

   > `paper_url` takes precedence if both are supplied.
   >  
   > If `references_path` is provided, the workflow uses that repo-relative directory/file as the reference corpus;  
   > if omitted, it falls back to the default reference corpus defined in `.github/workflows/ci.yml`.

6. Click the green **"Run workflow"** button

> **Tip:** If the "Run workflow" button does not appear, the `workflow_dispatch` trigger is missing from the selected branch.  
> Hard-refresh (Ctrl+Shift+R / Cmd+Shift+R) and double-check the branch.

### Finding the report

After the run completes:

- **Inline log**: open the run → click the **"Review paper"** step to read the report directly
- **Downloadable artifact**: scroll to the **Artifacts** section at the bottom of the run page → click **`novelty-report`**  
  The file extension matches the chosen format (`report.md`, `report.txt`, or `report.json`)

---

## 7. Reference Corpus Format

The reference store is a JSON array.  
Only `id`, `title`, and `abstract` are required; all other fields are optional.

```json
[
  {
    "id": "vaswani2017",
    "title": "Attention Is All You Need",
    "abstract": "We propose the Transformer, a novel architecture based solely on attention mechanisms …",
    "authors": ["Ashish Vaswani", "Noam Shazeer"],
    "year": 2017,
    "venue": "NeurIPS"
  },
  {
    "id": "devlin2018",
    "title": "BERT: Pre-training of Deep Bidirectional Transformers",
    "abstract": "…",
    "year": 2018
  }
]
```

Pass it with `--references refs.json`.  
The evaluator selects the most similar papers via TF-IDF cosine similarity and sends them to the LLM as context.

---

## 8. Running Tests

```bash
make test          # verbose
make test-quiet    # terse (pass/fail summary only)
```

Tests never require an API key — the LLM is injected as a stub.

---

## 9. Using a Custom / Local LLM

Replace the OpenAI backend with any `(str) -> str` callable:

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

## 10. Adapting to a New Project

To reuse this workflow in a different repository:

1. Copy `open_idea_sourcing/`, `review_paper.py`, `requirements.txt`, `Makefile`, and `.env.example`
2. Copy `.github/workflows/ci.yml`
3. Add `OPENAI_API_KEY` as a repository secret (Step 6 above)
4. Run `make install` and verify with `make test`

The `workflow_dispatch` trigger and artifact upload in `ci.yml` work out of the box with no further changes.
