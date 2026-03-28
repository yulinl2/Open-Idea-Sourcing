"""Smoke tests for the ip_debate package scaffold (v0.0.0)."""

import pytest

import ip_debate
from ip_debate import __version__
from ip_debate.report import OutputFormat, format_report, suggest_filename


# ---------------------------------------------------------------------------
# Package version
# ---------------------------------------------------------------------------

def test_version_is_0_0_0():
    assert __version__ == "0.0.0"


def test_version_attribute_on_package():
    assert hasattr(ip_debate, "__version__")
    assert isinstance(ip_debate.__version__, str)


# ---------------------------------------------------------------------------
# Reporting interface — stubs raise NotImplementedError
# ---------------------------------------------------------------------------

def test_format_report_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        format_report(None)


def test_format_report_raises_not_implemented_all_formats():
    for fmt in ("text", "markdown", "json"):
        with pytest.raises(NotImplementedError):
            format_report(object(), fmt=fmt)  # type: ignore[arg-type]


def test_suggest_filename_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        suggest_filename(None)


def test_suggest_filename_raises_not_implemented_all_formats():
    for fmt in ("text", "markdown", "json"):
        with pytest.raises(NotImplementedError):
            suggest_filename(object(), fmt=fmt)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# OutputFormat type alias is exported
# ---------------------------------------------------------------------------

def test_output_format_type_alias_exported():
    # OutputFormat is a Literal type alias — just verify it is importable and
    # that the three expected string values are captured in its __args__.
    assert set(OutputFormat.__args__) == {"text", "markdown", "json"}  # type: ignore[attr-defined]
