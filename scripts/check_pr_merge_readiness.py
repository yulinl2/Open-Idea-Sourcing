"""Fail-closed PR merge-readiness evaluator.

Called by scripts/check_pr_merge_readiness.sh with two JSON arguments:
  argv[1]: gh pr view JSON (number, title, url, isDraft, reviewDecision)
  argv[2]: gh pr checks --required JSON (list of check objects with bucket field)

Exit codes:
  0 — all required checks green, PR not a draft, no CHANGES_REQUESTED
  1 — one or more blockers found
"""

from __future__ import annotations

import json
import sys


def evaluate_merge_readiness(pr: dict, checks: list[dict]) -> bool:
    """Evaluate merge readiness for a PR given its metadata and required checks.

    Prints a human-readable summary and returns True if the PR is blocked,
    False if it is ready to merge.
    """
    print(f"PR #{pr['number']}: {pr['title']}")
    print(pr["url"])

    failed = False

    if pr.get("isDraft"):
        print("- BLOCKED: PR is still a draft.")
        failed = True

    if pr.get("reviewDecision") == "CHANGES_REQUESTED":
        print("- BLOCKED: review decision is CHANGES_REQUESTED.")
        failed = True

    blocking_checks = [c for c in checks if c.get("bucket") != "pass"]

    if blocking_checks:
        print("- BLOCKED: required checks not all green:")
        for c in blocking_checks:
            workflow = c.get("workflow") or "(no workflow)"
            name = c.get("name") or "(unnamed check)"
            state = c.get("state") or "UNKNOWN"
            bucket = c.get("bucket") or "unknown"
            link = c.get("link") or ""
            print(f"  * [{bucket}] {workflow} :: {name} ({state}) {link}")
        failed = True

    if not blocking_checks and not failed:
        print("- OK: all required checks are green.")

    return failed


if __name__ == "__main__":
    pr = json.loads(sys.argv[1])
    checks = json.loads(sys.argv[2])
    failed = evaluate_merge_readiness(pr, checks)
    sys.exit(1 if failed else 0)
