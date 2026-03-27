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

---

## [2.6.0] — 2026-03-27

### Added

**Stage 2: Hardcoded decomposition swap-in**
- `--decomposition-mode hardcoded` + `--hardcoded-decomposition-file <path>` — bypasses the LLM for Stage 2 entirely; loads a JSON file with `core_concept` and `concept_tree` fields directly into the pipeline. Useful for ablation studies and reproducibility.
- `decomposition_mode` and `hardcoded_decomposition_file` settable in `pipeline_config.yaml`.
- `decomposition_model` field added to `RunMetadata` and displayed in the **Configuration** table of both Markdown and text reports when a separate Stage 2 model is configured.

**Stage 3: `include_paper_citations` guard**
- `OnlineReferenceSearch.search(include_paper_citations=True/False)` — when `False`, Phase 1 (both the arXiv-ID path and the title-lookup path) is entirely skipped; keyword search (Phase 2) still runs.
- `--no-paper-cited-refs` CLI flag now reliably skips *all* references-endpoint calls via this parameter.
- `fetch_citations(title, arxiv_id)` split out as a dedicated method on `OnlineReferenceSearch`, separate from `search()`. Cited papers are added to the reference store with `source="paper-cited"` (previously they were incorrectly tagged as `"online"`).

**Report: merged Reference Papers table**
- The separate "Most Similar Reference Papers" table and "Reference Index" section are merged into a single **Reference Papers** table with columns `Ref | Score | Source | Title | Year | Authors`.
- Source tags (`user`, `paper-cited`, `online`, `domain`) shown inline per row.

**Pipeline config: decomposition model field**
- `pipeline_config.yaml` gains a `decomposition_model` field (default commented out to `o3`) so Stage 2 can be routed to a high-reasoning model without changing the general `model` setting.

**Fast / slow test split**
- `pytest.ini` defines a `slow` marker.
- 15 large end-to-end test classes in `test_review_paper.py` and `test_novelty_evaluator.py` are marked `@pytest.mark.slow`.
- CI runs `pytest -m "not slow"` on feature-branch push/PR (~3 min); full suite runs on `main` push and `workflow_dispatch` only.
- `make test-fast` target added to `Makefile` for local use.

**Wake-up workflow: label opt-in + cooldown**
- `copilot-wakeup.yml` now requires the `copilot-wakeup` label on the PR — only PRs you explicitly opt in to will receive auto-wake-up comments.
- 30-minute cooldown guard: skips posting if the bot already commented within the last 30 minutes, preventing comment spam on repeated timeouts.

**Pipeline log improvements**
- Stage 1: parser failure is logged with the specific error so operators know what went wrong.
- Stage 2: core concept and concept tree depth/node count logged after decomposition.
- Stage 3: per-source load counts (`user`, `paper-cited`, `online`, `domain`) logged separately; online search errors now report how each error was handled and how many fetches each query produced.

### Fixed
- `paper-cited` source tagging: cited papers were previously tagged `"online"` in the reference store. They are now correctly tagged `"paper-cited"`.
- `get_source()` docstring corrected to distinguish "not tracked" (`""`) from "tracked with default label" (`"unknown"`).
- `_render_concept_tree_ascii()` docstring corrected: "no children" → "no label AND no children".
- `find_domain_references()` now correctly threads the `decomp` argument to `_find_domain_references()`; `{decomposition}` slot added to `domain_references.txt` prompt template.
- `_count_tree_depth()` and `_count_tree_nodes()` were using dict API (`.get("children")`) on `ConceptNode` dataclass; fixed to use `.children` attribute — resolves `AttributeError` crash during pipeline log output.

### Removed
- Dead `_build_mindmap()` function from `report_generator.py` (always returned `""` after `IdeaDecomposition` was slimmed in v2.4). Removed 10 associated tests.

---

## [2.5.0] — 2026-03-26

### Added

**Source priority deduplication**
- `ReferenceStore.add()` now respects a strict priority order when the same paper arrives from multiple sources: `user > paper-cited > online > domain`.
- The highest-priority label wins as the primary source tag; all provenance labels ever seen for a paper are retained and accessible via the new `get_all_sources(paper_id)` method.
- `_SOURCE_PRIORITY` dict at module level maps each source tag to an integer (lower = higher priority).

**REF-N Reference Index in reports**
- Both Markdown and text reports now include a **Reference Index** section that maps every `REF-N` label cited by the LLM to the actual paper title, year, authors, similarity score, source tag, and URL.
- The "Most Similar Reference Papers" table gains a `Ref` column so `REF-1` / `REF-10` are identifiable inline without scrolling to the index.

**Auto wake-up workflow**
- `.github/workflows/copilot-wakeup.yml` — listens for `workflow_run` completion with `conclusion: timed_out` on the CI workflow and automatically posts a Copilot wake-up comment on the associated PR.

### Fixed
- `UnboundLocalError: OnlineReferenceSearch` — removed a redundant `from ... import OnlineReferenceSearch` inside `_review_one()` that shadowed the module-level import. Fixes all 21 failures in `test_review_paper.py`.

---

## [2.4.0] — 2026-03-26

### Added

**Stage 1: LLM-only parser**
- `LLMPaperParser` now retries the LLM call up to 3× before raising `RuntimeError`. Regex fallback removed entirely — the LLM is always used when an API key is present.

**Stage 2: Slim `IdeaDecomposition`**
- `IdeaDecomposition` slimmed to two fields: `core_concept: str` and `concept_tree: ConceptNode | None`. All hard-structure fields (`sub_ideas`, `assumptions`, `limitations`, `implementation_steps`) removed.
- `decomposition.txt` prompt rewritten as a minimal, open-ended instruction — no structural prescription; the LLM determines depth and breadth from the scientific content.

**Stage 3: Threshold-only similarity filter**
- `[:self._top_k]` cap removed from both `evaluate()` and `evaluate_with_context()`. `similarity_threshold` is now the sole filter; all papers above the threshold are passed to evaluation.

**Stage 3d / Stage 4: Domain references as 4th source**
- `lookup_domain_refs()` added to `OnlineReferenceSearch` — resolves LLM-identified domain references via Semantic Scholar title lookup and adds them to the store with `source="domain"`.
- The four reference sources are now cleanly separated: `"user"`, `"paper-cited"`, `"online"`, `"domain"`.

**Stage 4: 1-to-all derivation annotation**
- `SimilarityAnnotation` redesigned: `derivation_map: dict[str, list[str]]` (concept component → `[REF-N, …]`), `combination_analysis: str`, `novel_elements: list[str]`.
- `annotation.txt` rewritten as a single prompt that sees all references simultaneously and identifies combination patterns across subsets.

**Pipeline: config file and reflection log**
- `pipeline_config.yaml` — central config file for all model, flag, and prompt settings; loaded via `--config FILE` CLI flag.
- `--save-reflection FILE` (env: `REFLECTION_FILE`) — appends one dated Markdown entry per evaluation to a growing audit-trail document.

### Changed
- Source tag `"bundled"` collapsed into `"user"` everywhere.
- `--no-bundled-refs` renamed to `--no-user-refs` (env: `NO_USER_REFS=1`).

---

## [2.3.0] — 2026-03-26

### Added

**Stage 5: Accumulated context in dimension chain**
- `_check_combination()` now receives `prior_dup` — the duplication verdict and
  explanation — injected as `PRIOR ANALYSIS` context into `combination.txt`.
- `_check_equivalence()` now receives both `prior_dup` and `prior_combo` — both
  prior verdicts — injected as accumulated `PRIOR ANALYSIS` context into
  `equivalence.txt`.
- `evaluate()` and `evaluate_with_context()` chain results:
  duplication → combination(dup) → equivalence(dup + combo).
- Implements the "increasingly deep digestion" design principle from Issue #42:
  each pass builds on the prior evidence rather than starting cold.

**Stage 3: Sub-stage toggle flags**
- `--no-bundled-refs` CLI flag (env: `NO_BUNDLED_REFS=1`) — skip loading
  `data/references.json` to isolate online-retrieval-only runs.
- `--no-paper-cited-refs` CLI flag (env: `NO_PAPER_CITED_REFS=1`) — skip the
  paper's own citation list retrieval from Semantic Scholar to isolate keyword-
  search-only retrieval.
- Together with the existing `--no-online-search`, all three Stage 3 sub-stages
  are now independently togglable for clean ablation studies.

---

## [2.2.0] — 2026-03-25

### Added

**Pipeline: `PipelineContext` as shared state bus**
- `PipelineContext` is now the single shared state object threaded through all pipeline stages in `_review_one()`.
- `NoveltyEvaluator.evaluate_with_context(ctx)` — ablation-friendly entry point that reads inputs from and writes results back to context, replacing the 6-parameter `evaluate()` call in the main pipeline.
- Enables: independent stage re-runs, per-stage checkpointing, reliable ablations (swap model/prompt/pipeline without touching adjacent stages).
- `PipelineContext` gains `search_queries`, `online_papers`, `stage_runtimes`, and `ref_sources` fields.
- Backward-compatible: the existing `evaluate()` method remains fully functional.

**Stage 1: LLM-based paper parser**
- `LLMPaperParser` in `paper_parser.py` — uses an LLM to extract title, abstract, authors, and section list from raw paper text. More robust than regex for real PDFs.
- Prompt template: `open_idea_sourcing/prompts/paper_parse.txt`.
- Falls back gracefully to the regex-based `PaperParser` when the LLM call fails or returns empty output.
- `--llm-parser` CLI flag (env: `LLM_PARSER=1`) to enable.

**Stage 3: Reference source separation and annotated audit list**
- `ReferenceStore.add(paper, source=...)` and `ReferenceStore.load(path, source=...)` accept a source label.
- `ReferenceStore.get_source(paper_id)` returns the source label for any loaded paper.
- Source labels: `"bundled"` (data/references.json), `"user"` (--references file), `"online"` (keyword search).
- Pipeline log similarity-search job detail shows a complete annotated reference list grouped by source. Enables full audit trail without mixing or auto-ingesting sources.

---

## [2.1.0] — 2026-03-25

### Added

**Stage 5: REF-N evidence IDs in analysis prompts**
- `format_references()` now labels each reference as `REF-N [id]: Title…` — enables LLMs to cite references by short label (REF-1, REF-3) rather than opaque 40-char Semantic Scholar UUIDs.
- All dimension prompts (`duplication`, `combination`, `equivalence`) updated to request `REF-N` citations in their REFERENCES field.
- Reports display cited `REF-N` labels inline with each analysis dimension.

**Stage 3: Temporal reference filter**
- `OnlineReferenceSearch(min_year=YYYY)` — filters retrieved papers by publication year.
- `--since-year YEAR` CLI flag: only online references published in or after YEAR are included.
- Year filter applied to both `/paper/search` query params (Semantic Scholar `year=YYYY-` param) and post-processing of `/references` endpoint results.

**Stage 3: Retry logic for transient HTTP errors**
- `OnlineReferenceSearch._http_get()` — shared HTTP-GET helper with exponential-backoff retry (up to 3 attempts, base delay 2 s) for HTTP 429 (rate limit), 500, and 503 errors.
- Non-retryable errors (400, 401, 404) fail immediately as before.

**Stage 3: All 3 reference sources always aggregated**
- For non-arXiv papers, `OnlineReferenceSearch.search()` now calls `_lookup_paper_id_by_title()` to find the Semantic Scholar paper ID and fetch the paper's own reference list — the same depth signal previously only available for arXiv submissions.

**Stage 3 / Stage 5: Threshold-based reference filtering**
- Default `similarity_threshold` raised from 0.05 → 0.1 (papers below this score are never included).
- Default `top_k_similar` cap raised from 5 → 20 (threshold is now the primary filter).
- `--similarity-threshold FLOAT` CLI flag (env: `SIMILARITY_THRESHOLD`).
- `--top-k` default raised to 20.

### Changed
- `decomposition.txt` prompt relaxed: removes "exactly 3 levels" prescription; tree size is now "as needed" (typically 2–4 levels). Prompt shortened and more flexible.
- `--top-k` default changed from 5 → 20 to work with the new threshold-first filtering.

---

**Online reference search**
- Fixed URL encoding bug in `OnlineReferenceSearch._fetch_references`: `urllib.parse.quote(safe="")` encoded the colon in `arXiv:XXXX.XXXXX` to `%3A`. Semantic Scholar's API expects the literal colon; changed to `safe=":"`.
- `OnlineReferenceSearch` now records HTTP / network errors in `self._last_errors` (accessible via `.last_errors` property). The SemanticScholar API Pipeline Job Log detail section surfaces these errors (e.g. HTTP 429 rate-limit) so users can tell why 0 papers were fetched.

**Reference corpus**
- Removed placeholder "A custom reference paper" (`user-paper-001`) from `data/references.json`; it was a test stub that poisoned similarity search with a zero-score result for every evaluation run.

---

## [2.0.0] — 2026-03-25

### Added

**Deep concept tree decomposition (Stage 2 — Understand)**
- `ConceptNode` dataclass — recursive tree node (`label: str`, `children: list[ConceptNode]`).
- `IdeaDecomposition` gains two new fields: `concept_tree: ConceptNode | None` and `implementation_steps: list[str]`.
- `decomposition.txt` prompt updated to elicit a `CONCEPT_TREE` indented outline (3 levels: Problem/Method/Evidence at L1, sub-problems at L2, key terms at L3) and `IMPLEMENTATION_STEPS` (5–8 numbered concrete steps).
- `_parse_concept_tree_text()` — indent-aware parser; auto-detects 2-space or 4-space indent unit; handles multi-root outlines via a virtual root.
- `_format_decomp_context()` — compact formatter for injecting decomposition context into LLM prompts.
- `_render_concept_tree_ascii()` in `report_generator.py` — renders `ConceptNode` trees with `├──`, `└──`, `│` box-drawing chars; replaces Mermaid mind-map in reports.
- `implementation_steps` rendered as a numbered **Implementation Roadmap** in Markdown and text reports.
- JSON output includes `concept_tree` (nested dict) and `implementation_steps` in `idea_decomposition`.

**Prompts directory**
- All prompt templates moved from inline constants in `novelty_evaluator.py` into versioned `.txt` files under `open_idea_sourcing/prompts/`.
- `_load_prompt(name)` helper reads templates at import time.
- All dimension prompts (`duplication`, `combination`, `equivalence`, `annotation`) gain a `{decomposition}` slot — verdicts are now grounded in the structural concept breakdown.

**Stage 2 before Stage 3**
- `NoveltyEvaluator.decompose_idea(paper, raw)` public method — callable before the retrieval step.
- `review_paper.py` calls decomposition before online search (Stage 2 → Stage 3) so the concept tree can inform Semantic Scholar query generation.
- `generate_search_queries()` accepts an optional `decomposition` keyword argument; when provided, the concept context is appended to the query-generation prompt.
- `evaluate()` accepts `idea_decomposition` parameter — skips internal decomposition when a pre-computed result is passed.

**Separate decomposition model**
- `NoveltyEvaluator(decomposition_llm=...)` — routes the decomposition step through a separate callable; enables using a reasoning model for the expensive structural pass.
- `--decomposition-model NAME` CLI flag (env: `OPENAI_DECOMPOSITION_MODEL`) — passes a separate LLM to `NoveltyEvaluator`.
- `_build_llm()` auto-detects reasoning models (`o1-*`, `o3-*`, `o4-*` prefix) and omits `temperature` from the API call.

**Pipeline context**
- `PipelineContext` dataclass — typed shared state bus for pipeline stages (foundation for future `Pipeline` class refactor).

### Changed
- Idea Decomposition report section: ASCII concept tree replaces Mermaid mind-map when `concept_tree` is populated; `implementation_steps` appear as a numbered roadmap.
- Pipeline Job Log: Stage 2 (Idea decomposition) now appears before Stage 3 (Online reference search).

---

## [1.3.0] — 2026-03-25

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

## [1.2.0] — 2026-03-25

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
[Unreleased]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v2.6.0...HEAD
[2.6.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v1.3.0...v2.0.0
[1.3.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/yulinl2/Open-Idea-Sourcing/releases/tag/v1.0.0
