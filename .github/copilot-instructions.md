# Copilot Coding Agent Instructions

These rules apply to every Copilot coding agent session in this repository.
See `AGENT_INSTRUCTIONS.md` for the full rationale behind each rule.

---

## Branch hygiene — check this FIRST on every session

```bash
# Your working branch must be rooted in the correct base.
# For PRs targeting main:
git merge-base --is-ancestor origin/main HEAD \
  || git reset --hard origin/main

# For PRs targeting infra-base:
git merge-base --is-ancestor origin/infra-base HEAD \
  || git reset --hard origin/infra-base
```

**Never start work on an orphan branch** (`infra-base`, `agent-e2e`, `agent-linear`,
`agent-reconstruct`, `agent-reports`) when the PR targets `main`, or vice-versa.
If the sandbox gives you a branch with the wrong history, reset immediately.

---

## Staging and committing — never use `git add .`

```bash
# WRONG — stages .venv/, __pycache__/, *.pyc, and everything else
git add .

# CORRECT — stage only the files you intentionally changed
git add path/to/file1.py path/to/file2.yml
git status   # verify before every commit
git -c commit.gpgsign=false commit -m "your message"
```

---

## Shell quoting — always quote pip version specifiers

```bash
# WRONG — >=6.0 is a shell redirect; creates a file named =6.0
pip install pyyaml>=6.0

# CORRECT
pip install "pyyaml>=6.0"
```

---

## GitHub Actions workflow dispatch

Always pass `--ref main` when dispatching `agent-review.yml` via `gh workflow run`:

```yaml
gh workflow run agent-review.yml \
  --repo "${{ github.repository }}" \
  --ref main \
  --field paper_url="$PAPER_URL" \
  --field track="$TRACK"
```

Without `--ref`, `gh` tries a GraphQL default-branch lookup that `GITHUB_TOKEN`
cannot perform on push events (403 error).

---

## Branch architecture — keep these completely separate

| Branch type | Examples | Target of PRs |
|---|---|---|
| Main-track | `main`, `copilot/*` | `main` |
| Orphan agent-track | `infra-base`, `agent-e2e`, `agent-linear`, `agent-reconstruct`, `agent-reports` | their own base only |

- `agent-review.yml` push trigger lives on **infra-base / agent-\*** — NOT on main.
- `agent-track-workflows.yml` lives on **main** — NOT on infra-base.
- Never cherry-pick or merge across these two groups without explicit intent.

---

## Pushing changes

Use `report_progress` tool — do not run `git push` directly.
Before calling it, confirm `git log --oneline -5` shows the expected clean history.

---

## Memory hygiene — what to store vs. what NOT to store

**Store** (permanent, branch-agnostic rules and conventions):
- Coding conventions, naming patterns, API contracts
- Architectural rules (e.g. "push trigger lives on infra-base, not main")
- Command recipes (how to build, test, lint)

**Never store** (current status — goes stale immediately with parallel branches):
- "Branch X now has files A, B, C" — file contents change every commit
- "Current PR is at commit Y" — meaningless to the next session
- "Tests pass as of today" — may be false tomorrow

When calling `store_memory`, ask: *would this fact still be true in 3 months on a different branch?* If no, don't store it.
