---
name: contrib agent-reports
description: "Create or reuse the stable local worktree for agent-reports. Use when you want to contribute to the reports branch from the slash palette."
---
Set up or reuse the stable local worktree for `agent-reports`.

Rules:
- Do not switch the current workspace off its existing branch.
- Always use the worktree path `../Open-Idea-Sourcing-worktrees/agent-reports`.
- Always fetch `origin/agent-reports` before creating a worktree.
- If the worktree already exists and points at `agent-reports`, reuse it and report the path.
- If the path exists but is not the expected git worktree, stop and ask before changing anything.
- Otherwise create it with `git worktree add -B agent-reports ../Open-Idea-Sourcing-worktrees/agent-reports origin/agent-reports`.

Example:
- `/contrib agent-reports`
