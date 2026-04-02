# Agent Instructions

Rules for AI coding agents working in this repository. These exist because the
same mistakes have recurred across multiple PR sessions and are expensive to
undo. Read this before touching any file.

---

## 1. Branch hygiene — the single most important rule

**Every feature branch that targets `main` MUST be rooted in `main`.**

At the very start of any session, verify and fix your branch base:

```bash
# Confirm you are standing on a commit reachable from origin/main
git merge-base --is-ancestor origin/main HEAD \
  || git reset --hard origin/main   # reset if not reachable
```

Concretely:
- If the sandbox gives you a branch whose history contains infra-base, agent-e2e,
  agent-linear, agent-reconstruct, or agent-reports commits, **reset to origin/main
  immediately** before making any changes.
- Never use `git merge --allow-unrelated-histories` as a workaround to paper over
  an orphan branch accidentally mixed into a main-track PR. It pollutes the history
  and creates PRs that cannot be cleanly reviewed or merged.

---

## 2. Orphan branches are isolated — do not mix them with main

This repo has two categories of branches that must stay completely separate:

| Category | Branches | Purpose |
|---|---|---|
| **Main-track** | `main`, `copilot/*` PRs | Product code, CI workflows |
| **Orphan agent-track** | `infra-base`, `agent-e2e`, `agent-linear`, `agent-reconstruct`, `agent-reports` | Agent execution shells, reports accumulation |

Rules:
- Never base a PR on an orphan branch unless you intend to merge *into* that orphan branch.
- Never cherry-pick from infra-base into main or vice-versa unless the change is explicitly about keeping the two in sync.
- When working on a `copilot/*` PR branch, confirm the PR's base is `main`:
  ```bash
  gh pr view --json baseRefName   # must print "main"
  ```

---

## 3. `.venv` and other generated artifacts — never commit them

The `copilot-setup-steps.yml` workflow creates a `.venv/` directory during
sandbox initialisation. This directory must never be committed.

Rules:
- **Never run `git add .`** (adds everything, including `.venv`, `__pycache__`,
  `*.pyc`, temp files, etc.).  
  Instead, stage files explicitly:
  ```bash
  git add path/to/specific/file.py
  git add path/to/another/file.py
  ```
- **Always run `git status` before committing** to confirm no unintended files are
  staged.
- **Never use unquoted shell redirects** for version specifiers in pip:
  ```bash
  # WRONG — >=6.0 is a shell redirect; creates a file named =6.0
  pip install pyyaml>=6.0
  # CORRECT — quote the specifier
  pip install "pyyaml>=6.0"
  ```

The `.gitignore` on main already excludes `.venv/`, `venv/`, `__pycache__/`,
`*.pyc`, `.env`, and `checkpoints/`. Orphan branches carry their own `.gitignore`
(maintained by `scripts/bootstrap_agent_branches.py`); do not remove entries
from it.

---

## 4. Git commit signing

The sandbox may have GPG signing configured. Always disable it when committing:

```bash
git -c commit.gpgsign=false commit -m "your message"
```

---

## 5. Pushing changes

You cannot `git push` directly — the remote rejects it with 403.  
Use `report_progress` tool to commit and push to the PR branch.

Before calling `report_progress`, confirm that:
1. `git status` shows only intentional staged/modified files.
2. `git log --oneline -5` shows the expected linear history rooted in `origin/main`.

---

## 6. PR creation and base branch

- Always set PR base to `main` (the default).
- If a PR was accidentally created targeting an orphan branch, close it and
  create a new one — do not attempt to rebase across unrelated histories.
- Use `gh pr view --json baseRefName,headRefName` to verify before pushing.

---

## 7. Workflow file discipline

- The stable filename for agent-track fan-out is
  `.github/workflows/agent-track-workflows.yml` — edit in-place, never rename
  or duplicate it.
- When running `gh workflow run`, always pass `--ref main` to avoid a GraphQL
  lookup for the default branch (which `GITHUB_TOKEN` cannot perform on push
  events).
- Stale workflow versions are retired by renaming to `*.yml.bak` (not `.yml`),
  keeping them out of GitHub Actions while preserving local history.

---

## 8. Workflow dispatch inputs — use dropdowns whenever possible

For `workflow_dispatch` inputs with a fixed set of valid values, always use
`type: choice` (dropdown) or `type: boolean` (checkbox) instead of a free-text
`type: string`. This prevents typos, makes valid options visible in the UI, and
avoids broken runs from invalid input.

```yaml
# CORRECT — dropdown for an enumerated string value
on:
  workflow_dispatch:
    inputs:
      operation:
        description: "Operation to run"
        required: false
        default: "review"
        type: choice
        options:
          - review
          - fix-gitignore
          - sync-agent-review-workflow

# CORRECT — checkbox for a boolean flag
      dry_run:
        description: "Dry run (show changes, no push)"
        required: false
        default: false
        type: boolean
```

Rules:
- Use `type: choice` for any input whose valid values form a small, known set
  (operation names, track names, output formats, etc.).
- Use `type: boolean` for on/off flags; omit the `"true"/"false"` string idiom.
- When using `type: choice`, the options are visible in the dropdown — you do not
  need to enumerate them in the `description:` string.
- Free-text inputs (`type: string`, the default) are reserved for open-ended
  values like URLs, arbitrary identifiers, or space-separated branch lists.

---

## 9. Maintenance operations — lifecycle convention

One-shot maintenance operations (e.g., fix a config on all orphan branches) live
as guarded jobs inside `agent-track-workflows.yml`.  **Never add a new standalone
`.yml` workflow file** — always inline into the existing unified entry-point.

### Lifecycle: ADD → DISPATCH → AUTO-RETIRE

```
1. ADD      Add a guarded job to agent-track-workflows.yml:
               if: github.event.inputs.operation == '<op-name>'
            • Add the op name to the `operation` input description.
            • Add the op entry to the file-header comment block.
            • If the op needs extra inputs (e.g., branch list), add them under
              workflow_dispatch.inputs and register them in
              .github/scripts/retire_maintenance_op.py → OP_EXCLUSIVE_INPUTS.
            • Add a final "Self-archive" step at the end of the job:
                - name: Self-archive this operation
                  if: success()
                  run: python3 .github/scripts/retire_maintenance_op.py --op <op-name>

2. DISPATCH Trigger once from the Actions UI:
               Actions → Agent track workflows → Run workflow → operation=<op>

3. AUTO-RETIRE On success the Self-archive step runs retire_maintenance_op.py,
            which:
            a. Extracts the job block and saves it as
               .github/workflows/<op>.yml.bak
               for historical reference (inert — GitHub Actions ignores non-.yml).
            b. Strips the op from agent-track-workflows.yml.
            c. Deletes the associated one-time script (from OP_SCRIPTS).
            d. Pushes the change to main.
            The op disappears from the Run-workflow dropdown automatically —
            no follow-up PR needed.
```

### Why `.github/workflows/**` is in the push trigger's `paths-ignore`

The push trigger's `paths-ignore` includes `.github/workflows/**` so that when
`retire_maintenance_op.py` pushes the cleaned-up workflow YAML to main, it does
not trigger another fan-out review run.  Code changes (the things that should
trigger reviews) do not live under `.github/workflows/`, so this exclusion is
safe.

### Registering future exclusive inputs

When your new op needs custom inputs (like `branches`), add them to the
`OP_EXCLUSIVE_INPUTS` dict in `.github/scripts/retire_maintenance_op.py`:

```python
OP_EXCLUSIVE_INPUTS: dict[str, list[str]] = {
  "sync-agent-review-workflow": ["branches", "dry_run"],
    "fix-gitignore": [],
    "my-new-op": ["my-extra-input"],   # ← add here
}
```

Also register the associated script (if any) in `OP_SCRIPTS` so it is deleted
on retire.  Set to `None` if there is no associated script:

```python
OP_SCRIPTS: dict[str, str | None] = {
  "sync-agent-review-workflow": ".github/scripts/fix_orphan_agent_review.py",
    "fix-gitignore": ".github/scripts/fix_orphan_gitignore.py",
    "my-new-op": ".github/scripts/my_new_op.py",   # ← add here, or None
}
```

The retire script uses these dicts to know which `workflow_dispatch` input blocks
to remove and which script file to delete when the op is retired.

All orphan branches must have a comprehensive `.gitignore`. The template is
maintained in `scripts/bootstrap_agent_branches.py` (`ORPHAN_GITIGNORE`
constant). When re-bootstrapping branches (`--no-skip-existing`), the new
`.gitignore` is written automatically.

To manually propagate a `.gitignore` fix to all existing orphan branches:

```bash
python3 .github/scripts/fix_orphan_gitignore.py
```

(See that script for details.)
