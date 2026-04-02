#!/usr/bin/env python3
"""
.github/scripts/fix_orphan_agent_review.py

One-shot script to write the correct agent-review.yml on infra-base (and
optionally each agent-track branch).

The canonical content for infra-base / agent branches is main's agent-review.yml
plus a push trigger for infra-base and each agent-* branch.  The push trigger
must NOT live on main's copy (it causes phantom failure check-runs on every
copilot/* PR push).

Run this after merging the main cleanup PR so that:
1. infra-base gets the shell-based placeholder fix (from PR #78) and the
   infra-base push trigger that was inadvertently left out.
2. agent-* branches optionally get the same update.

Usage:
    python3 .github/scripts/fix_orphan_agent_review.py [--branches infra-base agent-e2e ...]

The script uses git worktrees so it never abandons the current branch.
Each worktree is cleaned up on exit whether the run succeeds or fails.
"""
import argparse
import contextlib
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Content of agent-review.yml for infra-base / agent-* branches.
#
# Identical to main's version except:
#   • Header comment updated to describe push trigger intent
#   • Push trigger section added for infra-base + all agent-* branches
#
# (Keep this in sync with .github/workflows/agent-review.yml on main.)
# ---------------------------------------------------------------------------

INFRA_AGENT_REVIEW_YML = """\
name: Agent review

# Parallel agent-track CI — runs independently of the baseline ci.yml pipeline.
#
# Trigger matrix:
#   • Manual (workflow_dispatch)  — review any paper on any agent track
#   • Push to infra-base / agent-* branches — run fast infra tests (no API key needed)
#
# NOTE: The push trigger intentionally lives here (infra-base / agent-* branches)
# and NOT on main.  Having push: branches: [agent-*] in main's copy causes GitHub
# to create phantom failure check-runs on every copilot/* PR branch push (the
# pushed branch never matches agent-*, so 0 jobs run and the check fails).
# Main's copy carries workflow_dispatch only.
#
# This workflow is branch-local by design: each agent-* branch carries its own
# agent.py and this workflow discovers it automatically via the TRACK variable.
# The baseline ci.yml (review_paper.py) is unaffected.

on:
  push:
    branches:
      - "infra-base"
      - "agent-e2e"
      - "agent-linear"
      - "agent-reconstruct"
  workflow_dispatch:
    inputs:
      paper_url:
        description: "URL of the paper to review (arXiv abstract or PDF)"
        required: true
        default: "https://arxiv.org/abs/2006.06138"
      track:
        description: "Agent track to use: e2e | linear | reconstruct"
        required: true
        default: "e2e"
      model:
        description: "LLM model identifier (e.g. gpt-4o, gpt-4o-mini)"
        required: false
        default: "gpt-4o"

# Prevent concurrent agent runs on the same track from interfering.
concurrency:
  group: "agent-${{ inputs.track || github.ref_name }}"
  cancel-in-progress: false

jobs:
  # ------------------------------------------------------------------
  # Job 1: Run infra unit tests (no API key needed; runs on every push)
  # ------------------------------------------------------------------
  test-infra:
    name: Infra tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12.12"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          # Install base requirements if present; fall back to pdfminer only
          if [ -f requirements.txt ]; then
            python -m pip install -r requirements.txt
          else
            python -m pip install pdfminer.six
          fi

      - name: Run infra unit tests
        run: |
          # Run infra-specific tests if the test directory exists.
          # Falls back to a basic import smoke-test until track tests are added.
          if [ -d tests ] && python -m pytest tests/ --co -q 2>/dev/null | grep -q "agent"; then
            python -m pytest tests/ -v -k "agent or infra" -m "not slow"
          else
            python -c "from infra import RunContext, ReportContent, ReportWriter, ToolRegistry; ctx = RunContext(track='smoke', impl_id='smoke_v0', paper_id='test', paper_source='local', model='stub'); ctx.record_tool('smoke_tool'); ctx.mark_finished(); fm = ctx.to_yaml_front_matter(); assert 'track:' in fm, 'YAML front matter missing track'; assert 'smoke_tool' in fm, 'YAML front matter missing tool'; print('Infra smoke test passed.')"
          fi

  # ------------------------------------------------------------------
  # Job 2: Run agent review (manual trigger only — requires OPENAI_API_KEY)
  # ------------------------------------------------------------------
  agent-review:
    name: "Agent review (${{ inputs.track || github.ref_name }})"
    runs-on: ubuntu-latest
    if: github.event_name == 'workflow_dispatch'
    needs: test-infra
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4
        with:
          # Check out the agent-<track> branch so agent.py is present.
          # Falls back to the current ref if the track branch doesn't exist yet.
          ref: "agent-${{ inputs.track }}"
        continue-on-error: true

      - name: Fallback checkout (track branch not yet created)
        uses: actions/checkout@v4
        if: ${{ failure() }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12.12"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then
            python -m pip install -r requirements.txt
          else
            python -m pip install pdfminer.six openai
          fi

      - name: Derive paper ID from URL
        id: paper
        env:
          PAPER_URL: ${{ inputs.paper_url }}
        run: |
          # Extract a filesystem-safe paper ID from the URL.
          # arXiv: https://arxiv.org/abs/2006.06138 → 2006.06138
          PAPER_ID=$(python -c "import re, os; url = os.environ['PAPER_URL']; m = re.search(r'arxiv\\.org/(?:abs|pdf)/([0-9]+\\.[0-9]+)', url); print(m.group(1) if m else url.rstrip('/').split('/')[-1].replace('.pdf', '')[:50])")
          echo "PAPER_ID=$PAPER_ID" >> "$GITHUB_OUTPUT"
          echo "Derived paper ID: $PAPER_ID"

      - name: Run agent review
        id: run-agent
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          PAPER_URL: ${{ inputs.paper_url }}
          TRACK: ${{ inputs.track }}
          MODEL: ${{ inputs.model }}
          PAPER_ID: ${{ steps.paper.outputs.PAPER_ID }}
        run: |
          mkdir -p reports

          if [ -f agent.py ]; then
            # Run the track's agent.py if it exists.
            python agent.py \\
              --paper-url "$PAPER_URL" \\
              --model "${MODEL:-gpt-4o}" \\
              --output reports/report.md
          else
            # agent.py not yet on this branch — emit a placeholder report
            # so the artifact upload and agent-reports-branch publish still work.
            # Shell-only implementation keeps all content at YAML block-scalar
            # indentation (column ≥ 10), avoiding the YAML parse error that
            # occurs when Python inline code starts at column 0.
            NOW=$(python3 -c "import datetime; print(datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))")
            SHA="${GITHUB_SHA:0:8}"
            {
              echo '---'
              printf 'track: %s\\n'        "$TRACK"
              echo  'impl_id: placeholder'
              printf 'paper_id: %s\\n'     "$PAPER_ID"
              printf 'paper_source: %s\\n' "$PAPER_URL"
              printf 'model: %s\\n'        "${MODEL:-gpt-4o}"
              echo  'tool_list: []'
              printf 'start_time: %s\\n'   "$NOW"
              printf 'finish_time: %s\\n'  "$NOW"
              printf 'git_commit: %s\\n'   "$SHA"
              echo  'final_verdict: PENDING'
              echo  'confidence: 0.00'
              echo  'main_cited_evidence: []'
              echo  '---'
              echo  ''
              printf '# Derivation Audit: %s\\n' "$PAPER_ID"
              echo  ''
              printf '> **Note:** `agent.py` has not yet been implemented on the `agent-%s`\\n' "$TRACK"
              echo  '> branch. This placeholder report was generated by the CI workflow.'
              echo  '> See `docs/AGENT_TRACK_ROADMAP.md` for the build sequence.'
              echo  ''
              echo  '## Status'
              echo  ''
              printf 'The `agent-%s` branch is queued for implementation.\\n' "$TRACK"
              echo  'See [AGENT_TRACK_ROADMAP.md](../docs/AGENT_TRACK_ROADMAP.md) for the roadmap.'
            } > reports/report.md
          fi

      - name: Upload report as artifact
        uses: actions/upload-artifact@v4
        with:
          name: "agent-${{ inputs.track }}-report-${{ steps.paper.outputs.PAPER_ID }}"
          path: reports/report.md

      - name: Publish report to agent-reports branch
        env:
          TRACK: ${{ inputs.track }}
          PAPER_ID: ${{ steps.paper.outputs.PAPER_ID }}
          RUN_NUMBER: ${{ github.run_number }}
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          # Publish under agent-<track>/<paper_id>/report.md inside the
          # agent-reports orphan branch (namespaced away from baseline reports/).
          TARGET_DIR="agent-${TRACK}/${PAPER_ID}"

          if git ls-remote --exit-code --heads origin agent-reports > /dev/null 2>&1; then
            git fetch origin agent-reports
            git worktree add /tmp/agent-reports-branch origin/agent-reports
          else
            git worktree add --orphan -b agent-reports /tmp/agent-reports-branch
          fi

          mkdir -p "/tmp/agent-reports-branch/${TARGET_DIR}"
          cp reports/report.md "/tmp/agent-reports-branch/${TARGET_DIR}/report.md"

          cd /tmp/agent-reports-branch
          git add .
          if git diff --cached --quiet; then
            echo "No new reports to commit."
          else
            git -c commit.gpgsign=false commit -m "agent report: ${TRACK}/${PAPER_ID} (run #${RUN_NUMBER})"
            git push origin HEAD:agent-reports
          fi
"""

ORPHAN_BRANCHES = [
    "infra-base",
    "agent-e2e",
    "agent-linear",
    "agent-reconstruct",
]


def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, check=check, cwd=cwd)


def branch_exists_remote(branch: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", branch],
        capture_output=True,
    )
    return result.returncode == 0


@contextlib.contextmanager
def worktree(branch: str):
    """Context manager: adds a detached worktree for *branch*, cleans up on exit."""
    with tempfile.TemporaryDirectory(prefix=f"wt-{branch.replace('/', '-')}-") as tmpdir:
        run(["git", "worktree", "add", "--detach", tmpdir, f"origin/{branch}"])
        try:
            run(["git", "checkout", "-B", branch], cwd=tmpdir)
            yield Path(tmpdir)
        finally:
            run(["git", "worktree", "remove", "--force", tmpdir], check=False)


def fix_branch(branch: str) -> bool:
    if not branch_exists_remote(branch):
        print(f"  Branch '{branch}' not found on origin — skipping.")
        return False

    print(f"\n=== Fixing agent-review.yml on '{branch}' ===")
    with worktree(branch) as wt_path:
        dest = wt_path / ".github" / "workflows" / "agent-review.yml"
        dest.parent.mkdir(parents=True, exist_ok=True)

        current = dest.read_text() if dest.exists() else ""
        if current == INFRA_AGENT_REVIEW_YML:
            print(f"  agent-review.yml already up to date — nothing to do.")
            return False

        dest.write_text(INFRA_AGENT_REVIEW_YML)
        run(["git", "add", ".github/workflows/agent-review.yml"], cwd=str(wt_path))
        run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-m",
             f"{branch}: update agent-review.yml — shell placeholder, infra-base push trigger"],
            cwd=str(wt_path),
        )
        try:
          run(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], cwd=str(wt_path))
        except subprocess.CalledProcessError:
          print("  Push failed while updating a workflow file.")
          print("  This operation requires a token with workflow write access.")
          print(
            "  In GitHub Actions, configure ORPHAN_WORKFLOW_PUSH_TOKEN and rerun "
            "sync-agent-review-workflow.",
          )
          raise
        print(f"  Updated '{branch}'.")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply the correct agent-review.yml to orphan agent branches.",
    )
    parser.add_argument(
        "--branches",
        nargs="+",
        default=ORPHAN_BRANCHES,
        metavar="BRANCH",
        help=f"Branches to update (default: {' '.join(ORPHAN_BRANCHES)})",
    )
    args = parser.parse_args()

    updated = []
    try:
      for branch in args.branches:
        if fix_branch(branch):
          updated.append(branch)
    except subprocess.CalledProcessError as exc:
      cmd = " ".join(str(part) for part in exc.cmd)
      print(f"\nERROR: command failed: {cmd}", file=sys.stderr)
      print(
        "Hint: if this failed on git push for .github/workflows/agent-review.yml, "
        "use a PAT with workflow write access.",
        file=sys.stderr,
      )
      sys.exit(exc.returncode)

    print("\nDone.")
    if updated:
        print(f"Updated branches: {', '.join(updated)}")
    else:
        print("All branches were already up to date.")


if __name__ == "__main__":
    main()
