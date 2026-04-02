---
name: ci-one-off
description: "Dispatch agent-track-workflows.yml for one-off maintenance or patch operations. Use for fix-gitignore, sync-agent-review-workflow, housekeeping-reports, or any non-recurring dispatch."
agent: "Agent Track Dispatcher"
argument-hint: "Operation and optional fields, for example: fix-gitignore or sync-agent-review-workflow dry_run=true"
---
Dispatch `.github/workflows/agent-track-workflows.yml` for this repository.

Rules:
- Always run `gh workflow run agent-track-workflows.yml --ref main`.
- Always include `--field operation=<op>`.
- Supported operations: `review`, `fix-gitignore`, `sync-agent-review-workflow`, `housekeeping-reports`.
- For `review`, accept optional `paper_url=...` and `model=...`.
- For `sync-agent-review-workflow`, accept optional `branches='...'` and `dry_run=true|false`.
- For `housekeeping-reports`, accept optional `target_branch=...`.
- If the request does not clearly specify an operation, ask a single short clarifying question.

Examples:
- `/ci-one-off fix-gitignore`
- `/ci-one-off sync-agent-review-workflow branches='infra-base agent-e2e' dry_run=true`
- `/ci-one-off housekeeping-reports target_branch=agent-reports`
