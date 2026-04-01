#!/usr/bin/env python3
"""
scripts/propagate_agent_impls.py

Propagates the full agent implementations from infra-base (agent_impls/)
to each agent-track branch. Run this after merging the clean-up PR into
infra-base.

This script:
1. For each track (e2e, linear, reconstruct):
   a. Checks out the agent-<track> branch (or fetches it from origin)
   b. Copies the implementation files from agent_impls/<track>/
   c. Also copies data/, requirements.txt, pytest.ini, tests/
   d. Commits and pushes

Usage (from the workflow checkout directory, or a full clone):
    python3 scripts/propagate_agent_impls.py [--dry-run] [--tracks e2e linear reconstruct]

Requires a clean git state and push access to origin.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


def run(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, check=check, capture_output=capture, text=True)


def get_current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def branch_exists_remote(branch: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", branch],
        capture_output=True,
    )
    return result.returncode == 0


def copy_tree(src: Path, dst: Path) -> None:
    """Copy src into dst, creating dst if needed."""
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    elif src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


TRACK_CONFIG = {
    "e2e": {
        "branch": "agent-e2e",
        "impl_dir": "agent_impls/e2e",
        "impl_id": "e2e_v1_0_0",
        "description": "end-to-end autonomous baseline",
    },
    "linear": {
        "branch": "agent-linear",
        "impl_dir": "agent_impls/linear",
        "impl_id": "linear_v1_0_0",
        "description": "6-stage checkpointed pipeline",
    },
    "reconstruct": {
        "branch": "agent-reconstruct",
        "impl_dir": "agent_impls/reconstruct",
        "impl_id": "reconstruct_v1_0_0",
        "description": "teacher-student reconstruction track",
    },
}

# Files from infra-base to copy to each agent branch
SHARED_FILES = [
    "data/",
    "requirements.txt",
    "pytest.ini",
    "tests/",
    "infra/",
    ".github/workflows/agent-review.yml",
]


def propagate_track(track: str, config: dict, repo_root: Path, dry_run: bool) -> bool:
    """Propagate the implementation for one track. Returns True on success."""
    branch = config["branch"]
    impl_dir = repo_root / config["impl_dir"]

    if not impl_dir.exists():
        print(f"  WARNING: impl dir {impl_dir} not found — skipping {track}")
        return False

    print(f"\n=== Propagating {track} → {branch} ===")

    if not branch_exists_remote(branch):
        print(f"  WARNING: Remote branch '{branch}' does not exist — skipping")
        return False

    # Use a worktree to avoid disturbing the current checkout
    worktree_path = Path("/tmp") / f"propagate_{branch.replace('/', '_')}"
    if worktree_path.exists():
        shutil.rmtree(worktree_path)

    try:
        # Fetch and add worktree
        run(["git", "fetch", "origin", branch])
        run(["git", "worktree", "add", str(worktree_path), f"origin/{branch}"])
        run(["git", "-C", str(worktree_path), "checkout", "-b", branch])

        # Copy shared files
        for src_rel in SHARED_FILES:
            src = repo_root / src_rel.rstrip("/")
            dst_name = src_rel.rstrip("/").split("/")[-1] if "/" in src_rel else src_rel
            dst = worktree_path / src_rel.rstrip("/")
            if src.exists():
                print(f"  Copying {src_rel} → {branch}/{dst.relative_to(worktree_path)}")
                if dst.exists():
                    if dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        dst.unlink()
                copy_tree(src, dst)
            else:
                print(f"  SKIP (not found): {src_rel}")

        # Copy agent implementation files
        for src_file in impl_dir.iterdir():
            dst_path = worktree_path / src_file.name
            print(f"  Copying {src_file.relative_to(repo_root)} → {branch}/{src_file.name}")
            if dst_path.exists():
                if dst_path.is_dir():
                    shutil.rmtree(dst_path)
                else:
                    dst_path.unlink()
            copy_tree(src_file, dst_path)

        # Add .gitignore for checkpoints if not present
        gitignore_path = worktree_path / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text("checkpoints/\n__pycache__/\n*.pyc\n.env\n")
        elif "checkpoints/" not in gitignore_path.read_text():
            with open(gitignore_path, "a") as f:
                f.write("\ncheckpoints/\n")

        # Check if there are any changes
        result = run(
            ["git", "-C", str(worktree_path), "status", "--porcelain"],
            capture=True,
        )
        if not result.stdout.strip():
            print(f"  No changes to commit for {branch}")
            return True

        if dry_run:
            print(f"  [DRY RUN] Would commit and push to {branch}:")
            print(result.stdout)
            return True

        # Commit
        run(["git", "-C", str(worktree_path), "add", "."])
        run([
            "git", "-C", str(worktree_path), "commit",
            "-m", f"agent-{track}: v1 implementation ({config['impl_id']}), data/, tests/",
        ])
        # Push
        run(["git", "-C", str(worktree_path), "push", "origin",
             f"HEAD:refs/heads/{branch}"])
        print(f"  Successfully propagated {track} → {branch}")
        return True

    except subprocess.CalledProcessError as exc:
        print(f"  ERROR propagating {track}: {exc}")
        return False
    finally:
        # Remove worktree
        try:
            run(["git", "worktree", "remove", str(worktree_path), "--force"], check=False)
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Propagate agent implementations from infra-base to agent branches."
    )
    parser.add_argument(
        "--tracks", nargs="*", choices=["e2e", "linear", "reconstruct"],
        default=["e2e", "linear", "reconstruct"],
        help="Which tracks to propagate (default: all)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without pushing",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent

    results = {}
    for track in args.tracks:
        config = TRACK_CONFIG[track]
        ok = propagate_track(track, config, repo_root, args.dry_run)
        results[track] = ok

    print("\n=== Propagation summary ===")
    for track, ok in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {track} → {TRACK_CONFIG[track]['branch']}")

    if not all(results.values()):
        sys.exit(1)
    print("\nDone. Run the agent-review workflow to trigger CI on each track.")


if __name__ == "__main__":
    main()
