# Open-Idea-Sourcing

An AI system that reviews academic papers for **genuine novelty**. The system goes beyond detecting copy-paste plagiarism — it also identifies papers that merely combine existing works, traces each component to its origin, and reveals subtle methodological equivalences hidden behind different notation or framing.

## Features

| Capability | What it does |
|---|---|
| **Direct duplication detection** | Identifies whether the paper's core ideas are essentially the same as prior work, even when wording differs |
| **Combination analysis** | Detects papers that are simple assemblies of existing components and traces each piece to its source |
| **Methodological equivalence** | Surfaces re-derivations of established methods under different names, notation, or application domains |
| **Reference anchoring** | Compares the submission against a user-managed corpus of reference papers via TF-IDF similarity search |
| **Structured reports** | Outputs detailed reports in plain text, Markdown, or JSON |

## Installation

```bash
# Clone the repository
git clone https://github.com/yulinl2/Open-Idea-Sourcing.git
cd Open-Idea-Sourcing

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Set your OpenAI API key

```bash
export OPENAI_API_KEY="sk-..."
```

### 2. (Optional) Build a reference store

Create a `refs.json` file listing papers to compare against:

```json
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

### 3. Review a paper

```bash
# Review a PDF with Markdown output
python review_paper.py my_paper.pdf --references refs.json --format markdown

# Review plain text, output JSON
python review_paper.py my_paper.txt --format json > report.json

# Use a different model
python review_paper.py my_paper.pdf --model gpt-4-turbo --format text
```

## Architecture

```
open_idea_sourcing/
├── paper_parser.py       Parse PDF/text → structured title, abstract, sections
├── reference_store.py    Manage a local corpus of reference papers (JSON)
├── similarity_search.py  TF-IDF cosine similarity to find related references
├── novelty_evaluator.py  LLM-powered 3-pass novelty analysis + synthesis
└── report_generator.py   Render NoveltyReport as text / Markdown / JSON

review_paper.py           CLI entry point
```

### Evaluation passes

`NoveltyEvaluator` runs four LLM calls for each paper:

1. **Duplication check** — Is this essentially a copy of a known paper?
2. **Combination check** — Is this just A + B from existing works without a unifying insight?
3. **Equivalence check** — Is this a re-derivation of a well-known method?
4. **Synthesis** — Holistic verdict: `NOVEL`, `MARGINAL`, or `NOT_NOVEL`.

Each pass returns a structured `VERDICT / EXPLANATION / REFERENCES` block that is then compiled into a `NoveltyReport`.

### Bring your own LLM

The evaluator accepts any callable `(prompt: str) -> str`, so you can plug in a local model:

```python
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

```bash
pytest tests/ -v
```

All 75 tests run without an API key — the test suite stubs the LLM with canned responses.

## License

MIT © 2026 Yulin Li
