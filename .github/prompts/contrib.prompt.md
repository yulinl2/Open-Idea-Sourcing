---
name: contrib
description: "Route contribution setup to an existing supported target. Use for main, infra-base, agent-e2e, agent-linear, agent-reconstruct, or agent-reports. If the target is ambiguous or unsupported, ask a short clarifying question instead of guessing."
argument-hint: "Target branch, optionally followed by a task for main; for example: main fix parser timeout or agent-linear"
---
Set up the right local contribution target for this repository.

Rules:
- Supported targets are exactly `main`, `infra-base`, `agent-e2e`, `agent-linear`, `agent-reconstruct`, and `agent-reports`.
- If the first argument is not one of those exact target names, ask one short clarifying question instead of guessing.
- `main` means local main-track branch mode. It creates and switches to a fresh `copilot/local/*` branch rooted in `origin/main`.
- The agent-track targets mean stable local worktree mode. They create or reuse `../Open-Idea-Sourcing-worktrees/<target>` from `origin/<target>`.
- Do not silently interpret arbitrary text as a branch name.
- If the user picked `main`, any remaining text after `main` is the optional task name.
- If the user picked an agent-track target, ignore any extra freeform text and ask for clarification if it changes the intent.

Examples:
- `/contrib main`
- `/contrib main fix parser timeout`
- `/contrib agent-linear`


