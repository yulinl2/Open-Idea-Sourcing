"""
infra/run_context.py

RunContext: the canonical run metadata container.

Every agent-track run must create a RunContext at startup and pass it through
to the report writer. The context serialises to the YAML front matter of report.md
and serves as the audit anchor for cross-run comparison.

Cherry-pick contract: do not modify the field names or serialisation format
without bumping the schema version; track branches may add fields but must not
remove or rename base fields.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _git_commit_hash() -> str:
    """Return the current HEAD short hash, or 'unknown' if unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


@dataclass
class RunContext:
    """
    Canonical run metadata for one agent-track paper review.

    Required fields (must be present in every report.md front matter):
      track, impl_id, paper_id, paper_source, model, tool_list,
      start_time, finish_time, git_commit, final_verdict, confidence,
      main_cited_evidence

    Optional fields:
      response_id — set if the underlying SDK returns a run/response ID
    """

    # --- identity ---
    track: str                          # e.g. "e2e", "linear", "reconstruct"
    impl_id: str                        # e.g. "e2e_v1_0_0"

    # --- paper ---
    paper_id: str                       # e.g. arXiv ID "2006.06138"
    paper_source: str                   # URL or file path used

    # --- model ---
    model: str                          # e.g. "gpt-4o", "claude-3-5-sonnet"
    response_id: str = ""               # SDK run/response ID if available

    # --- tools ---
    tool_list: list[str] = field(default_factory=list)

    # --- timing ---
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finish_time: str = ""

    # --- provenance ---
    git_commit: str = field(default_factory=_git_commit_hash)

    # --- verdict ---
    final_verdict: str = ""             # NOVEL | COMBINATION | EQUIVALENT | DUPLICATE
    confidence: float = 0.0            # 0.0–1.0
    main_cited_evidence: list[str] = field(default_factory=list)

    def mark_finished(self) -> None:
        """Call when the run completes to record the finish timestamp."""
        self.finish_time = datetime.now(timezone.utc).isoformat()

    def record_tool(self, tool_name: str) -> None:
        """Record that a tool was used in this run."""
        if tool_name not in self.tool_list:
            self.tool_list.append(tool_name)

    def to_yaml_front_matter(self) -> str:
        """
        Serialise to YAML front matter for embedding in report.md.

        Returns the block including the opening and closing '---' delimiters.
        """
        lines = ["---"]
        lines.append(f"track: {self.track}")
        lines.append(f"impl_id: {self.impl_id}")
        lines.append(f"paper_id: {self.paper_id}")
        lines.append(f"paper_source: {self.paper_source}")
        lines.append(f"model: {self.model}")
        if self.response_id:
            lines.append(f"response_id: {self.response_id}")
        tool_list_yaml = ", ".join(self.tool_list) if self.tool_list else "none"
        lines.append(f"tool_list: [{tool_list_yaml}]")
        lines.append(f"start_time: {self.start_time}")
        lines.append(f"finish_time: {self.finish_time}")
        lines.append(f"git_commit: {self.git_commit}")
        lines.append(f"final_verdict: {self.final_verdict}")
        lines.append(f"confidence: {self.confidence:.2f}")
        if self.main_cited_evidence:
            lines.append("main_cited_evidence:")
            for ev in self.main_cited_evidence:
                lines.append(f"  - {ev}")
        else:
            lines.append("main_cited_evidence: []")
        lines.append("---")
        return "\n".join(lines)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunContext":
        """Reconstruct a RunContext from a deserialized YAML/JSON dict."""
        return cls(
            track=data.get("track", ""),
            impl_id=data.get("impl_id", ""),
            paper_id=data.get("paper_id", ""),
            paper_source=data.get("paper_source", ""),
            model=data.get("model", ""),
            response_id=data.get("response_id", ""),
            tool_list=list(data.get("tool_list", [])),
            start_time=data.get("start_time", ""),
            finish_time=data.get("finish_time", ""),
            git_commit=data.get("git_commit", "unknown"),
            final_verdict=data.get("final_verdict", ""),
            confidence=float(data.get("confidence", 0.0)),
            main_cited_evidence=list(data.get("main_cited_evidence", [])),
        )
