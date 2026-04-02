---
name: contrib agent-e2e
description: "Create or reuse the stable local worktree for agent-e2e. Use when you want to contribute to the end-to-end agent track from the slash palette."
---
Set up or reuse the stable local worktree for `agent-e2e`.

Rules:
- Do not switch the current workspace off its existing branch.
- Always use the worktree path `../Open-Idea-Sourcing-worktrees/agent-e2e`.
- Always fetch `origin/agent-e2e` before creating a worktree.
- If the worktree already exists and points at `agent-e2e`, reuse it and report the path.
- If the path exists but is not the expected git worktree, stop and ask before changing anything.
- Otherwise create it with `git worktree add -B agent-e2e ../Open-Idea-Sourcing-worktrees/agent-e2e origin/agent-e2e`.

Example:
- `/contrib agent-e2e`
