#!/usr/bin/env python3
"""
Reorganize flat report files on a target branch into versioned subdirectories.

Each Novelty Evaluation report file is named:
    <paper-slug>_<YYYY-MM-DDTHHMMSS>.md

and contains a ``| Code version | X.Y.Z |`` table row in its Run Metadata
section.  This script moves every flat file at the branch root into:
    <paper-slug>/v<code-version>/

so that reports are grouped by paper and package version.

Usage
-----
    python3 .github/scripts/reorganize_reports.py --branch agent-reports
    python3 .github/scripts/reorganize_reports.py --branch agent-reports --dry-run
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

WORKTREE_PATH = Path("/tmp/reports-housekeeping")

# Pattern for the timestamp suffix that suggest_filename appends.
_TIMESTAMP_RE = re.compile(r"^(.+?)_(\d{4}-\d{2}-\d{2}T\d{6})$")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _paper_slug(stem: str) -> str:
    """Strip the trailing timestamp from a report file stem.

    ``Conformal_Inference_of_Counterfactuals_and_Individual_Treatm_2026-03-26T000800``
    → ``Conformal_Inference_of_Counterfactuals_and_Individual_Treatm``
    """
    m = _TIMESTAMP_RE.match(stem)
    return m.group(1) if m else stem


def _parse_version(content: str) -> str:
    """Return the Code version value from a report's Run Metadata table row."""
    m = re.search(r"\|\s*Code version\s*\|\s*([^|\n]+?)\s*\|", content)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def reorganize(branch: str, *, dry_run: bool = False) -> int:
    """Reorganize flat report files on *branch*.

    Returns the number of files moved (or that would have been moved for
    a dry run).
    """
    check = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", branch],
        capture_output=True,
    )
    if check.returncode != 0:
        print(
            f"Branch '{branch}' not found on origin. Nothing to do.",
            file=sys.stderr,
        )
        return 0

    subprocess.run(["git", "fetch", "origin", branch], check=True)

    if WORKTREE_PATH.exists():
        shutil.rmtree(WORKTREE_PATH)

    subprocess.run(
        ["git", "worktree", "add", str(WORKTREE_PATH), f"origin/{branch}"],
        check=True,
    )

    try:
        return _reorganize_in_worktree(branch, dry_run=dry_run)
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(WORKTREE_PATH)],
            check=True,
        )


def _reorganize_in_worktree(branch: str, *, dry_run: bool) -> int:
    flat_files = sorted(p for p in WORKTREE_PATH.glob("*.md") if p.is_file())

    if not flat_files:
        print(f"No flat .md files found on '{branch}'. Nothing to do.")
        return 0

    moves: list[tuple[Path, Path]] = []
    skipped = 0

    for src in flat_files:
        slug = _paper_slug(src.stem)
        content = src.read_text(encoding="utf-8", errors="replace")
        version = _parse_version(content)

        if not version:
            print(f"  SKIP {src.name}: no 'Code version' field found")
            skipped += 1
            continue

        dest_dir = WORKTREE_PATH / slug / f"v{version}"
        dest_file = dest_dir / src.name

        if dest_file.exists():
            print(f"  SKIP {src.name}: already exists at {dest_file.relative_to(WORKTREE_PATH)}")
            skipped += 1
            continue

        print(f"  {'WOULD MOVE' if dry_run else 'MOVE'} {src.name}")
        print(f"    → {dest_dir.relative_to(WORKTREE_PATH)}/")
        moves.append((src, dest_file))

    if not moves:
        print(f"No files need moving on '{branch}' ({skipped} skipped).")
        return 0

    if dry_run:
        print(f"\nDry run: {len(moves)} file(s) would be moved, {skipped} skipped.")
        return len(moves)

    for src, dest in moves:
        dest.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dest)

    subprocess.run(["git", "add", "-A"], check=True, cwd=WORKTREE_PATH)

    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=WORKTREE_PATH
    )
    if status.returncode == 0:
        print("Nothing staged — all moves already reflected in the index?")
        return len(moves)

    subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            f"chore: reorganize {len(moves)} flat reports into versioned subdirs",
        ],
        check=True,
        cwd=WORKTREE_PATH,
    )
    subprocess.run(
        ["git", "push", "origin", f"HEAD:{branch}"],
        check=True,
        cwd=WORKTREE_PATH,
    )
    print(f"\nMoved {len(moves)} file(s) and pushed to '{branch}'.")
    return len(moves)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reorganize flat .md report files on a branch into versioned subdirs."
    )
    parser.add_argument(
        "--branch",
        default="agent-reports",
        help="Target branch (default: agent-reports)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be moved without making any changes.",
    )
    args = parser.parse_args()
    count = reorganize(args.branch, dry_run=args.dry_run)
    sys.exit(0 if count >= 0 else 1)


if __name__ == "__main__":
    main()
