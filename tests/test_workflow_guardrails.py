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


def test_permissions_do_not_use_unsupported_workflows_scope():
    """GitHub Actions permissions do not support a 'workflows' scope key."""
    for workflow_file in WORKFLOW_FILES:
        data = yaml.safe_load(workflow_file.read_text(encoding="utf-8"))
        for permission_mapping in _iter_permission_mappings(data):
            assert "workflows" not in permission_mapping, (
                "Unsupported permissions key 'workflows' found in "
                f"{workflow_file}. Use supported scopes only."
            )