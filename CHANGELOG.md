# Changelog

All notable changes to **Open-Idea-Sourcing** are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## How to release a new version

1. **Update this file** — move items from `[Unreleased]` into a new `## [x.y.z] — YYYY-MM-DD` section.
2. **Bump the package version** — edit `open_idea_sourcing/__init__.py`:
   ```python
   __version__ = "x.y.z"
   ```
3. **Open a PR** with those two changes and merge it to `main`.
4. **Create a tag** from `main` (see options below) — the release workflow fires automatically.

### Tagging options

| Tool | Steps |
|------|-------|
| **GitHub.com UI** | *Releases → Draft a new release → Choose a tag → type `vx.y.z` → Publish* |
| **GitHub Desktop** | *Repository menu → Create Tag… → enter `vx.y.z` → push when prompted* |
| **Command line** | `git tag -a v1.2.3 -m "Release v1.2.3" && git push origin v1.2.3` |
| **Ask @copilot** | Open a PR comment or issue and say _"@copilot tag and release v1.2.3"_ — the agent can draft the version-bump PR for you |

The `release.yml` workflow will:
- Run all tests (fails fast if any test breaks).
- Verify `__version__` in `__init__.py` matches the tag.
- Create a GitHub Release with the changelog excerpt as release notes.
- Mark the release as a **pre-release** automatically if the tag contains a hyphen (e.g. `v1.1.0-beta.1`).

---

## [Unreleased]

### Added

**Paper parser**
- `ParsedPaper` gains an `authors: list[str]` field; `PaperParser._extract_authors()` heuristically extracts author names (capitalised-word lines between the title and institutional affiliations).
- `_extract_title()` now joins continuation lines (lines starting with a lowercase letter or connector word such as "of", "for", "via") so multi-line PDF titles are reconstructed correctly (e.g. "Conformal Inference" + "of Counterfactuals …" → full title).
- PaperParser Pipeline Job Log detail section now shows an **Authors** field.

**Online reference search**
- Fixed URL encoding bug in `OnlineReferenceSearch._fetch_references`: `urllib.parse.quote(safe="")` encoded the colon in `arXiv:XXXX.XXXXX` to `%3A`. Semantic Scholar's API expects the literal colon; changed to `safe=":"`.
- `OnlineReferenceSearch` now records HTTP / network errors in `self._last_errors` (accessible via `.last_errors` property). The SemanticScholar API Pipeline Job Log detail section surfaces these errors (e.g. HTTP 429 rate-limit) so users can tell why 0 papers were fetched.

**Reference corpus**
- Removed placeholder "A custom reference paper" (`user-paper-001`) from `data/references.json`; it was a test stub that poisoned similarity search with a zero-score result for every evaluation run.

---

## [2.2.0] — 2026-03-25

### Changed

**Stage 2 (Understand) now runs before Stage 3 (Retrieve)**
- `NoveltyEvaluator.decompose_idea()` — new public method that runs the idea decomposition pass before online retrieval so the structured concept tree is available to inform LLM query generation.  The caller (Stage 2) records the PipelineJob entry; `evaluate()` skips the internal LLM call when `idea_decomposition` is pre-supplied.
- `evaluate()` gains two new optional parameters — `idea_decomposition: IdeaDecomposition | None` and `_idea_decomposition_raw: dict[str, str] | None` — mirroring the existing `domain_references` / `_domain_references_raw` pattern for pre-computed stages.
- `generate_search_queries()` in `online_search.py` gains an optional `decomposition: IdeaDecomposition | None` parameter.  When a decomposition with a `core_concept` is supplied, the enhanced `_QUERY_GENERATION_PROMPT_WITH_DECOMP` is used; conceptual queries are derived from the structured concept tree rather than just the raw paper text.
- `review_paper._review_one()` now runs Stage 2 immediately after parsing (before Stage 3), passes the pre-computed decomposition to `generate_search_queries`, and forwards it to `evaluate()` so no redundant LLM call is made.  The "Idea decomposition" PipelineJob is added to `early_jobs` with a correct offset relative to parse + decomp duration.
- The `stage_runtimes` dict now includes a `"decomposition"` entry.

**Evidence IDs (REF-N labels) in evaluation prompts**
- `format_references()` now labels each reference as `REF-N [id]: ...` instead of `N. [id] ...`.
- `_DUPLICATION_PROMPT`, `_COMBINATION_PROMPT`, and `_EQUIVALENCE_PROMPT` INSTRUCTIONS now explicitly instruct the LLM to cite references using their `REF-N` label (e.g. `REF-2`) both within the EXPLANATION and in the REFERENCES field.
- `_SYNTHESIS_PROMPT` INSTRUCTIONS now ask the LLM to back SUMMARY claims with `REF-N` labels where relevant.

---

## [2.1.0] — 2026-03-25

### Added

**Concept tree pipeline integration — the tree is now analytically useful**
- `_render_concept_tree_text()` — module-level helper (parallel to `report_generator._render_concept_tree_ascii`) that renders a `ConceptNode` tree as an ASCII string for embedding in LLM prompts.
- `_format_decomp_context()` — produces a compact decomposition summary string (core concept + ASCII concept tree) for injection into every downstream analysis prompt.
- `NoveltyEvaluator` gains `decomposition_llm` and `decomposition_model` constructor parameters so a stronger reasoning model (e.g. `o3-mini`, `o4-mini`) can be used specifically for the decomposition step without increasing cost for the rest of the pipeline.
- `--decomposition-model` CLI flag (also honours `OPENAI_DECOMPOSITION_MODEL` env var) wires a separate LLM callable into `NoveltyEvaluator.decomposition_llm`.

### Changed

- `_DUPLICATION_PROMPT`, `_COMBINATION_PROMPT`, `_EQUIVALENCE_PROMPT`, and `_SYNTHESIS_PROMPT` each now include a `PAPER DECOMPOSITION` section that provides the concept tree (or core concept + key components when no tree is present) to the analysis LLM.  The analysis passes can now reason about the paper's hierarchical structure explicitly — tracing each branch of the tree to a prior-art source — rather than treating the paper as a flat text blob.
- `_check_duplication`, `_check_combination`, `_check_equivalence`, `_synthesise` accept an optional `decomposition: str` argument so the context can be cleanly controlled in tests.
- `_decompose_idea()` uses `self._decomposition_llm` rather than `self._llm`, enabling the decomposition LLM to be swapped independently.
- `_build_llm()` in `review_paper.py` now auto-detects reasoning models (`o1-*`, `o3-*`, `o4-*` prefix) and omits the `temperature` parameter from the chat completion request, which those models do not accept.
- The `Idea decomposition` Pipeline Job Log entry shows the decomposition model name when it differs from the main model.

---

## [2.0.0] — 2026-03-25

### Added

**Deep concept tree (v2.0 primary feature)**
- `ConceptNode` dataclass — a recursive tree node (`label: str`, `children: list[ConceptNode]`) that represents any level of technical detail in a hierarchical concept tree.
- `IdeaDecomposition.concept_tree: ConceptNode | None` — optional hierarchical concept tree field added to the existing decomposition dataclass.  When present it supersedes the flat lists as the primary structured view of the paper's contribution.
- `_parse_concept_tree_text()` — parses indentation-based (2-spaces per level) LLM output into a `ConceptNode` tree.  Blank lines are ignored; nodes are attached to the deepest available parent.
- `_render_concept_tree_ascii()` in `report_generator.py` — renders a `ConceptNode` tree as a list of ASCII box-drawing lines using `├──` / `└──` / `│` connectors (identical to the Unix `tree` command output).
- `_concept_tree_to_dict()` in `report_generator.py` — serialises a `ConceptNode` tree to a JSON-compatible nested dict (`{label, children?}`).

### Changed

- `_IDEA_DECOMPOSITION_PROMPT` updated to request a `CONCEPT_TREE` section from the LLM — a multi-level indented tree with at least 3 top-level branches (Problem, Method, Evidence) and ≥3 levels deep where the technical implementation warrants it.
- Markdown report: replaced the Mermaid `mindmap` diagram (Idea Mind Map section) with an ASCII concept tree rendered in a fenced code block under a new `### Concept Tree` section within `## Idea Decomposition`.  The ASCII tree is renderer-agnostic, never silently drops nodes, and goes arbitrarily deep.
- Text report: `## Idea Decomposition` section now renders the concept tree with the `_render_concept_tree_ascii` helper when a tree is present.
- JSON report: `idea_decomposition` object gains an optional `concept_tree` key containing the full nested node structure when a tree is present.

---

## [1.3.0] — 2026-03-20

### Added

**Online reference search (Stage 3 — Retrieve)**
- `open_idea_sourcing/online_search.py` — `OnlineReferenceSearch` class queries the [Semantic Scholar Graph API](https://api.semanticscholar.org/) (no API key required).
  - *Depth signal*: `GET /paper/arXiv:{id}/references` fetches the paper's own bibliography when an arXiv ID is available.
  - *Breadth signal*: LLM-generated conceptual queries (central problem, proposed strategy, alternative approaches) are issued against `/paper/search`, surfacing work that is *conceptually equivalent* even when terminology differs.
  - *Fallback*: abstract-derived query fires when both depth and breadth returns are sparse.
  - Results are merged, deduplicated, and added to the reference store before TF-IDF similarity search.
- `generate_search_queries(paper_content, llm)` free function — separated from the search engine so query generation and retrieval can be swapped or ablated independently.
- `--no-online-search` CLI flag — opt out when working offline or debugging with a fixed reference corpus.
- `_extract_arxiv_id(source)` helper in `review_paper.py` — extracts the arXiv ID from the paper URL (including `.pdf`-suffixed variants) and passes it to `OnlineReferenceSearch.search(arxiv_id=...)`.
- Pipeline Job Log detail sections — collapsible `<details>` blocks below each agent's table:
  - *PaperParser*: extracted title, abstract excerpt, and full section list.
  - *SemanticScholar API*: numbered query list and all fetched paper titles/years.
  - *SimilaritySearch*: query excerpt (code block) and all matches with cosine scores.
- `PipelineJob.detail: str = ""` field — optional extended Markdown content; empty string suppresses the detail block.

### Changed

- **DomainRefFinder moved to Stage 3d (Retrieve)**: `NoveltyEvaluator.find_domain_references()` is now a public method called from `review_paper.py` after similarity search, before the evaluation passes. It is classified as a *retrieval* task (contextualising the paper in its field), not an evaluation pass. Pipeline Job Log records it in the retrieval group.
- `evaluate()` accepts `domain_references` + `_domain_references_raw` optional parameters; when provided the internal call is skipped and the caller's PipelineJob is recorded instead (backward-compatible).
- Pipeline Job Log Gantt diagram groups pre-LLM stages (parse, online search, similarity, domain refs) separately from LLM evaluation stages.
- Similarity search pipeline job input cell shortened to `TF-IDF cosine on N ref(s)` (full results in detail section).
- Pipeline Job Log Online reference search input cell shortened to `arXiv:{id} + N LLM queries` (full query list in detail section).
- **Source blockquote removed** from the report header — the paper URL was duplicated between the blockquote and Run Metadata → Configuration → Input; blockquote removed.
- **Domain references** redesigned from a dense table to a **numbered list**: each entry has a clickable title (Semantic Scholar search link), inline authors + year, and relevance text in a collapsible `<details>` block.
- **Reference annotations** format changed from prose paragraphs inside `<details>` to an **inline 2-column comparison table** (`Dimension | Notes`) rendered immediately visible — Overlap, Differences, and Derivation are scannable side-by-side.

### Fixed

- `_extract_field()` regex now handles `**FIELD:**` markdown-bold format that LLMs sometimes emit (using `(?:\*\*)?` exact-asterisk groups). This resolves three visible symptoms: "0 sub-idea(s)" in the Pipeline Job Log, double labels in Idea Decomposition (`**Core concept:** **CORE_CONCEPT:** …`), and wrong dimension verdicts (❓ UNCLEAR when the LLM returned e.g. `**VERDICT: LOW**`).
- arXiv PDF URLs with `.pdf` suffix (e.g. `https://arxiv.org/pdf/1706.03762.pdf`) now correctly extract the arXiv ID for depth-signal retrieval.
- Semantic Scholar User-Agent header now derives from `__version__` instead of the hard-coded `open-idea-sourcing/1.0`.

---

## [1.2.0] — 2026-03-20

### Added

**Enriched evaluation pipeline**
- `IdeaDecomposition` dataclass — runs *first* in the evaluation pipeline; decomposes the paper into core concept, sub-ideas, assumptions, and limitations.
- Idea decomposition section (with Mermaid mind-map diagram) appears at the top of every report, before the overall verdict.
- `SimilarityAnnotation` dataclass — per-reference LLM annotation of overlap, differences, and derivation for each top-matched paper.
- `DomainReference` dataclass — LLM-identified key references contextualising the paper in its field.
- Bundled reference corpus `data/references.json` — ships with the repository; loaded automatically without requiring `--references`.
- `--references` now defaults to the bundled baseline corpus (`data/references.json`); user-supplied stores are merged on top.
- Paper metainfo block (title, authors, venue, year) displayed at the top of Markdown/PDF reports.
- Collapsible `<details>` blocks for each novelty dimension in Markdown/PDF reports.

### Changed
- `--save-references` removed; the bundled corpus is now the persistent default store.
- `evaluate()` LLM call order: decomposition → duplication → combination → equivalence → synthesis → domain references → per-paper annotation.

---

## [1.1.0] — 2026-03-18

### Added
- Pipeline Job Log (Mermaid Gantt diagram + table) displayed at the top of every report, immediately after run metadata.
- `RunMetadata` now records `git_branch`, `git_commit` (with clickable hyperlink), `git_commit_url`, `ci_run_url`, and `pr_number` for full provenance tracing.
- Metadata section grouped into three sub-tables: **Run context**, **Configuration**, **Performance**.
- Report filenames now start directly with the paper title (no `novelty_report_` prefix).
- Automated GitHub Releases via `release.yml` workflow (triggered by `v*` tags).
- `CHANGELOG.md` with Keep-a-Changelog format and tagging guide.

---

## [1.0.0] — 2026-03-14

### Added
- Initial release: novelty evaluation pipeline with duplication, combination, and methodological-equivalence checks.
- Reference store (TF-IDF similarity search) with JSON persistence.
- Report formats: plain text, Markdown, JSON, PDF.
- CLI (`review_paper.py`) with `--format`, `--output`, `--reports-dir`, `--top-k`, `--model`, `--references`, `--save-references` options.
- GitHub Actions CI workflow: tests + optional paper-review dispatch.
- `RunMetadata` with model, input source, timestamp, stage runtimes, and code version.

---

<!-- Links are auto-maintained — update when a new version is tagged -->
[Unreleased]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/yulinl2/Open-Idea-Sourcing/releases/tag/v1.0.0
