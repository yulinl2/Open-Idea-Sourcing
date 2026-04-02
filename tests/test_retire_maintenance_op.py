"""Tests for .github/scripts/retire_maintenance_op.py.

Covers the pure retire_op() transformation logic and the git-staging path
that previously failed with exit code 128 when a script file was deleted.
"""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Import the script under test (it lives outside the normal package tree).
# ---------------------------------------------------------------------------

_SCRIPT_PATH = (
    Path(__file__).parent.parent / ".github" / "scripts" / "retire_maintenance_op.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("retire_maintenance_op", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rmo = _load_module()
retire_op = rmo.retire_op


# ---------------------------------------------------------------------------
# Minimal YAML fixture helpers
# ---------------------------------------------------------------------------

_SAMPLE_YAML = """\
name: Agent track workflows

# Operations:
#
#   review (default)
#   my-op  — does something useful
#   other-op — also useful
#

on:
  workflow_dispatch:
    inputs:
      operation:
        description: "Operation to run"
        required: false
        default: "review"
        type: choice
        options:
          - review
          - my-op
          - other-op
      my_exclusive_input:
        description: "Only used by my-op"
        required: false
        type: boolean

jobs:
  dispatch-tracks:
    name: Dispatch
    if: github.event.inputs.operation == 'review'
    runs-on: ubuntu-latest
    steps:
      - name: Do something
        run: echo hi

  # -------------------------------------------------------
  # Maintenance: my-op does the thing.
  # Trigger manually with operation=my-op.
  # -------------------------------------------------------
  my-op:
    name: My maintenance op
    if: github.event.inputs.operation == 'my-op'
    runs-on: ubuntu-latest
    steps:
      - name: Run
        run: echo done

  other-op:
    name: Other maintenance op
    if: github.event.inputs.operation == 'other-op'
    runs-on: ubuntu-latest
    steps:
      - name: Run
        run: echo done
"""


# ---------------------------------------------------------------------------
# Tests for retire_op() pure-function logic
# ---------------------------------------------------------------------------


class TestRetireOp:
    """Verify retire_op() correctly transforms the YAML string."""

    def test_removes_op_from_choice_options(self):
        updated, _ = retire_op(_SAMPLE_YAML, "my-op")
        assert "- my-op" not in updated
        assert "- other-op" in updated
        assert "- review" in updated

    def test_removes_op_header_comment(self):
        updated, _ = retire_op(_SAMPLE_YAML, "my-op")
        assert "#   my-op" not in updated
        assert "#   other-op" in updated

    def test_removes_job_block(self):
        updated, _ = retire_op(_SAMPLE_YAML, "my-op")
        assert "my-op:" not in updated
        assert "My maintenance op" not in updated

    def test_other_job_preserved(self):
        updated, _ = retire_op(_SAMPLE_YAML, "my-op")
        assert "other-op:" in updated
        assert "Other maintenance op" in updated

    def test_removes_exclusive_inputs(self):
        """Inputs listed in OP_EXCLUSIVE_INPUTS for the op are stripped."""
        # Patch OP_EXCLUSIVE_INPUTS to mark my_exclusive_input as exclusive to my-op.
        with patch.dict(rmo.OP_EXCLUSIVE_INPUTS, {"my-op": ["my_exclusive_input"]}):
            updated, _ = retire_op(_SAMPLE_YAML, "my-op")
        assert "my_exclusive_input" not in updated

    def test_extracts_job_block(self):
        _, block = retire_op(_SAMPLE_YAML, "my-op")
        assert "my-op:" in block
        assert "My maintenance op" in block

    def test_idempotent_after_first_run(self):
        updated, _ = retire_op(_SAMPLE_YAML, "my-op")
        updated2, _ = retire_op(updated, "my-op")
        assert updated == updated2

    def test_no_change_when_op_absent(self):
        updated, block = retire_op(_SAMPLE_YAML, "nonexistent-op")
        assert updated == _SAMPLE_YAML
        assert block == ""


# ---------------------------------------------------------------------------
# Tests for the git-staging path in main()
# ---------------------------------------------------------------------------


class TestGitStagingPath:
    """Regression test: retiring an op with an associated script must NOT call
    `git add -u` after `git rm --cached`, which caused exit code 128."""

    def _run_main_with_mocks(self, tmp_path, *, script_exists: bool, no_push: bool = True):
        """
        Run retire_maintenance_op.main() with mocked filesystem + git calls.

        Creates a temporary agent-track-workflows.yml, optionally a script
        file, and captures every subprocess command that would be run.
        Pass ``no_push=False`` to exercise the git-staging code path.
        """
        # ---- Set up fake workflow file ----
        wf_dir = tmp_path / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        wf_path = wf_dir / "agent-track-workflows.yml"
        wf_path.write_text(_SAMPLE_YAML)

        # ---- Set up fake script file ----
        scripts_dir = tmp_path / ".github" / "scripts"
        scripts_dir.mkdir(parents=True)
        fake_script = scripts_dir / "fix_my_op.py"
        if script_exists:
            fake_script.write_text("# one-time script\n")

        captured_cmds: list[list[str]] = []

        def fake_run(cmd: list[str]) -> None:
            captured_cmds.append(cmd)

        argv = ["retire_maintenance_op.py", "--op", "my-op"]
        if no_push:
            argv.append("--no-push")

        # ---- Patch paths and helpers inside the module ----
        with (
            patch.object(rmo, "WORKFLOW_PATH", wf_path),
            patch.object(rmo, "WORKFLOWS_DIR", wf_dir),
            patch.dict(
                rmo.OP_EXCLUSIVE_INPUTS,
                {"my-op": []},
                clear=False,
            ),
            patch.dict(
                rmo.OP_SCRIPTS,
                {"my-op": str(fake_script)},
                clear=False,
            ),
            patch.object(rmo, "run", side_effect=fake_run),
            patch("sys.argv", argv),
        ):
            rmo.main()

        return captured_cmds, fake_script

    def test_script_deleted_from_disk_after_retire(self, tmp_path):
        """The associated script file is removed from the filesystem."""
        _, fake_script = self._run_main_with_mocks(tmp_path, script_exists=True)
        assert not fake_script.exists()

    def test_git_rm_cached_called_for_deleted_script(self, tmp_path):
        """git rm --cached is called to stage the deletion."""
        cmds, fake_script = self._run_main_with_mocks(tmp_path, script_exists=True, no_push=False)
        script_str = str(fake_script)
        rm_cached_calls = [
            c for c in cmds if len(c) >= 3 and c[:3] == ["git", "rm", "--cached"]
        ]
        assert any(script_str in c for c in rm_cached_calls), (
            f"Expected 'git rm --cached' for {script_str}, got: {cmds}"
        )

    def test_git_add_u_NOT_called_after_rm_cached(self, tmp_path):
        """Regression: git add -u must NOT be called for the script path.

        Previously, retire_maintenance_op.py called ``git add -u <script>``
        after ``git rm --cached <script>``, which fails with exit code 128
        because git rm --cached already removes the path from the index.
        """
        cmds, fake_script = self._run_main_with_mocks(tmp_path, script_exists=True, no_push=False)
        script_str = str(fake_script)
        add_u_for_script = [
            c for c in cmds if len(c) >= 2 and c[:2] == ["git", "add"] and "-u" in c and script_str in c
        ]
        assert add_u_for_script == [], (
            f"git add -u should NOT be called for the script path, but got: {add_u_for_script}"
        )

    def test_no_push_skips_all_git_commands(self, tmp_path):
        """--no-push flag causes main() to skip all git commands."""
        cmds, _ = self._run_main_with_mocks(tmp_path, script_exists=True, no_push=True)
        # With --no-push, no git commands should be issued at all.
        git_cmds = [c for c in cmds if c and c[0] == "git"]
        assert git_cmds == [], f"Expected no git commands with --no-push, got: {git_cmds}"

    def test_no_crash_when_script_already_absent(self, tmp_path):
        """Retiring an op whose script is already gone raises no exception."""
        # Should complete without error.
        cmds, fake_script = self._run_main_with_mocks(tmp_path, script_exists=False)
        assert not fake_script.exists()
