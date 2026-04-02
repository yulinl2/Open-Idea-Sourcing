---
name: ci-review
description: "Dispatch agent-track-workflows.yml with operation=review. Use this when you want the paper review action from the slash palette."
agent: "Agent Track Dispatcher"
argument-hint: "Optional fields, for example: paper_url=https://arxiv.org/abs/2006.06138 model=gpt-5.4"
---
Dispatch `.github/workflows/agent-track-workflows.yml` for this repository.

Rules:
- Always run `gh workflow run agent-track-workflows.yml --ref main --field operation=review`.
- Accept optional `paper_url=...` and optional `model=...`.
- If the user provides unsupported fields, ask one short clarifying question.
- After dispatching, report the exact command used and one follow-up command to inspect the latest run.

Examples:
- `/ci-review`
- `/ci-review paper_url=https://arxiv.org/abs/2006.06138 model=gpt-5.4`
