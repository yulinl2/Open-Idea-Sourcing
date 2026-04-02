---
name: contrib infra-base
description: "Create or reuse the stable local worktree for infra-base. Use when you want to contribute to the shared agent-track infrastructure branch from the slash palette."
---
Set up or reuse the stable local worktree for `infra-base`.

Rules:
- Do not switch the current workspace off its existing branch.
- Always use the worktree path `../Open-Idea-Sourcing-worktrees/infra-base`.
- Always fetch `origin/infra-base` before creating a worktree.
- If the worktree already exists and points at `infra-base`, reuse it and report the path.
- If the path exists but is not the expected git worktree, stop and ask before changing anything.
- Otherwise create it with `git worktree add -B infra-base ../Open-Idea-Sourcing-worktrees/infra-base origin/infra-base`.

Example:
- `/contrib infra-base`
