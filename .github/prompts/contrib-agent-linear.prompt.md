---
name: contrib agent-linear
description: "Create or reuse the stable local worktree for agent-linear. Use when you want to contribute to the staged linear agent track from the slash palette."
---
Set up or reuse the stable local worktree for `agent-linear`.

Rules:
- Do not switch the current workspace off its existing branch.
- Always use the worktree path `../Open-Idea-Sourcing-worktrees/agent-linear`.
- Always fetch `origin/agent-linear` before creating a worktree.
- If the worktree already exists and points at `agent-linear`, reuse it and report the path.
- If the path exists but is not the expected git worktree, stop and ask before changing anything.
- Otherwise create it with `git worktree add -B agent-linear ../Open-Idea-Sourcing-worktrees/agent-linear origin/agent-linear`.

Example:
- `/contrib agent-linear`
