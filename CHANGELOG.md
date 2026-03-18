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
- Pipeline Job Log (Mermaid Gantt diagram + table) displayed at the top of every report, immediately after run metadata.
- `RunMetadata` now records `git_branch`, `git_commit` (with clickable hyperlink), `git_commit_url`, and `ci_run_url` for full provenance tracing.
- Metadata section grouped into three sub-tables: **Run context**, **Configuration**, **Performance**.
- Report filenames now start directly with the paper title (no `novelty_report_` prefix).

---

## [1.0.0] — 2025-01-01

### Added
- Initial release: novelty evaluation pipeline with duplication, combination, and methodological-equivalence checks.
- Reference store (TF-IDF similarity search) with JSON persistence.
- Report formats: plain text, Markdown, JSON, PDF.
- CLI (`review_paper.py`) with `--format`, `--output`, `--reports-dir`, `--top-k`, `--model`, `--references`, `--save-references` options.
- GitHub Actions CI workflow: tests + optional paper-review dispatch.
- `RunMetadata` with model, input source, timestamp, stage runtimes, and code version.

---

<!-- Links are auto-maintained — update when a new version is tagged -->
[Unreleased]: https://github.com/yulinl2/Open-Idea-Sourcing/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yulinl2/Open-Idea-Sourcing/releases/tag/v1.0.0
