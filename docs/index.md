---
layout: default
title: Home
---

# Open Idea Sourcing

**AI-powered academic novelty evaluation** — goes beyond plagiarism detection to uncover subtle methodological equivalences and combination papers.

[![CI](https://github.com/yulinl2/Open-Idea-Sourcing/actions/workflows/ci.yml/badge.svg)](https://github.com/yulinl2/Open-Idea-Sourcing/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-1.2.0-blue)](https://github.com/yulinl2/Open-Idea-Sourcing/blob/main/CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

| Capability | What it does |
|---|---|
| **Duplication detection** | Identifies core-idea copies even when wording differs |
| **Combination analysis** | Detects A + B assemblies and traces each component to its source |
| **Methodological equivalence** | Surfaces re-derivations hidden behind different notation or domain |
| **Online reference search** | Queries [Semantic Scholar](https://www.semanticscholar.org/) automatically — no local corpus needed |
| **Reference anchoring** | Ranks discovered papers by TF-IDF similarity before passing to the LLM |
| **Structured reports** | Outputs plain text, Markdown, JSON, or PDF with a full pipeline job log |

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/yulinl2/Open-Idea-Sourcing.git
cd Open-Idea-Sourcing
make install

# 2. Set your OpenAI key in .env
#    OPENAI_API_KEY=sk-...

# 3. Review a paper (PDF report saved to reports/)
source .venv/bin/activate
python review_paper.py https://arxiv.org/abs/2006.06138

# Disable online search when offline
python review_paper.py paper.pdf --no-online-search

# Batch review from an NDJSON file
python review_paper.py --papers-file data/test_papers.ndjson
```

---

## Documentation

| Document | Description |
|---|---|
| [README](https://github.com/yulinl2/Open-Idea-Sourcing#readme) | Full feature overview and FAQ |
| [WORKFLOW_GUIDE.md](https://github.com/yulinl2/Open-Idea-Sourcing/blob/main/WORKFLOW_GUIDE.md) | Detailed CLI reference, GitHub Actions setup, batch mode, custom LLMs |
| [CHANGELOG.md](https://github.com/yulinl2/Open-Idea-Sourcing/blob/main/CHANGELOG.md) | Version history |

---

## Architecture

```
open_idea_sourcing/
├── paper_parser.py       Parse PDF/text → structured title, abstract, sections
├── reference_store.py    Manage a local corpus of reference papers (JSON)
├── online_search.py      Fetch related papers from the Semantic Scholar API
├── similarity_search.py  TF-IDF cosine similarity to find related references
├── novelty_evaluator.py  LLM-powered 3-pass novelty analysis + synthesis
└── report_generator.py   Render NoveltyReport as text / Markdown / JSON / PDF

review_paper.py           CLI entry point
```

---

*MIT © 2026 Yulin Li*
