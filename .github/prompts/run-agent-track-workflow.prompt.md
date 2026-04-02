---
name: Run Agent Track Workflow
description: "Dispatch agent-track-workflows.yml from chat in one step. Use for review, fix-gitignore, sync-agent-review-workflow, or housekeeping-reports."
agent: "Agent Track Dispatcher"
argument-hint: "Operation and optional fields, for example: fix-gitignore"
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