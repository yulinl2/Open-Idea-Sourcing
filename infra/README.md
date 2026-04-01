# infra — Shared Execution Shell

This directory is the **only** cross-track shared code in the Open-Idea-Sourcing
agent-track family. Track branches (`agent-e2e`, `agent-linear`,
`agent-reconstruct`) cherry-pick specific commits from the `infra-base` branch
to pick up improvements without merging track-specific logic.

---

## Module index

| Module | Public symbols | Purpose |
|--------|----------------|---------|
| `run_context.py` | `RunContext` | Run metadata container; serialises to YAML front matter |
| `report_writer.py` | `ReportWriter`, `ReportContent`, `DerivationEntry`, `PriorWorkEntry` | Renders canonical `report.md` |
| `tool_registry.py` | `ToolRegistry` | Records tool invocations per run |
| `search_tools.py` | `search_semantic_scholar`, `fetch_s2_citations`, `fetch_s2_paper`, `search_arxiv` | S2 + arXiv thin clients |
| `pdf_utils.py` | `extract_text_from_pdf` | PDF-to-text extraction |

---

## Cherry-pick contract

1. Cherry-pick **specific commits**, not the whole branch.
2. Keep the `infra/` directory structure exactly as-is.
3. Reference the source commit in your commit message:
   ```
   cherry-pick infra: <description> (infra-base@<short-hash>)
   ```
4. Do not rename or remove base fields in `RunContext` — that breaks
   compatibility with existing `report.md` files from other tracks.
5. Track branches may **add** new fields to `RunContext` or new methods to
   `ReportWriter`, but should do so in track-local subclasses rather than
   modifying the base classes.

---

## What does NOT belong in infra

- Agent logic, decision loops, or reasoning prompts
- Track-specific stage classes or orchestration
- Frozen implementation snapshots (those live beside `agent.py` in each track branch)
- Any code that might be removed when a track evolves

If in doubt, put it in the track branch.
