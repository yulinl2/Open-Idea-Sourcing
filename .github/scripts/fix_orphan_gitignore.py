#!/usr/bin/env python3
"""
.github/scripts/fix_orphan_gitignore.py

One-shot script to write (or overwrite) the comprehensive .gitignore on all
existing orphan agent-track branches without recreating them from scratch.

Run this when orphan branches are missing the full .gitignore (e.g. after a
bootstrap that predated the ORPHAN_GITIGNORE template).

Usage:
    python3 .github/scripts/fix_orphan_gitignore.py

The script uses git worktrees so it never needs to abandon the current branch.
Each worktree is cleaned up on exit whether the run succeeds or fails.
"""
import contextlib
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

GITIGNORE_CONTENT = textwrap.dedent("""\
    __pycache__/
    *.pyc
    *.pyo
    .env
    .env.local
    checkpoints/
    reports/
    .pytest_cache/
    *.egg-info/
    dist/
    build/
    .venv/
    venv/
""")

ORPHAN_BRANCHES = [
    "infra-base",
    "agent-e2e",
    "agent-linear",
    "agent-reconstruct",
    "agent-reports",
]


def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, check=check, cwd=cwd)


def branch_exists_remote(branch: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", branch],
        capture_output=True,
    )
    return result.returncode == 0


@contextlib.contextmanager
def worktree(branch: str):
    """Context manager: adds a detached worktree for *branch*, cleans up on exit."""
    with tempfile.TemporaryDirectory(prefix=f"wt-{branch.replace('/', '-')}-") as tmpdir:
        run(["git", "worktree", "add", "--detach", tmpdir, f"origin/{branch}"])
        try:
            # Create (or reset) a local branch inside the worktree
            run(["git", "checkout", "-B", branch], cwd=tmpdir)
            yield Path(tmpdir)
        finally:
            run(["git", "worktree", "remove", "--force", tmpdir], check=False)


def fix_branch(branch: str) -> bool:
    if not branch_exists_remote(branch):
        print(f"  Branch '{branch}' not found on origin — skipping.")
        return False

    print(f"\n=== Fixing .gitignore on '{branch}' ===")
    with worktree(branch) as wt_path:
        gitignore_path = wt_path / ".gitignore"
        current = gitignore_path.read_text() if gitignore_path.exists() else ""
        if current == GITIGNORE_CONTENT:
            print(f"  .gitignore already up to date — nothing to do.")
            return False

        gitignore_path.write_text(GITIGNORE_CONTENT)
        run(["git", "add", ".gitignore"], cwd=str(wt_path))
        run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-m",
             f"{branch}: update .gitignore — add venv, pycache, build artifacts"],
            cwd=str(wt_path),
        )
        run(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], cwd=str(wt_path))
        print(f"  Updated '{branch}'.")
        return True


def main() -> None:
    updated = []
    for branch in ORPHAN_BRANCHES:
        if fix_branch(branch):
            updated.append(branch)

    print("\nDone.")
    if updated:
        print(f"Updated branches: {', '.join(updated)}")
    else:
        print("All branches were already up to date.")


if __name__ == "__main__":
    main()
