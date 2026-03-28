"""Reporting interface stub for the IP debate / reconstruction pipeline.

Mirrors the :mod:`open_idea_sourcing.report_generator` contract so the same
dispatch workflow can publish outputs without changes to the CI plumbing —
all functions here raise :class:`NotImplementedError` until the pipeline
internals are built.
"""

from __future__ import annotations

from typing import Any, Literal

OutputFormat = Literal["text", "markdown", "json"]


def format_report(result: Any, fmt: OutputFormat = "text") -> str:
    """Format a pipeline result as a human-readable string.

    Parameters
    ----------
    result:
        Pipeline result object (TBD — data model not yet defined).
    fmt:
        Output format: one of ``"text"``, ``"markdown"``, or ``"json"``.

    Returns
    -------
    str
        Formatted report.

    Raises
    ------
    NotImplementedError
        Always — pipeline not yet implemented (v0.0.0 stub).
    """
    raise NotImplementedError(
        "ip_debate pipeline not yet implemented (v0.0.0 stub)."
        " Build the pipeline first, then replace this stub."
    )


def suggest_filename(result: Any, fmt: OutputFormat = "text") -> str:
    """Suggest an output filename for a pipeline result.

    Mirrors the :func:`open_idea_sourcing.report_generator.suggest_filename`
    API so dispatch workflows can use a uniform naming convention across both
    build tracks.

    Returns
    -------
    str
        A suggested filename.

    Raises
    ------
    NotImplementedError
        Always — pipeline not yet implemented (v0.0.0 stub).
    """
    raise NotImplementedError(
        "ip_debate pipeline not yet implemented (v0.0.0 stub)."
        " Build the pipeline first, then replace this stub."
    )
