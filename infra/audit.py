"""Audit logging for reconstruction runs.

Records every LLM call, prompt, response, timing, and token usage
so that runs are fully reproducible and inspectable.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class StepRecord:
    """One LLM interaction or processing step."""
    step_name: str
    model: str = ""
    system_prompt: str = ""
    user_prompt: str = ""
    response: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    duration_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLog:
    """Full audit trail for a single reconstruction dispatch."""
    paper_id: str
    paper_url: str
    reconstruction_type: str
    student_model: str
    teacher_model: str
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finish_time: str = ""
    steps: list[StepRecord] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: StepRecord) -> None:
        self.steps.append(step)

    def mark_finished(self) -> None:
        self.finish_time = datetime.now(timezone.utc).isoformat()

    def total_input_tokens(self) -> int:
        return sum(s.input_tokens for s in self.steps)

    def total_output_tokens(self) -> int:
        return sum(s.output_tokens for s in self.steps)

    def total_duration(self) -> float:
        return sum(s.duration_seconds for s in self.steps)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2, default=str), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "AuditLog":
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = [StepRecord(**s) for s in data.pop("steps", [])]
        log = cls(**{k: v for k, v in data.items() if k != "steps"})
        log.steps = steps
        return log
