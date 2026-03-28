# Debate / Reconstruction Pipeline Changelog

Changes for the **`ip_debate`** package — the IP debate / reconstruction test
pipeline.  This version series (`0.x.x`) is **independent** of the baseline
`open_idea_sourcing` series (`1.x.x` / `2.x.x` / …).

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Version separation FAQ

**Q: How is this version series kept separate from the baseline?**

The `ip_debate/` directory is a standalone Python package with its own
`__init__.py` and its own `__version__` string.  It is never imported by
`open_idea_sourcing` and its version is never read by the baseline release
workflow (`release.yml`).  A dedicated dispatch workflow
(`.github/workflows/debate_ci.yml`) drives CI for this track.

Tags for this track use the prefix **`debate-v`** (e.g. `debate-v0.1.0`) to
avoid clashing with the baseline `v1.x.x` tags that trigger `release.yml`.

---

## [Unreleased]

*(nothing yet — pipeline not built)*

---

## [0.0.0] — 2026-03-28

### Added

- `ip_debate/` package scaffold with `__version__ = "0.0.0"`.
- `ip_debate/report.py` — reporting interface stub (mirrors
  `open_idea_sourcing.report_generator` contract; raises
  `NotImplementedError` until the pipeline is built).
- `.github/workflows/debate_ci.yml` — dispatch workflow with
  `workflow_dispatch` inputs adapted for the debate / reconstruction pipeline.
- `DEBATE_CHANGELOG.md` — this file; tracks the 0.x version series.
- `tests/test_ip_debate.py` — smoke tests for the v0.0.0 scaffold.
