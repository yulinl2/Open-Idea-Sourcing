"""Unit tests for scripts/check_pr_merge_readiness.py.

Tests the fail-closed, decision logic of evaluate_merge_readiness
against fixture PR metadata and required-check payloads.
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

import pytest

# Put scripts/ on sys.path so we can import the module directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_pr_merge_readiness import evaluate_merge_readiness  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pr(*, draft: bool = False, review_decision: str = "") -> dict:
    return {
        "number": 1,
        "title": "Test PR",
        "url": "https://github.com/owner/repo/pull/1",
        "isDraft": draft,
        "reviewDecision": review_decision,
    }


def _check(bucket: str, name: str = "CI") -> dict:
    return {"bucket": bucket, "name": name, "state": bucket.upper(), "workflow": "CI", "link": ""}


# ---------------------------------------------------------------------------
# Green path
# ---------------------------------------------------------------------------


def test_all_pass_not_blocked(capsys):
    checks = [_check("pass", "Run tests"), _check("pass", "Lint")]
    blocked = evaluate_merge_readiness(_pr(), checks)
    assert not blocked
    out = capsys.readouterr().out
    assert "OK: all required checks are green." in out


# ---------------------------------------------------------------------------
# PR-level blockers
# ---------------------------------------------------------------------------


def test_draft_is_blocked(capsys):
    blocked = evaluate_merge_readiness(_pr(draft=True), [_check("pass")])
    assert blocked
    assert "BLOCKED: PR is still a draft." in capsys.readouterr().out


def test_changes_requested_is_blocked(capsys):
    blocked = evaluate_merge_readiness(_pr(review_decision="CHANGES_REQUESTED"), [_check("pass")])
    assert blocked
    assert "BLOCKED: review decision is CHANGES_REQUESTED." in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Check-bucket blockers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bucket", ["fail", "pending", "cancel", "skipping"])
def test_non_pass_bucket_is_blocked(bucket, capsys):
    blocked = evaluate_merge_readiness(_pr(), [_check(bucket)])
    assert blocked
    out = capsys.readouterr().out
    assert "BLOCKED: required checks not all green:" in out
    assert f"[{bucket}]" in out


def test_mixed_checks_blocked_on_any_non_pass(capsys):
    checks = [_check("pass", "Lint"), _check("fail", "Run tests")]
    blocked = evaluate_merge_readiness(_pr(), checks)
    assert blocked
    out = capsys.readouterr().out
    assert "Run tests" in out
    assert "Lint" not in out  # pass bucket not listed as blocking


# ---------------------------------------------------------------------------
# Multiple co-occurring blockers
# ---------------------------------------------------------------------------


def test_draft_plus_failing_check_both_reported(capsys):
    blocked = evaluate_merge_readiness(_pr(draft=True), [_check("fail")])
    assert blocked
    out = capsys.readouterr().out
    assert "BLOCKED: PR is still a draft." in out
    assert "BLOCKED: required checks not all green:" in out


def test_changes_requested_plus_pending_both_reported(capsys):
    blocked = evaluate_merge_readiness(
        _pr(review_decision="CHANGES_REQUESTED"),
        [_check("pending", "Run tests")],
    )
    assert blocked
    out = capsys.readouterr().out
    assert "BLOCKED: review decision is CHANGES_REQUESTED." in out
    assert "BLOCKED: required checks not all green:" in out


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def test_output_includes_pr_header(capsys):
    evaluate_merge_readiness(_pr(), [_check("pass")])
    out = capsys.readouterr().out
    assert "PR #1: Test PR" in out
    assert "https://github.com/owner/repo/pull/1" in out


def test_blocking_check_output_format(capsys):
    check = {"bucket": "fail", "name": "Run tests", "state": "FAILURE", "workflow": "CI", "link": "https://example.com/run/1"}
    evaluate_merge_readiness(_pr(), [check])
    out = capsys.readouterr().out
    assert "[fail] CI :: Run tests (FAILURE) https://example.com/run/1" in out


def test_missing_check_fields_use_fallbacks(capsys):
    """A check dict with only 'bucket' set must not raise."""
    blocked = evaluate_merge_readiness(_pr(), [{"bucket": "fail"}])
    assert blocked
    out = capsys.readouterr().out
    assert "(no workflow)" in out
    assert "(unnamed check)" in out
