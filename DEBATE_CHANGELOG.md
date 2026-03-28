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

**Q: How do we keep the baseline track up-to-date on this branch?**

The debate branch is a **regular branch** off the same repo — it shares commit
history with `main`, so a plain `git merge` is all that's needed:

```bash
git fetch origin
git checkout copilot/ip-debate-reconstruction-demo
git merge origin/main          # or: git rebase origin/main
git push origin copilot/ip-debate-reconstruction-demo
```

This is **automated** by `.github/workflows/sync_from_main.yml`, which
triggers every time a commit lands on `main` and merges it into this branch
(fast-forward when possible, merge commit otherwise).  If the auto-merge
produces a conflict you'll receive a workflow failure notification and can
resolve it manually with the commands above.

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
- `.github/workflows/sync_from_main.yml` — auto-merges `main` into this
  branch on every push to `main`, keeping the baseline track current.
- Initial merge of `main` (v2.6.0 baseline) into this branch.
