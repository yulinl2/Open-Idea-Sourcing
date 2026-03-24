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
