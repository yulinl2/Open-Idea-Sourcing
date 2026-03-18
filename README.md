# Open-Idea-Sourcing

An AI system that reviews academic papers for **genuine novelty**. The system goes beyond detecting copy-paste plagiarism — it also identifies papers that merely combine existing works, traces each component to its origin, and reveals subtle methodological equivalences hidden behind different notation or framing.

## Features

| Capability | What it does |
|--------------------------------------------|-------------------------------------|
| **Direct duplication detection** | Identifies whether the paper's core ideas are essentially the same as prior work, even when wording differs |
| **Combination analysis** | Detects papers that are simple assemblies of existing components and traces each piece to its source |
| **Methodological equivalence** | Surfaces re-derivations of established methods under different names, notation, or application domains |
| **Automatic online reference search** | Queries the [Semantic Scholar](https://www.semanticscholar.org/) public API to discover related papers automatically — no local reference corpus needed |
| **Reference anchoring** | Compares the submission against discovered (and optionally user-supplied) reference papers via TF-IDF similarity search |
| **Structured reports** | Outputs detailed reports in plain text, Markdown, JSON, or PDF |

## Quick Start

### Installation

Clone the repository:

``` bash
git clone https://github.com/yulinl2/Open-Idea-Sourcing.git
cd Open-Idea-Sourcing
```

Then install the project dependencies:

``` bash
make install
```

This command creates a local virtual environment in `.venv`, creates a `.env` file from `.env.example` if needed, and installs the required Python packages.

### Configure API Key

Open `.env` and replace the placeholder value with your real API key:

``` bash
OPENAI_API_KEY=your_real_api_key_here
```

`review_paper.py` automatically loads `OPENAI_API_KEY` from `.env` and does not override an already-set environment variable.

### Review a Paper

Activate the virtual environment:

* On macOS/Linux:

``` bash
source .venv/bin/activate
```

* On Windows:

``` powershell
.venv\Scripts\Activate.ps1
```

``` bat
.venv\Scripts\activate.bat
```

Then **run the reviewer** (Markdown report):

``` bash
python review_paper.py path/to/paper.pdf --format markdown
```

You can also review a plain-text file:

``` bash
python review_paper.py path/to/paper.txt --format text
```

If you want to save the report to a file:

``` bash
python review_paper.py path/to/paper.pdf --format markdown > report.md
```


### Optional: Add Reference Papers

Create a `refs.json` file if you want to compare the paper against your own reference list:

``` json
[
  {
    "id": "vaswani2017",
    "title": "Attention Is All You Need",
    "abstract": "We propose the Transformer, a novel architecture based solely on attention mechanisms.",
    "authors": ["Ashish Vaswani", "Noam Shazeer"],
    "year": 2017,
    "venue": "NeurIPS"
  }
]
```

### Online Reference Search

By default, `review_paper.py` automatically queries the **Semantic Scholar** public API to find related papers before the LLM evaluation stages.  No API key or local corpus is required.

The search strategy is:

1. Query Semantic Scholar with the paper **title** (high-precision).
2. If too few results are returned, a second query is issued using the opening terms of the **abstract** (higher recall).
3. Duplicate results (same paper ID) are removed.
4. The fetched papers are added to the reference store and ranked by TF-IDF similarity against the submitted paper's content, so only the most relevant papers are surfaced to the LLM.

To disable online search (e.g., when working offline):

``` bash
python review_paper.py paper.pdf --no-online-search
```

The `--references` flag and online search can be used together; papers from both sources are merged in the reference store before similarity ranking.

## Architecture

```text
open_idea_sourcing/
├── paper_parser.py       Parse PDF/text → structured title, abstract, sections
├── reference_store.py    Manage a local corpus of reference papers (JSON)
├── online_search.py      Fetch related papers from the Semantic Scholar API
├── similarity_search.py  TF-IDF cosine similarity to find related references
├── novelty_evaluator.py  LLM-powered 3-pass novelty analysis + synthesis
└── report_generator.py   Render NoveltyReport as text / Markdown / JSON / PDF

review_paper.py           CLI entry point
```

### Evaluation passes

`NoveltyEvaluator` runs four LLM calls for each paper:

1.  **Duplication check** — Is this essentially a copy of a known paper?
2.  **Combination check** — Is this just A + B from existing works without a unifying insight?
3.  **Equivalence check** — Is this a re-derivation of a well-known method?
4.  **Synthesis** — Holistic verdict: `NOVEL`, `MARGINAL`, or `NOT_NOVEL`.

Each pass returns a structured `VERDICT / EXPLANATION / REFERENCES` block that is then compiled into a `NoveltyReport`.

### Bring your own LLM

The evaluator accepts any callable `(prompt: str) -> str`, so you can plug in a local model:

``` python
from open_idea_sourcing.novelty_evaluator import NoveltyEvaluator
from open_idea_sourcing.paper_parser import PaperParser

def my_llm(prompt: str) -> str:
    # call your local model here
    ...

parser = PaperParser()
paper = parser.parse_text(open("paper.txt").read())

evaluator = NoveltyEvaluator(llm=my_llm)
report = evaluator.evaluate(paper)
print(report.overall_verdict)
```

## Running the Tests

``` bash
make test
# or
make test-quiet
```

All tests run without an API key — the test suite stubs the LLM with canned responses.

## Common Commands

``` bash
make help      # show all available targets
make install   # create .venv, bootstrap .env (if missing), install dependencies
source .venv/bin/activate  # activate .venv in the current terminal
make test      # run tests (verbose)
make test-quiet # run tests (quiet)
```

Windows activation commands are in the "Review a Paper" section above.

## FAQ / Troubleshooting

### What is `make`? Do I need to install it?

`make` is a build automation tool that runs shortcuts like `make install` and `make test`.

Check whether you already have it:

``` bash
make --version
```

If that command prints a version, you are good to go.

If it says command not found:

-   macOS: install Apple Command Line Tools with `xcode-select --install`
-   Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y build-essential`

After installing, run:

``` bash
make install
```

### How do I check my Python version?

Run:

``` bash
python3 --version
```

This project targets Python 3.12+ and includes `.python-version` set to `3.12.12`.

### My Python version is too old. What should I do?

If `python3 --version` is below 3.12, install Python 3.12 and rerun setup:

``` bash
make install
```

If you use `pyenv`, one straightforward path is:

``` bash
pyenv install 3.12.12
pyenv local 3.12.12
make install
```

### Why isn't there a `make activate` target?

`make` runs each recipe in a child process, not in your current interactive terminal session.

-   A target like `activate` that runs `source .venv/bin/activate` only affects that child process.
-   After the target exits, your original terminal session is unchanged.
-   Use `source .venv/bin/activate` directly in your terminal before running app commands.

### `pytest: command not found`

Use:

``` bash
make test
```

If needed, activate first with `source .venv/bin/activate`.

### `No module named pytest`

This usually means you are using a global Python instead of the project venv. Run:

``` bash
make install
make test
```

### `pip: command not found`

Do not rely on global `pip`. Use project setup:

``` bash
make install
```

This uses `.venv/bin/python -m pip` internally.

## License

MIT © 2026 Yulin Li
