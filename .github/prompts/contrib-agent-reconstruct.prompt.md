---
name: contrib agent-reconstruct
description: "Create or reuse the stable local worktree for agent-reconstruct. Use when you want to contribute to the reconstruction agent track from the slash palette."
---
Set up or reuse the stable local worktree for `agent-reconstruct`.

Rules:
- Do not switch the current workspace off its existing branch.
- Always use the worktree path `../Open-Idea-Sourcing-worktrees/agent-reconstruct`.
- Always fetch `origin/agent-reconstruct` before creating a worktree.
- If the worktree already exists and points at `agent-reconstruct`, reuse it and report the path.
- If the path exists but is not the expected git worktree, stop and ask before changing anything.
- Otherwise create it with `git worktree add -B agent-reconstruct ../Open-Idea-Sourcing-worktrees/agent-reconstruct origin/agent-reconstruct`.

Example:
- `/contrib agent-reconstruct`
