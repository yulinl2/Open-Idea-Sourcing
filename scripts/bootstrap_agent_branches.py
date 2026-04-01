#!/usr/bin/env python3
"""
scripts/bootstrap_agent_branches.py

Called by .github/workflows/setup-agent-branches.yml to create orphan branches.
Each branch is created from the current checkout (main), then pushed to origin.

Usage (from the workflow's checkout directory):
    python3 scripts/bootstrap_agent_branches.py [--skip-existing]
"""
import argparse
import os
import subprocess
import sys
import textwrap
from pathlib import Path


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, check=check)


def branch_exists_remote(branch: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--heads", "origin", branch],
        capture_output=True,
    )
    return result.returncode == 0


def switch_to_orphan(branch: str) -> None:
    run(["git", "checkout", "--orphan", branch])
    run(["git", "rm", "-rf", ".", "--quiet"])


def checkout_from_main(*paths: str) -> None:
    run(["git", "checkout", "main", "--"] + list(paths))


def commit_and_push(branch: str, message: str, force: bool = False) -> None:
    run(["git", "add", "."])
    run(["git", "commit", "-m", message])
    if force and branch_exists_remote(branch):
        # Delete the remote branch first so an orphan root commit can be force-pushed
        # without a non-fast-forward rejection.
        run(["git", "push", "origin", "--delete", branch])
    run(["git", "push", "origin", f"HEAD:refs/heads/{branch}"])


def back_to_main() -> None:
    run(["git", "checkout", "main"])


# ---------------------------------------------------------------------------
# Shared content written to every orphan branch
# ---------------------------------------------------------------------------

# Comprehensive .gitignore for orphan agent branches.
# Must stay in sync with the template in AGENT_INSTRUCTIONS.md §8.
ORPHAN_GITIGNORE = textwrap.dedent("""\
    __pycache__/
    *.pyc
    *.pyo
    .env
    .env.local
    checkpoints/
    reports/
    .pytest_cache/
    *.egg-info/
    dist/
    build/
    .venv/
    venv/
""")


# ---------------------------------------------------------------------------
# Branch content definitions
# ---------------------------------------------------------------------------

INFRA_BASE_README = textwrap.dedent("""\
    # infra-base

    Orphan branch - canonical source for the agent-track shared execution shell.

    Track branches (agent-e2e, agent-linear, agent-reconstruct) cherry-pick
    infra/ and .github/workflows/agent-review.yml from this branch.
    They never merge back into main or infra-base.

    ## Contents

    | Path | Purpose |
    |------|---------|
    | infra/ | Shared Python execution shell: RunContext, ReportWriter, ToolRegistry, search clients, PDF utils |
    | PROJECT_INSTRUCTIONS_AGENT.md | Canonical agent-track charter |
    | AGENT_TRACK_ROADMAP.md | Per-branch build sequences and human workflow |
    | .github/workflows/agent-review.yml | Parallel CI workflow (cherry-picked into each track branch) |

    ## Cherry-picking into a track branch

    From the track branch (e.g. agent-e2e):

        git cherry-pick <infra-base-commit-sha>
""")

AGENT_E2E_README = textwrap.dedent("""\
    # agent-e2e

    Single autonomous tool loop: no imposed stage order, one report.md output.

    See AGENT_TRACK_ROADMAP.md section 3 for the full build sequence.

    ## Quickstart

        python agent.py --paper-url https://arxiv.org/abs/2006.06138 --model gpt-4o
""")

AGENT_E2E_PY = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"agent-e2e: single autonomous tool loop.

    Implementation guide: AGENT_TRACK_ROADMAP.md section 3
    \"\"\"
    import argparse
    import sys

    AGENT_IMPL_ID = "e2e_v0_0_0"


    def main() -> None:
        parser = argparse.ArgumentParser(description="agent-e2e: autonomous review loop")
        parser.add_argument("--paper-url", required=True)
        parser.add_argument("--model", default="gpt-4o")
        parser.add_argument("--output", default="reports/report.md")
        args = parser.parse_args()
        print(f"[agent-e2e] impl_id={AGENT_IMPL_ID} paper_url={args.paper_url} model={args.model}")
        print("[agent-e2e] Not yet implemented -- see AGENT_TRACK_ROADMAP.md section 3")
        sys.exit(1)


    if __name__ == "__main__":
        main()
""")

AGENT_LINEAR_README = textwrap.dedent("""\
    # agent-linear

    6-stage checkpointed pipeline with full I/O specs per stage.
    Supports --from-stage N for resuming interrupted runs.

    See AGENT_TRACK_ROADMAP.md section 4 for the full build sequence.

    ## Quickstart

        python agent.py --paper-url https://arxiv.org/abs/2006.06138 --model gpt-4o
        # Resume from stage 3:
        python agent.py --paper-url https://arxiv.org/abs/2006.06138 --from-stage 3
""")

AGENT_LINEAR_PY = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"agent-linear: 6-stage checkpointed pipeline.

    Implementation guide: AGENT_TRACK_ROADMAP.md section 4
    Supports --from-stage N for resuming interrupted runs.
    \"\"\"
    import argparse
    import sys

    AGENT_IMPL_ID = "linear_v0_0_0"


    def main() -> None:
        parser = argparse.ArgumentParser(description="agent-linear: staged pipeline")
        parser.add_argument("--paper-url", required=True)
        parser.add_argument("--model", default="gpt-4o")
        parser.add_argument("--output", default="reports/report.md")
        parser.add_argument("--from-stage", type=int, default=1,
                            help="Resume from stage N (1-6)")
        args = parser.parse_args()
        print(f"[agent-linear] impl_id={AGENT_IMPL_ID} paper_url={args.paper_url} model={args.model} "
              f"from_stage={args.from_stage}")
        print("[agent-linear] Not yet implemented -- see AGENT_TRACK_ROADMAP.md section 4")
        sys.exit(1)


    if __name__ == "__main__":
        main()
""")

AGENT_RECONSTRUCT_README = textwrap.dedent("""\
    # agent-reconstruct

    Minimal teacher-student reconstruction track.

    The teacher agent extracts a domain problem statement from the paper (no solution
    revealed). The student agent independently develops a methodology using only the
    hint and an allowed reference set -- no external search.

    See AGENT_TRACK_ROADMAP.md section 5 for the full build sequence.

    ## Quickstart

        python agent.py --paper-url https://arxiv.org/abs/2006.06138 \\\\
                        --refs 1706.03762 1409.0473 \\\\
                        --model gpt-4o

    ## Inputs

    - `--paper-url` : arXiv URL or local PDF path for the paper to reconstruct
    - `--refs`      : space-separated arXiv IDs that the student may use
    - `--model`     : LLM model identifier (default: gpt-4o)
    - `--output`    : output path for report.md (default: reports/report.md)
""")

AGENT_RECONSTRUCT_PY = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"agent-reconstruct: minimal teacher-student reconstruction track.

    Implementation guide: AGENT_TRACK_ROADMAP.md section 5

    Teacher agent: reads paper, extracts domain problem hint (no solution revealed).
    Student agent: given hint + allowed refs only, develops methodology independently.
                   No external search -- reconstruction from first principles.
    \"\"\"
    import argparse
    import sys

    AGENT_IMPL_ID = "reconstruct_v0_0_0"


    def main() -> None:
        parser = argparse.ArgumentParser(
            description="agent-reconstruct: teacher-student reconstruction"
        )
        parser.add_argument("--paper-url", required=True,
                            help="arXiv URL or local PDF path of the paper to reconstruct")
        parser.add_argument("--refs", nargs="*", default=[],
                            help="Allowed reference arXiv IDs or PDF paths for the student")
        parser.add_argument("--model", default="gpt-4o")
        parser.add_argument("--output", default="reports/report.md")
        args = parser.parse_args()
        print(f"[agent-reconstruct] impl_id={AGENT_IMPL_ID} paper_url={args.paper_url} "
              f"refs={args.refs} model={args.model}")
        print("[agent-reconstruct] Not yet implemented -- see AGENT_TRACK_ROADMAP.md section 5")
        sys.exit(1)


    if __name__ == "__main__":
        main()
""")

AGENT_REPORTS_README = textwrap.dedent("""\
    # agent-reports

    Orphan branch that accumulates published agent-track reports.

    ## Directory layout

        agent-e2e/<paper_id>/report.md
        agent-linear/<paper_id>/report.md
        agent-reconstruct/<paper_id>/report.md

    Reports are published here automatically by the agent-review.yml workflow
    after each successful run. Each report.md is self-contained with YAML
    front-matter fields (track, impl_id, model, git_commit, final_verdict,
    confidence, etc.) enabling cross-run, cross-branch comparison.

    ## Cross-track comparison

        git checkout agent-reports
        grep "final_verdict:" agent-*/2006.06138/report.md
        grep "confidence:" agent-*/2006.06138/report.md
""")


# ---------------------------------------------------------------------------
# Branch setup functions
# ---------------------------------------------------------------------------

def setup_infra_base(skip_existing: bool) -> None:
    branch = "infra-base"
    if skip_existing and branch_exists_remote(branch):
        print(f"Branch '{branch}' already exists -- skipping.")
        return
    print(f"\n=== Creating '{branch}' ===")
    switch_to_orphan(branch)
    checkout_from_main(
        "infra/",
        "PROJECT_INSTRUCTIONS_AGENT.md",
        "AGENT_TRACK_ROADMAP.md",
        ".github/workflows/agent-review.yml",
    )
    Path("README.md").write_text(INFRA_BASE_README)
    Path(".gitignore").write_text(ORPHAN_GITIGNORE)
    commit_and_push(branch, "infra-base: shared execution shell, charter, and roadmap (bootstrap)",
                    force=not skip_existing)
    print(f"Created '{branch}'")
    back_to_main()


def setup_agent_branch(
    branch: str,
    readme: str,
    agent_py: str,
    commit_msg: str,
    skip_existing: bool,
) -> None:
    if skip_existing and branch_exists_remote(branch):
        print(f"Branch '{branch}' already exists -- skipping.")
        return
    print(f"\n=== Creating '{branch}' ===")
    switch_to_orphan(branch)
    checkout_from_main("infra/", ".github/workflows/agent-review.yml")
    Path("README.md").write_text(readme)
    Path("agent.py").write_text(agent_py)
    Path(".gitignore").write_text(ORPHAN_GITIGNORE)
    commit_and_push(branch, commit_msg, force=not skip_existing)
    print(f"Created '{branch}'")
    back_to_main()


def setup_agent_reports(skip_existing: bool) -> None:
    branch = "agent-reports"
    if skip_existing and branch_exists_remote(branch):
        print(f"Branch '{branch}' already exists -- skipping.")
        return
    print(f"\n=== Creating '{branch}' ===")
    switch_to_orphan(branch)
    Path("README.md").write_text(AGENT_REPORTS_README)
    Path(".gitignore").write_text(ORPHAN_GITIGNORE)
    for track in ("agent-e2e", "agent-linear", "agent-reconstruct"):
        Path(track).mkdir(exist_ok=True)
        Path(track, ".gitkeep").touch()
    commit_and_push(branch, "agent-reports: orphan bootstrap (empty report directories)",
                    force=not skip_existing)
    print(f"Created '{branch}'")
    back_to_main()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap the agent-track orphan branches from the current main checkout."
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip branches that already exist on origin (safe re-run; default behaviour)",
    )
    parser.add_argument(
        "--no-skip-existing",
        dest="skip_existing",
        action="store_false",
        help="Recreate branches even if they already exist (destructive; deletes and re-pushes)",
    )
    parser.set_defaults(skip_existing=True)
    args = parser.parse_args()

    setup_infra_base(args.skip_existing)

    setup_agent_branch(
        branch="agent-e2e",
        readme=AGENT_E2E_README,
        agent_py=AGENT_E2E_PY,
        commit_msg="agent-e2e: orphan bootstrap (placeholder agent.py)",
        skip_existing=args.skip_existing,
    )

    setup_agent_branch(
        branch="agent-linear",
        readme=AGENT_LINEAR_README,
        agent_py=AGENT_LINEAR_PY,
        commit_msg="agent-linear: orphan bootstrap (placeholder agent.py)",
        skip_existing=args.skip_existing,
    )

    setup_agent_branch(
        branch="agent-reconstruct",
        readme=AGENT_RECONSTRUCT_README,
        agent_py=AGENT_RECONSTRUCT_PY,
        commit_msg="agent-reconstruct: orphan bootstrap (placeholder agent.py)",
        skip_existing=args.skip_existing,
    )

    setup_agent_reports(args.skip_existing)

    print("\nDone. All agent branches are set up.")
    print(
        "Next: implement agent.py on each track branch per AGENT_TRACK_ROADMAP.md."
    )


if __name__ == "__main__":
    main()
