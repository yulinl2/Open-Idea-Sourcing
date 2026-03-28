"""Smoke tests for the ip_debate package scaffold (v0.0.0)."""

import pytest

import ip_debate
from ip_debate import __version__
from ip_debate.report import OutputFormat, format_report, suggest_filename
from ip_debate.run import _build_parser, main


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


# ---------------------------------------------------------------------------
# run.py CLI — argument parser interface (debate-track entrypoint)
# ---------------------------------------------------------------------------

def test_run_parser_paper_url():
    """--paper-url is parsed correctly."""
    parser = _build_parser()
    args = parser.parse_args(["--paper-url", "https://arxiv.org/abs/1234.5678"])
    assert args.paper_url == "https://arxiv.org/abs/1234.5678"
    assert args.papers_file == ""


def test_run_parser_papers_file():
    """--papers-file is parsed correctly."""
    parser = _build_parser()
    args = parser.parse_args(["--papers-file", "data/batch.ndjson"])
    assert args.papers_file == "data/batch.ndjson"
    assert args.paper_url == ""


def test_run_parser_paper_url_and_papers_file_mutually_exclusive():
    """--paper-url and --papers-file cannot both be given."""
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["--paper-url", "https://arxiv.org/abs/1", "--papers-file", "f.ndjson"]
        )


def test_run_parser_debate_mode_default():
    parser = _build_parser()
    args = parser.parse_args(["--paper-url", "https://arxiv.org/abs/1"])
    assert args.debate_mode == "crewai"


def test_run_parser_debate_mode_choices():
    parser = _build_parser()
    for mode in ("crewai", "wasserstein", "hybrid"):
        args = parser.parse_args(["--paper-url", "u", "--debate-mode", mode])
        assert args.debate_mode == mode


def test_run_parser_invalid_debate_mode():
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--paper-url", "u", "--debate-mode", "unknown"])


def test_run_parser_output_format_default():
    parser = _build_parser()
    args = parser.parse_args(["--paper-url", "u"])
    assert args.output_format == "markdown"


def test_run_parser_output_format_choices():
    parser = _build_parser()
    for fmt in ("text", "markdown", "json"):
        args = parser.parse_args(["--paper-url", "u", "--output-format", fmt])
        assert args.output_format == fmt


def test_run_main_raises_not_implemented():
    """main() raises NotImplementedError (pipeline stub) when args are valid."""
    with pytest.raises(NotImplementedError):
        main(["--paper-url", "https://arxiv.org/abs/1234.5678"])


def test_run_main_requires_input_source():
    """main() exits with an error when neither --paper-url nor --papers-file given."""
    with pytest.raises(SystemExit):
        main([])


def test_run_module_is_separate_from_baseline():
    """run.py must not import anything from open_idea_sourcing."""
    import importlib
    import sys
    # Reload the module and check its globals contain no baseline imports.
    mod = importlib.import_module("ip_debate.run")
    baseline_imports = [
        name for name in vars(mod)
        if name.startswith("open_idea_sourcing") or name == "review_paper"
    ]
    assert baseline_imports == [], (
        f"ip_debate.run must not depend on the baseline: {baseline_imports}"
    )
