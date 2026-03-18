#!/usr/bin/env python3
"""Automated documentation update script.

Reads the current codebase state, constructs a prompt using the
doc-agent instructions template (.github/doc-agent-instructions.md),
calls OpenAI to generate targeted doc updates, and writes the results back.

Environment variables
---------------------
OPENAI_API_KEY   Required.  OpenAI API key.
CHANGE_SUMMARY   Optional.  Brief description of what changed.  If omitted,
                 the script derives a summary from the most recent git commit
                 message.
DOC_SCOPE        Optional.  Comma-separated file keys to update.
                 Use "all" (default) to update every file listed in
                 doc-agent-instructions.md.
DRY_RUN          Optional.  Set to "true" to print proposed JSON without
                 writing files.
OPENAI_MODEL     Optional.  Model name (default: gpt-4o).

Transfer guide
--------------
To reuse this script in another project:
1. Copy this file and .github/doc-agent-instructions.md to the new repo.
2. Update DOC_FILES to match the new project's documentation layout (the
   same keys that appear in .github/doc-agent-instructions.md Section 2).
3. Update _extract_cli_flags() if the CLI is not argparse-based.
4. The rest of the script is generic.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Project-specific configuration — update when transferring to another repo
# ---------------------------------------------------------------------------

#: Maps the short "file key" used in prompts/responses to repo-relative paths.
DOC_FILES: dict[str, str] = {
    "readme": "README.md",
    "workflow-guide": "WORKFLOW_GUIDE.md",
    "changelog": "CHANGELOG.md",
    "site-index": "docs/index.md",
    "site-config": "docs/_config.yml",
}

#: Repo root (parent of this script's grandparent directory).
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

#: Instruction set / system prompt for the doc-writing agent.
INSTRUCTIONS_PATH = REPO_ROOT / ".github" / "doc-agent-instructions.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(rel: str) -> str:
    p = REPO_ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _write(rel: str, content: str) -> None:
    p = REPO_ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _extract_version() -> str:
    """Return the package version string from open_idea_sourcing/__init__.py."""
    src = _read("open_idea_sourcing/__init__.py")
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', src)
    return m.group(1) if m else "unknown"


def _extract_cli_flags() -> str:
    """Return the argparse _parse_args() body from review_paper.py (truncated)."""
    src = _read("review_paper.py")
    # Grab everything from the _parse_args function definition to the next
    # top-level function/class so we capture all add_argument() calls.
    m = re.search(r"(def _parse_args\b.*?)(?=\n^def |\n^class |\Z)", src, re.DOTALL | re.MULTILINE)
    body = m.group(1) if m else src
    return body[:4000]  # cap to stay within token budget


def _git_last_commit_message() -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _build_codebase_context() -> str:
    version = _extract_version()
    cli_section = _extract_cli_flags()
    changelog_head = _read("CHANGELOG.md")[:2000]
    return (
        f"## Codebase snapshot\n\n"
        f"**Package version:** `{version}`\n\n"
        f"**CLI flags (`review_paper.py _parse_args`):**\n"
        f"```python\n{cli_section}\n```\n\n"
        f"**CHANGELOG (first 2000 chars):**\n"
        f"```\n{changelog_head}\n```\n"
    )


def _build_prompt(
    instructions: str,
    context: str,
    change_summary: str,
    scope: list[str],
) -> str:
    doc_sections = "\n\n".join(
        f"### `{DOC_FILES[key]}` (key: `{key}`)\n```\n{_read(DOC_FILES[key])[:4000]}\n```"
        for key in scope
        if key in DOC_FILES
    )
    keys_list = ", ".join(f'"{k}"' for k in scope if k in DOC_FILES)
    return (
        f"{instructions}\n\n"
        f"---\n\n"
        f"{context}\n\n"
        f"---\n\n"
        f"## What changed\n\n"
        f"{change_summary}\n\n"
        f"---\n\n"
        f"## Current documentation\n\n"
        f"{doc_sections}\n\n"
        f"---\n\n"
        f"## Task\n\n"
        f"Update the documentation files listed above (keys: {keys_list}) to "
        f"accurately reflect the current codebase state and the change described "
        f"above.  Follow the rules in the instruction set exactly.\n\n"
        f"Return a JSON object with keys from: {keys_list}.  "
        f"Omit any file that requires no changes.  "
        f"Return ONLY the JSON object — no surrounding prose."
    )


def _parse_json_response(raw: str) -> dict[str, str]:
    """Extract a JSON object from the LLM response, handling markdown fences."""
    raw = raw.strip()
    # Strip outer ```json ... ``` if present
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        raw = m.group(1)
    # Find the outermost { ... }
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in response")
    return json.loads(raw[start : end + 1])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("OPENAI_API_KEY not set — skipping doc update.", file=sys.stderr)
        return 0  # non-fatal so push-triggered runs don't fail without a key

    change_summary = os.environ.get("CHANGE_SUMMARY", "").strip()
    if not change_summary:
        change_summary = _git_last_commit_message() or "No change summary provided."

    scope_raw = os.environ.get("DOC_SCOPE", "all").strip()
    scope: list[str] = (
        list(DOC_FILES.keys())
        if scope_raw == "all"
        else [s.strip() for s in scope_raw.split(",")]
    )
    # Filter to known keys only
    scope = [k for k in scope if k in DOC_FILES]
    if not scope:
        print(f"Unknown DOC_SCOPE value(s): {scope_raw}", file=sys.stderr)
        return 1

    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    instructions = INSTRUCTIONS_PATH.read_text(encoding="utf-8") if INSTRUCTIONS_PATH.exists() else (
        "You are a technical documentation writer.  "
        "Update the provided documentation files to match the codebase."
    )

    context = _build_codebase_context()
    prompt = _build_prompt(instructions, context, change_summary, scope)

    try:
        from openai import OpenAI  # local import so the module is importable without openai installed
    except ImportError:
        print("openai package not installed; run: pip install openai", file=sys.stderr)
        return 1

    client = OpenAI(api_key=api_key)
    print(f"Calling {model} to update docs (scope: {', '.join(scope)}) …")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    raw = response.choices[0].message.content or ""

    if dry_run:
        print("=== DRY RUN — proposed changes ===")
        print(raw)
        return 0

    try:
        updates = _parse_json_response(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Failed to parse LLM response as JSON: {exc}", file=sys.stderr)
        print(raw[:2000], file=sys.stderr)
        return 1

    if not updates:
        print("LLM returned an empty update set — no files changed.")
        return 0

    for key, content in updates.items():
        if key not in DOC_FILES:
            print(f"Warning: unknown file key '{key}' in response — skipping.", file=sys.stderr)
            continue
        # Ensure single trailing newline
        content = content.rstrip("\n") + "\n"
        _write(DOC_FILES[key], content)
        print(f"Updated {DOC_FILES[key]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
