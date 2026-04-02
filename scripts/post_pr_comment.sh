#!/usr/bin/env bash
set -euo pipefail

# Create or edit a PR comment using a real markdown body to avoid literal
# "\\n" rendering.
#
# Usage:
#   scripts/post_pr_comment.sh <pr-number> [--repo owner/repo] --body-file path/to/comment.md
#   scripts/post_pr_comment.sh <pr-number> [--repo owner/repo] --body "single line"
#   cat comment.md | scripts/post_pr_comment.sh <pr-number> [--repo owner/repo]
#   scripts/post_pr_comment.sh --edit-comment-id <comment-id> [--repo owner/repo] --body-file path/to/comment.md

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <pr-number> [--repo owner/repo] (--body-file <file> | --body <text> | stdin)" >&2
  echo "   or: $0 --edit-comment-id <comment-id> [--repo owner/repo] (--body-file <file> | --body <text> | stdin)" >&2
  exit 2
fi

mode="create"
pr_number=""
comment_id=""

if [[ "$1" == "--edit-comment-id" ]]; then
  if [[ $# -lt 2 ]]; then
    echo "--edit-comment-id requires a numeric comment id" >&2
    exit 2
  fi
  mode="edit"
  comment_id="$2"
  shift 2
else
  pr_number="$1"
  shift
fi

repo_args=()
body_file=""
body_text=""
use_agent_format=1

agent_badge='<small>········ _Posted by @🍪`Copilot via VS Code`_ ········</small>'

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      if [[ $# -lt 2 ]]; then
        echo "--repo requires a value like owner/repo" >&2
        exit 2
      fi
      repo_args=(--repo "$2")
      shift 2
      ;;
    --body-file)
      if [[ $# -lt 2 ]]; then
        echo "--body-file requires a path" >&2
        exit 2
      fi
      body_file="$2"
      shift 2
      ;;
    --body)
      if [[ $# -lt 2 ]]; then
        echo "--body requires text" >&2
        exit 2
      fi
      body_text="$2"
      shift 2
      ;;
    --as-user|--plain)
      use_agent_format=0
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -n "$body_file" && -n "$body_text" ]]; then
  echo "Use only one of --body-file or --body (or provide stdin)." >&2
  exit 2
fi

tmp_file=""
cleanup() {
  if [[ -n "$tmp_file" && -f "$tmp_file" ]]; then
    rm -f "$tmp_file"
  fi
}
trap cleanup EXIT

submit_comment() {
  local file_path="$1"
  local rendered_file="$file_path"

  if [[ "$use_agent_format" -eq 1 ]]; then
    if ! grep -Fqx "$agent_badge" "$file_path"; then
      tmp_file="$(mktemp -t pr-comment-XXXXXX.md)"
      {
        printf '%s\n\n' "$agent_badge"
        cat "$file_path"
      } > "$tmp_file"
      rendered_file="$tmp_file"
    fi
  fi

  if [[ "$mode" == "edit" ]]; then
    local repo=""
    if [[ ${#repo_args[@]} -gt 0 ]]; then
      repo="${repo_args[1]}"
    else
      repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
    fi

    local body_text
    body_text="$(cat "$rendered_file")"

    GH_REPO="$repo" gh api \
      --method PATCH \
      "repos/$repo/issues/comments/$comment_id" \
      --raw-field body="$body_text" >/dev/null
  else
    gh pr comment "$pr_number" "${repo_args[@]}" --body-file "$rendered_file"
  fi
}

if [[ -n "$body_file" ]]; then
  if [[ ! -f "$body_file" ]]; then
    echo "Body file not found: $body_file" >&2
    exit 2
  fi
  submit_comment "$body_file"
  exit 0
fi

if [[ -n "$body_text" ]]; then
  tmp_file="$(mktemp -t pr-comment-XXXXXX.md)"
  printf '%s\n' "$body_text" > "$tmp_file"
  submit_comment "$tmp_file"
  exit 0
fi

if [[ -t 0 ]]; then
  echo "No comment content provided. Use --body-file, --body, or pipe stdin." >&2
  exit 2
fi

tmp_file="$(mktemp -t pr-comment-XXXXXX.md)"
cat > "$tmp_file"

if [[ ! -s "$tmp_file" ]]; then
  echo "Comment body is empty." >&2
  exit 2
fi

submit_comment "$tmp_file"
