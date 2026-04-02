#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

chmod +x scripts/check_workflow_guardrails.sh scripts/check_staged_guardrails.sh .githooks/pre-commit .githooks/pre-push
git config core.hooksPath .githooks

echo "Installed local git hooks using core.hooksPath=.githooks"
echo "Hooks enabled: pre-commit, pre-push"
