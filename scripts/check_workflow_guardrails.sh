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

  if grep -n $'\t' "$file" >/dev/null 2>&1; then
    grep -n $'\t' "$file" | sed "s|^|$file: tab indentation is not allowed in workflow YAML: |"
    bad=1
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

  # Guardrail: any workflow_dispatch input that declares options must also
  # declare `type: choice` in the same input block.
  if awk '
    function indent(s,  i) {
      for (i = 1; i <= length(s); i++) {
        if (substr(s, i, 1) != " ") return i - 1
      }
      return length(s)
    }
    function finish_input_block() {
      if (in_input && saw_options && !saw_choice_type) {
        printf("%s:%d: workflow_dispatch input \"%s\" has options but no type: choice\n", FILENAME, input_start_line, input_name)
        bad = 1
      }
      in_input = 0
      input_indent = -1
      input_name = ""
      saw_options = 0
      saw_choice_type = 0
    }
    {
      line = $0
      if (line ~ /^[[:space:]]*#/) next

      if (line ~ /^[[:space:]]*workflow_dispatch:[[:space:]]*$/) {
        in_workflow_dispatch = 1
        workflow_dispatch_indent = indent(line)
        next
      }

      if (in_workflow_dispatch) {
        curr_indent = indent(line)
        if (line !~ /^[[:space:]]*$/ && curr_indent <= workflow_dispatch_indent) {
          finish_input_block()
          in_workflow_dispatch = 0
          in_inputs = 0
        }
      }

      if (in_workflow_dispatch && line ~ /^[[:space:]]*inputs:[[:space:]]*$/) {
        in_inputs = 1
        inputs_indent = indent(line)
        next
      }

      if (in_inputs) {
        curr_indent = indent(line)
        if (line !~ /^[[:space:]]*$/ && curr_indent <= inputs_indent) {
          finish_input_block()
          in_inputs = 0
        }
      }

      if (in_inputs) {
        if (line ~ /^[[:space:]]*[A-Za-z0-9_-]+:[[:space:]]*$/) {
          curr_indent = indent(line)
          if (curr_indent > inputs_indent) {
            if (in_input && curr_indent <= input_indent) {
              finish_input_block()
            }
            if (!in_input) {
              input_name = line
              sub(/^[[:space:]]*/, "", input_name)
              sub(/:.*/, "", input_name)
              in_input = 1
              input_indent = curr_indent
              input_start_line = NR
              saw_options = 0
              saw_choice_type = 0
              next
            }
          }
        }

        if (in_input) {
          curr_indent = indent(line)
          if (line !~ /^[[:space:]]*$/ && curr_indent <= input_indent) {
            finish_input_block()
          }
        }

        if (in_input) {
          if (line ~ /^[[:space:]]*options:[[:space:]]*$/) {
            saw_options = 1
          }
          if (line ~ /^[[:space:]]*type:[[:space:]]*choice[[:space:]]*$/) {
            saw_choice_type = 1
          }
        }
      }
    }
    END {
      finish_input_block()
      exit bad
    }
  ' "$file"; then
    :
  else
    bad=1
  fi

  if grep -Eq 'gh[[:space:]]+workflow[[:space:]]+run[[:space:]]+agent-review\.yml' "$file"; then
    if ! grep -Eq -- '--ref[[:space:]]+main' "$file"; then
      echo "$file: gh workflow run agent-review.yml must include --ref main."
      bad=1
    fi
  fi

  # Guardrail: sync-agent-review-workflow updates workflow files on orphan
  # branches, so it must require a dedicated token secret and validate it.
  if [[ "$file" == ".github/workflows/agent-track-workflows.yml" ]]; then
    if grep -Eq 'name:[[:space:]]+Sync agent-review workflow on orphan branches' "$file"; then
      if ! grep -Eq 'token:[[:space:]]+\$\{\{[[:space:]]*secrets\.ORPHAN_WORKFLOW_PUSH_TOKEN[[:space:]]*\|\|[[:space:]]*github\.token[[:space:]]*\}\}' "$file"; then
        echo "$file: sync-agent-review-workflow Checkout main must set with.token to secrets.ORPHAN_WORKFLOW_PUSH_TOKEN || github.token."
        bad=1
      fi
      if ! grep -Eq 'name:[[:space:]]+Validate workflow push token' "$file"; then
        echo "$file: sync-agent-review-workflow must include a preflight token validation step."
        bad=1
      fi
    fi

    if grep -Eq 'name:[[:space:]]+Write \.gitignore to all orphan branches' "$file"; then
      if ! grep -Eq 'Self-archive skipped \(missing token\)' "$file"; then
        echo "$file: fix-gitignore must include explicit self-archive skipped messaging when token is missing."
        bad=1
      fi
    fi
  fi
done

if [[ $bad -ne 0 ]]; then
  cat <<'EOF'

Workflow guardrail failed.
Fix the reported workflow issues before committing or pushing.
EOF
  exit 1
fi

echo "Workflow guardrails passed."
