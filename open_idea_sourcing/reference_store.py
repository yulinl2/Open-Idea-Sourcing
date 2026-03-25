"""Manage a local store of reference papers used during novelty evaluation.

Papers are kept in memory (and can be persisted to / loaded from a JSON
file) so that the similarity search component can compare a submitted
paper against a known corpus.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ReferencePaper:
    """Lightweight metadata record for a reference paper."""

    id: str
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    venue: str = ""
    url: str = ""

    @property
    def searchable_text(self) -> str:
        """Combined text used for similarity search."""
        return f"{self.title} {self.abstract}"


class ReferenceStore:
    """In-memory store of reference papers with optional JSON persistence."""

    def __init__(self) -> None:
        self._papers: dict[str, ReferencePaper] = {}
        self._sources: dict[str, str] = {}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(self, paper: ReferencePaper, source: str = "unknown") -> None:
        """Add or overwrite a reference paper, recording its *source* label.

        Parameters
        ----------
        paper:
            The reference paper to add.
        source:
            Where this paper originated.  Conventional labels are
            ``"bundled"``, ``"user"``, ``"paper-cited"``, and
            ``"online"``.  Defaults to ``"unknown"`` for backward
            compatibility.
        """
        self._papers[paper.id] = paper
        self._sources[paper.id] = source

    def get(self, paper_id: str) -> Optional[ReferencePaper]:
        return self._papers.get(paper_id)

    def get_source(self, paper_id: str) -> str:
        """Return the source label for *paper_id*, or ``""`` if unknown."""
        return self._sources.get(paper_id, "")

    def remove(self, paper_id: str) -> bool:
        if paper_id in self._papers:
            del self._papers[paper_id]
            self._sources.pop(paper_id, None)
            return True
        return False

    def all_papers(self) -> list[ReferencePaper]:
        return list(self._papers.values())

    def __len__(self) -> int:
        return len(self._papers)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> None:
        """Serialise the store to a JSON file."""
        data = [asdict(p) for p in self._papers.values()]
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: str | Path, source: str = "bundled") -> None:
        """Load papers from a JSON file, merging into the current store.

        Parameters
        ----------
        path:
            Path to a JSON file containing a list of reference paper
            objects (as produced by :meth:`save`).
        source:
            Source label applied to every paper loaded from this file.
            Defaults to ``"bundled"`` (the most common call-site usage).
        """
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        for item in raw:
            self.add(ReferencePaper(**item), source=source)

    @classmethod
    def from_file(cls, path: str | Path) -> "ReferenceStore":
        """Convenience constructor that loads from a JSON file."""
        store = cls()
        store.load(path)
        return store
