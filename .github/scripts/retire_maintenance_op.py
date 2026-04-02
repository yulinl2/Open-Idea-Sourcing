#!/usr/bin/env python3
"""
Retire a completed one-shot maintenance operation from agent-track-workflows.yml.

Usage:
    python3 .github/scripts/retire_maintenance_op.py --op fix-gitignore
    python3 .github/scripts/retire_maintenance_op.py --op sync-agent-review-workflow
    python3 .github/scripts/retire_maintenance_op.py --op my-new-op --no-push  # dry-run

What it does:
    1. Removes the operation name from the 'operation' input description.
    2. Removes the op's entry from the file-header comment block.
    3. Removes any workflow_dispatch inputs exclusively used by this operation.
    4. Extracts the comment block + job block and saves it as <op>.yml.bak
       in .github/workflows/ for historical reference.
    5. Removes the comment block + job block from agent-track-workflows.yml.
    6. Deletes the associated one-time script file (if listed in OP_SCRIPTS).
    7. Commits the change and pushes it to main (unless --no-push is given).

Lifecycle convention for maintenance operations in agent-track-workflows.yml:
    ADD:      Add a guarded job (if: github.event.inputs.operation == '<op>') with
              a final "Self-archive" step that calls this script.
    DISPATCH: Trigger once from the Actions UI with operation=<op>.
    RETIRE:   On success the self-archive step runs this script, removes the op
              from the YAML, deletes the associated script, and pushes to main —
              so it disappears from the UI with no dead code left behind.

To add a future maintenance operation, follow AGENT_INSTRUCTIONS.md §Maintenance ops.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

WORKFLOW_PATH = Path(".github/workflows/agent-track-workflows.yml")
WORKFLOWS_DIR = Path(".github/workflows")

# workflow_dispatch inputs that belong exclusively to a specific maintenance op.
# They are removed when the op is retired.  Key = op name, value = list of input keys.
OP_EXCLUSIVE_INPUTS: dict[str, list[str]] = {
    "sync-agent-review-workflow": ["branches", "dry_run"],
    "fix-gitignore": [],
}

# One-time script files associated with each op.  When the op retires, the
# script is deleted too so it doesn't linger as dead code on main.
# Set to None if the op has no associated script to delete.
OP_SCRIPTS: dict[str, str | None] = {
    "sync-agent-review-workflow": ".github/scripts/fix_orphan_agent_review.py",
    "fix-gitignore": ".github/scripts/fix_orphan_gitignore.py",
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

def retire_op(content: str, op: str) -> tuple[str, str]:
    """Return (updated YAML, extracted job block text) with all traces of *op* removed."""
    content = _remove_from_description(content, op)
    content = _remove_from_choice_options(content, op)
    content = _remove_header_comment_entry(content, op)
    exclusive = OP_EXCLUSIVE_INPUTS.get(op, [])
    if exclusive:
        content = _remove_exclusive_inputs(content, exclusive)
    job_block = _extract_job_block(content, op)
    content = _remove_job_block(content, op)
    return content, job_block


# ---------------------------------------------------------------------------
# Step-by-step helpers
# ---------------------------------------------------------------------------

def _remove_from_description(content: str, op: str) -> str:
    """Remove op name from the 'operation' input description string (legacy free-text style)."""
    for pat in [f", '{op}'", f"'{op}', ", f', "{op}"', f'"{op}", ']:
        content = content.replace(pat, "")
    return content


def _remove_from_choice_options(content: str, op: str) -> str:
    """Remove op from the 'operation' input's type: choice options list."""
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    in_operation_block = False
    in_options_list = False

    for line in lines:
        stripped = line.rstrip("\n\r")

        if re.match(r"^      operation:\s*$", stripped):
            in_operation_block = True
            in_options_list = False
            result.append(line)
            continue

        if in_operation_block:
            indent = len(stripped) - len(stripped.lstrip()) if stripped else float("inf")
            if stripped and indent < 8:
                # Left the operation block entirely.
                in_operation_block = False
                in_options_list = False
            elif re.match(r"^        options:\s*$", stripped):
                in_options_list = True
            elif in_options_list and re.match(r"^          - ", stripped):
                # Inside the options list — skip the line for the retiring op.
                if stripped.strip() == f"- {op}":
                    continue
            elif in_options_list and stripped and indent < 10:
                # A new property inside the operation block — end of options list.
                in_options_list = False

        result.append(line)

    return "".join(result)


def _remove_header_comment_entry(content: str, op: str) -> str:
    """Remove the '#   <op>  — ...' entry (possibly multi-line) from the file header."""
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    skipping = False
    for line in lines:
        if re.match(rf"^#   {re.escape(op)}\b", line):
            skipping = True
            continue
        if skipping:
            # Continuation lines have 4+ spaces after '#' (deeply indented).
            # Any other line (blank comment, section header) ends the skip.
            if re.match(r"^#    ", line):
                continue  # still a continuation — skip it
            skipping = False
        result.append(line)
    return "".join(result)


def _remove_exclusive_inputs(content: str, inputs_to_remove: list[str]) -> str:
    """Remove workflow_dispatch input blocks exclusively used by the retiring op."""
    norm = {x.replace("-", "_") for x in inputs_to_remove}
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^      ([\w-]+):\s*$", lines[i])
        if m and m.group(1).replace("-", "_") in norm:
            # Skip this input block: advance until the next 6-space input or shallower.
            i += 1
            while i < len(lines):
                if not lines[i].strip():
                    i += 1
                    continue
                if len(lines[i]) - len(lines[i].lstrip()) <= 6:
                    break  # next sibling input (or end of inputs)
                i += 1
        else:
            result.append(lines[i])
            i += 1
    return "".join(result)


def _extract_job_block(content: str, op: str) -> str:
    """Extract the comment block + job block for *op* and return it as text."""
    lines = content.splitlines(keepends=True)
    # Find the job start line.
    job_start = None
    for idx, line in enumerate(lines):
        if re.match(rf"^  {re.escape(op)}:\s*$", line):
            job_start = idx
            break
    if job_start is None:
        return ""
    # Walk backwards to include the preceding comment/separator block.
    comment_start = job_start
    i = job_start - 1
    while i >= 0 and (not lines[i].strip() or lines[i].strip().startswith("#")):
        comment_start = i
        i -= 1
    # Walk forward to include the full job body.
    job_end = job_start + 1
    while job_end < len(lines):
        if not lines[job_end].strip():
            # Blank — peek ahead for next non-blank.
            k = job_end + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines) and len(lines[k]) - len(lines[k].lstrip()) <= 2:
                break
            job_end += 1
            continue
        if len(lines[job_end]) - len(lines[job_end].lstrip()) <= 2:
            break
        job_end += 1
    return "".join(lines[comment_start:job_end])


def _remove_job_block(content: str, op: str) -> str:
    """Remove the 2-space-indent job block plus its preceding comment block."""
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    i = 0
    while i < len(lines):
        if re.match(rf"^  {re.escape(op)}:\s*$", lines[i]):
            # Walk *back* in result to peel off the preceding comment/blank lines.
            while result and (not result[-1].strip() or result[-1].strip().startswith("#")):
                result.pop()
            # Skip *forward* through the job block.
            i += 1
            while i < len(lines):
                if not lines[i].strip():
                    # Blank line — peek ahead to see whether the next non-blank
                    # line is a sibling job/comment (indent ≤ 2 → stop consuming).
                    k = i + 1
                    while k < len(lines) and not lines[k].strip():
                        k += 1
                    if k < len(lines) and len(lines[k]) - len(lines[k].lstrip()) <= 2:
                        break  # leave the blank line for the outer loop
                    i += 1
                    continue
                if len(lines[i]) - len(lines[i].lstrip()) <= 2:
                    break  # sibling job
                i += 1
            continue  # outer loop will process lines[i] (blank or next job)
        result.append(lines[i])
        i += 1
    return "".join(result)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retire a completed maintenance operation from agent-track-workflows.yml.",
    )
    parser.add_argument("--op", required=True, help="Operation name, e.g. fix-gitignore")
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Edit file but skip the git commit/push (useful for testing).",
    )
    args = parser.parse_args()

    op = args.op
    if op not in OP_EXCLUSIVE_INPUTS:
        print(
            f"Unknown operation '{op}'. Add it to OP_EXCLUSIVE_INPUTS first.",
            file=sys.stderr,
        )
        sys.exit(1)

    original = WORKFLOW_PATH.read_text()
    updated, job_block = retire_op(original, op)

    if updated == original:
        print(f"No changes — '{op}' may already be retired or not present.")
        return

    WORKFLOW_PATH.write_text(updated)
    print(f"Retired '{op}' from {WORKFLOW_PATH}")

    # Save the extracted job block as a .yml.bak for historical reference.
    bak_path = WORKFLOWS_DIR / f"{op}.yml.bak"
    if job_block:
        bak_header = (
            f"# Auto-archived maintenance op: {op}\n"
            f"# Originally inlined in agent-track-workflows.yml\n"
            f"# This is a historical record only — this job will never run.\n\n"
        )
        bak_path.write_text(bak_header + job_block)
        print(f"Saved archived job block: {bak_path}")

    # Delete the associated one-time script (if any) so it doesn't linger as dead code.
    script_path_str = OP_SCRIPTS.get(op)
    script_path = Path(script_path_str) if script_path_str else None
    if script_path and script_path.exists():
        script_path.unlink()
        print(f"Deleted associated script: {script_path}")

    if not args.no_push:
        run(["git", "add", str(WORKFLOW_PATH)])
        if job_block and bak_path.exists():
            run(["git", "add", str(bak_path)])
        if script_path and not script_path.exists():
            run(["git", "rm", "--cached", "--ignore-unmatch", str(script_path)])
        run(
            [
                "git",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-m",
                f"chore: auto-retire {op} maintenance op (completed successfully)",
            ]
        )
        run(["git", "push", "origin", "HEAD:main"])
        print("Committed and pushed to main.")
    else:
        print("--no-push: file updated in place, no commit made.")


if __name__ == "__main__":
    main()
