"""Guardrails for GitHub Actions workflow files.

These tests are intentionally strict about common failure modes so workflow
syntax/config regressions are caught in CI before merge.
"""

from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
WORKFLOW_FILES = sorted(WORKFLOWS_DIR.glob("*.yml"))


def _workflow_on(data: dict) -> dict:
    # PyYAML may coerce the literal key 'on' to boolean True.
    return data.get("on") or data.get(True, {})


def _iter_permission_mappings(node):
    """Yield every mapping value found under a 'permissions' key."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "permissions" and isinstance(value, dict):
                yield value
            yield from _iter_permission_mappings(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_permission_mappings(item)


def test_workflow_files_exist():
    assert WORKFLOW_FILES, "Expected at least one workflow file under .github/workflows"


def test_all_workflows_parse_as_yaml():
    for workflow_file in WORKFLOW_FILES:
        raw = workflow_file.read_text(encoding="utf-8")
        try:
            yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise AssertionError(f"Invalid YAML in {workflow_file}: {exc}") from exc


def test_workflow_jobs_use_only_supported_permission_scopes():
    """All workflow jobs must only use GitHub Actions supported permission scopes.

    The `workflows` scope IS supported and intentionally used on jobs that push
    .github/workflows/*.yml files to orphan branches.  Any other unknown scope
    would indicate a typo or misunderstanding.
    """
    # Full list of supported GitHub Actions permission scopes.
    supported_scopes = {
        "actions", "attestations", "checks", "contents", "deployments",
        "discussions", "id-token", "issues", "metadata", "packages",
        "pages", "pull-requests", "repository-projects", "secrets",
        "security-events", "statuses", "workflows",
    }
    for workflow_file in WORKFLOW_FILES:
        data = yaml.safe_load(workflow_file.read_text(encoding="utf-8"))
        for permission_mapping in _iter_permission_mappings(data):
            for scope in permission_mapping:
                assert scope in supported_scopes, (
                    f"Unknown/unsupported permission scope '{scope}' in {workflow_file}. "
                    f"Supported scopes: {sorted(supported_scopes)}"
                )


def test_sync_workflow_uses_workflows_write_permission():
    """sync-agent-review-workflow must use workflows:write permission.

    This allows github.token to push .github/workflows/agent-review.yml to
    orphan branches without needing a dedicated PAT with workflow scope.
    """
    workflow_file = WORKFLOWS_DIR / "agent-track-workflows.yml"
    data = yaml.safe_load(workflow_file.read_text(encoding="utf-8"))
    sync_job = data["jobs"]["sync-agent-review-workflow"]

    permissions = sync_job.get("permissions", {})
    assert permissions.get("workflows") == "write", (
        "sync-agent-review-workflow must have workflows:write permission so "
        "github.token can push .github/workflows/agent-review.yml to orphan branches"
    )

    # The checkout step must NOT override the token with a PAT; github.token
    # with workflows:write is sufficient.
    checkout_steps = [
        step
        for step in sync_job.get("steps", [])
        if step.get("name") == "Checkout main"
    ]
    assert checkout_steps, "Expected 'Checkout main' step in sync-agent-review-workflow"
    token_expr = checkout_steps[0].get("with", {}).get("token", "")
    normalized_token = str(token_expr).strip()
    assert normalized_token in ("", "${{ github.token }}"), (
        "Checkout main in sync-agent-review-workflow must use the default "
        "github.token (no PAT or non-default secret such as "
        "secrets.ORPHAN_WORKFLOW_PUSH_TOKEN; if set explicitly, token must be "
        "${{ github.token }})"
    )


def test_fix_gitignore_workflow_has_self_archive_step():
    """fix-gitignore must retain the self-archive step for auto-retire.

    The job also needs workflows:write so github.token can push
    agent-track-workflows.yml to main when the retire script runs.
    """
    workflow_file = WORKFLOWS_DIR / "agent-track-workflows.yml"
    data = yaml.safe_load(workflow_file.read_text(encoding="utf-8"))
    fix_job = data["jobs"]["fix-gitignore"]

    steps = fix_job.get("steps", [])
    names = [step.get("name") for step in steps]
    assert "Self-archive this operation" in names, (
        "fix-gitignore must keep self-archive step"
    )

    permissions = fix_job.get("permissions", {})
    assert permissions.get("workflows") == "write", (
        "fix-gitignore must have workflows:write permission so github.token can "
        "push agent-track-workflows.yml to main during self-archive"
    )


def test_agent_track_workflow_is_maintenance_only():
    workflow_file = WORKFLOWS_DIR / "agent-track-workflows.yml"
    data = yaml.safe_load(workflow_file.read_text(encoding="utf-8"))

    workflow_on = _workflow_on(data)

    # A push trigger is allowed ONLY if it is narrowed to a paths filter
    # (no-op guard to prevent phantom failure check-runs when this file
    # changes in a PR commit).  A blanket push trigger without paths would
    # fire on every branch push and is not permitted.
    if "push" in workflow_on:
        push_cfg = workflow_on["push"] or {}
        assert push_cfg.get("paths"), (
            "agent-track-workflows push trigger must have a 'paths' filter — "
            "a blanket push trigger is not allowed for a maintenance-only workflow"
        )

    options = workflow_on["workflow_dispatch"]["inputs"]["operation"]["options"]
    assert "review" not in options, "review should dispatch via agent-review.yml, not maintenance workflow"


def test_agent_review_has_strict_prechecks_without_placeholder_fallback():
    workflow_file = WORKFLOWS_DIR / "agent-review.yml"
    data = yaml.safe_load(workflow_file.read_text(encoding="utf-8"))
    job = data["jobs"]["agent-review"]

    steps = job.get("steps", [])
    keycheck = [step for step in steps if step.get("name") == "Validate OPENAI_API_KEY"]
    assert keycheck, "agent-review workflow must validate OPENAI_API_KEY before execution"

    run_steps = [step for step in steps if step.get("name") == "Run agent review"]
    assert run_steps, "Expected Run agent review step"
    run_script = run_steps[0].get("run", "")
    assert "reports/report.md is missing or empty" in run_script, (
        "Run agent review must fail if agent.py does not produce a non-empty report"
    )

    validate_track_steps = [
        step for step in steps if step.get("name") == "Validate track implementation exists"
    ]
    assert validate_track_steps, (
        "agent-review workflow must fail fast if agent.py is missing on track branch"
    )


def test_agent_review_supports_track_all_option():
    workflow_file = WORKFLOWS_DIR / "agent-review.yml"
    data = yaml.safe_load(workflow_file.read_text(encoding="utf-8"))

    workflow_on = _workflow_on(data)
    track_input = workflow_on["workflow_dispatch"]["inputs"]["track"]
    assert "all" in track_input["options"], "agent-review track input must include all"

    resolve_job = data["jobs"].get("resolve-track-matrix", {})
    assert resolve_job, "agent-review must resolve matrix for all-track fan-out"

    agent_job = data["jobs"].get("agent-review", {})
    assert "strategy" in agent_job, "agent-review must use a matrix strategy"