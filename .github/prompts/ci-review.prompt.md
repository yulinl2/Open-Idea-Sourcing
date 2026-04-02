---
name: ci-review
description: "Dispatch agent-review.yml directly. Use this for recurring paper reviews from the slash palette."
agent: "Agent Track Dispatcher"
argument-hint: "Optional fields, for example: track=all paper_url=https://arxiv.org/abs/2006.06138 model=gpt-5.4"
---
Dispatch `.github/workflows/agent-review.yml` for this repository.

Rules:
- Always run `gh workflow run agent-review.yml --ref main`.
- If track is not provided, default to `track=all`.
- Accept optional `track=all|e2e|linear|reconstruct`, optional `paper_url=...`, and optional `model=...`.
- If the user provides unsupported fields, ask one short clarifying question.
- After dispatching, report the exact command used and one follow-up command to inspect the latest run.

Examples:
- `/ci-review`
- `/ci-review track=all paper_url=https://arxiv.org/abs/2006.06138 model=gpt-5.4`
