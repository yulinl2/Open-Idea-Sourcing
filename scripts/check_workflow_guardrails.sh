#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/check_workflow_guardrails.sh [workflow-file ...]
# If no files are provided, checks all workflow YAML files.

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [[ $# -gt 0 ]]; then
  files=("$@")
else
  files=()
  while IFS= read -r f; do
    files+=("$f")
  done < <(find .github/workflows -maxdepth 1 -type f -name "*.yml" | sort)
fi

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No workflow files found to validate."
  exit 0
fi

bad=0

for file in "${files[@]}"; do
  if [[ ! -f "$file" ]]; then
    continue
  fi

  # Guardrail: `permissions.workflows` is not a supported GitHub Actions scope
  # and causes workflow syntax validation errors.
  if awk '
    function indent(s,  i) {
      for (i = 1; i <= length(s); i++) {
        if (substr(s, i, 1) != " ") return i - 1
      }
      return length(s)
    }
    {
      line = $0
      if (line ~ /^[[:space:]]*#/) next

      if (line ~ /^[[:space:]]*permissions:[[:space:]]*$/) {
        in_permissions = 1
        perm_indent = indent(line)
        next
      }

      if (in_permissions) {
        if (line ~ /^[[:space:]]*$/) next
        curr_indent = indent(line)
        if (curr_indent <= perm_indent) {
          in_permissions = 0
        }
      }

      if (in_permissions && line ~ /^[[:space:]]*workflows:[[:space:]]*[^#]*$/) {
        printf("%s:%d: unsupported permissions key: workflows\n", FILENAME, NR)
        bad = 1
      }
    }
    END { exit bad }
  ' "$file"; then
    :
  else
    bad=1
  fi
done

if [[ $bad -ne 0 ]]; then
  cat <<'EOF'

Workflow guardrail failed.
Remove unsupported `workflows:` keys from `permissions:` blocks.
EOF
  exit 1
fi

echo "Workflow guardrails passed."
