---
name: contrib main
description: "Create and switch to a fresh local copilot/local/* branch from origin/main. Use when you want explicit main-track branch mode from the slash palette."
argument-hint: "Optional task name, for example: fix parser timeout"
---
Set up a fresh local main-track branch for this repository.

Rules:
- This prompt is only for locally created branches.
- Always use the `copilot/local/` prefix.
- First run `git status --short` and `git branch --show-current`.
- If the current worktree is not clean, do not switch branches. Summarize the blocking files and ask the user whether they want to commit, stash, or handle it manually.
- Always base the new branch on `origin/main`.
- If a task name was supplied, convert it into a short lowercase kebab-case slug and use `copilot/local/<slug>`.
- If no task name was supplied, use a timestamp slug in the form `YYYYMMDD-HHMM`.
- If the target branch name already exists locally, append `-2`, `-3`, and so on until the name is unique.
- Create and switch in one command.

Examples:
- `/contrib main`
- `/contrib main fix parser timeout`
