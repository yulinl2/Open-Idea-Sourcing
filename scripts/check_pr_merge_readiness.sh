#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

target="${1:-}"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required for this check."
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 (python3) is required for this check."
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

python3 "$(dirname "$0")/check_pr_merge_readiness.py" "$pr_json" "$checks_json"
