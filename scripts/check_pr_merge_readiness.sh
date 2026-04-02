#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

target="${1:-}"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required for this check."
  exit 2
fi

view_args=(pr view --json number,title,url,isDraft,reviewDecision)
checks_args=(pr checks --required --json name,state,bucket,workflow,link)
if [[ -n "$target" ]]; then
  view_args+=("$target")
  checks_args+=("$target")
fi

if ! pr_json="$(gh "${view_args[@]}")"; then
  echo "Unable to load PR metadata. Pass a PR number/url/branch or run this on a PR branch."
  exit 2
fi

tmp_err="$(mktemp)"
set +e
checks_json="$(gh "${checks_args[@]}" 2>"$tmp_err")"
checks_rc=$?
set -e
checks_err="$(cat "$tmp_err")"
rm -f "$tmp_err"

if [[ $checks_rc -ne 0 && $checks_rc -ne 1 && $checks_rc -ne 8 ]]; then
  [[ -n "$checks_err" ]] && echo "$checks_err"
  echo "Unable to load required status checks. Failing closed."
  exit 2
fi

if [[ -z "$checks_json" || "$checks_json" == "[]" ]]; then
  [[ -n "$checks_err" ]] && echo "$checks_err"
  echo "No required checks were returned for this PR. Failing closed."
  exit 1
fi

python3 - <<'PY' "$pr_json" "$checks_json"
import json
import sys

pr = json.loads(sys.argv[1])
checks = json.loads(sys.argv[2])

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

sys.exit(1 if failed else 0)
PY
