# agent-reports

Orphan branch that accumulates published agent-track reports.

## Directory layout

    agent-e2e/<paper_id>/report.md
    agent-linear/<paper_id>/report.md
    agent-reconstruct/<paper_id>/report.md

Reports are published here automatically by the agent-review.yml workflow
after each successful run. Each report.md is self-contained with YAML
front-matter fields (track, impl_id, model, git_commit, final_verdict,
confidence, etc.) enabling cross-run, cross-branch comparison.

## Cross-track comparison

    git checkout agent-reports
    grep "final_verdict:" agent-*/2006.06138/report.md
    grep "confidence:" agent-*/2006.06138/report.md
