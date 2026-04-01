# infra-base

Orphan branch - canonical source for the agent-track shared execution shell.

Track branches (agent-e2e, agent-linear, agent-reconstruct) cherry-pick
infra/ and .github/workflows/agent-review.yml from this branch.
They never merge back into main or infra-base.

## Contents

| Path | Purpose |
|------|---------|
| infra/ | Shared Python execution shell: RunContext, ReportWriter, ToolRegistry, search clients, PDF utils |
| PROJECT_INSTRUCTIONS_AGENT.md | Canonical agent-track charter |
| AGENT_TRACK_ROADMAP.md | Per-branch build sequences and human workflow |
| .github/workflows/agent-review.yml | Parallel CI workflow (cherry-picked into each track branch) |

## Cherry-picking into a track branch

From the track branch (e.g. agent-e2e):

    git cherry-pick <infra-base-commit-sha>
