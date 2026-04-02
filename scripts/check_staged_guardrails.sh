#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

bad=0

staged_files=()
while IFS= read -r f; do
  staged_files+=("$f")
done < <(git diff --cached --name-only --diff-filter=ACMR)

if [[ ${#staged_files[@]} -eq 0 ]]; then
  exit 0
fi

for file in "${staged_files[@]}"; do
  case "$file" in
    .venv/*|venv/*|__pycache__/*|*.pyc|*.pyo|.pytest_cache/*|dist/*|build/*)
      echo "$file: generated artifact is staged; unstage it before committing."
      bad=1
      ;;
    =*)
      echo "$file: suspicious shell-redirect artifact is staged; remove it before committing."
      bad=1
      ;;
  esac
done

for file in "${staged_files[@]}"; do
  case "$file" in
    .github/workflows/*.yml|.github/scripts/*|scripts/*|README.md|docs/*.md|.github/*.md)
      content="$(git show ":$file" 2>/dev/null || true)"

      if printf '%s\n' "$content" | grep -Eq 'gh[[:space:]]+workflow[[:space:]]+run[[:space:]]+agent-review\.yml'; then
        if ! printf '%s\n' "$content" | grep -Eq -- '--ref[[:space:]]+main'; then
          echo "$file: gh workflow run agent-review.yml must include --ref main."
          bad=1
        fi
      fi

      if printf '%s\n' "$content" | grep -Eq '(^|[[:space:]])pip(3)?[[:space:]]+install[[:space:]][^"'"'"'#\n]*[<>]=?[^"'"'"'#\n]*'; then
        echo "$file: quote pip version specifiers, e.g. pip install \"pyyaml>=6.0\"."
        bad=1
      fi
      ;;
  esac
done

if [[ $bad -ne 0 ]]; then
  cat <<'EOF'

Staged guardrails failed.
Fix the reported items before committing.
EOF
  exit 1
fi

echo "Staged-file guardrails passed."
