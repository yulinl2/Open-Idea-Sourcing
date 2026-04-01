"""
infra/__init__.py

Public surface of the infra package. Track branches cherry-pick the whole
infra/ directory; this __init__ re-exports the most commonly used symbols
so tracks can write:

    from infra import RunContext, ReportWriter, ToolRegistry
"""

from infra.run_context import RunContext
from infra.report_writer import ReportContent, ReportWriter, DerivationEntry, PriorWorkEntry
from infra.tool_registry import ToolRegistry
from infra.search_tools import (
    search_semantic_scholar,
    fetch_s2_citations,
    fetch_s2_paper,
    search_arxiv,
)
from infra.pdf_utils import extract_text_from_pdf

__all__ = [
    "RunContext",
    "ReportContent",
    "ReportWriter",
    "DerivationEntry",
    "PriorWorkEntry",
    "ToolRegistry",
    "search_semantic_scholar",
    "fetch_s2_citations",
    "fetch_s2_paper",
    "search_arxiv",
    "extract_text_from_pdf",
]
