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

# Priority order for source deduplication (lower value = higher priority).
# When the same paper is added from multiple sources, the highest-priority
# source wins as the primary label; all source tags are always retained.
_SOURCE_PRIORITY: dict[str, int] = {
    "user": 0,
    "paper-cited": 1,
    "online": 2,
    "domain": 3,
    "unknown": 99,
}


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
        self._sources: dict[str, str] = {}  # primary (highest-priority) source tag
        self._all_sources: dict[str, set[str]] = {}  # all observed source tags

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(self, paper: ReferencePaper, source: str = "unknown") -> None:
        """Add or update a reference paper, respecting source priority.

        When the same paper (matched by *paper.id*) is added from multiple
        sources, the *primary* source stored by :meth:`get_source` follows
        the priority order::

            user > paper-cited > online > domain > unknown

        All observed source tags are always retained and accessible via
        :meth:`get_all_sources`, so the full provenance history is never
        lost.

        Parameters
        ----------
        paper:
            The reference paper to add.
        source:
            Where this paper originated.  Conventional labels are
            ``"user"``, ``"paper-cited"``, ``"online"``, and
            ``"domain"``.  Defaults to ``"unknown"`` for backward
            compatibility.
        """
        # Always track every source tag seen for this paper.
        if paper.id not in self._all_sources:
            self._all_sources[paper.id] = set()
        self._all_sources[paper.id].add(source)

        # Update the *primary* source only when the new source has strictly
        # higher priority than the currently stored one.
        existing = self._sources.get(paper.id)
        if existing is None:
            self._sources[paper.id] = source
        else:
            if _SOURCE_PRIORITY.get(source, _SOURCE_PRIORITY["unknown"]) < _SOURCE_PRIORITY.get(existing, _SOURCE_PRIORITY["unknown"]):
                self._sources[paper.id] = source

        self._papers[paper.id] = paper

    def get(self, paper_id: str) -> Optional[ReferencePaper]:
        return self._papers.get(paper_id)

    def get_source(self, paper_id: str) -> str:
        """Return the highest-priority source label for *paper_id*.

        Returns an empty string when *paper_id* is not tracked (i.e. has never
        been added to this store).  For tracked papers the returned label is
        always non-empty (at minimum ``"unknown"``).
        """
        return self._sources.get(paper_id, "")

    def get_all_sources(self, paper_id: str) -> set[str]:
        """Return the set of *all* source tags ever recorded for *paper_id*.

        Returns an empty set when *paper_id* is not tracked.  When a paper
        has been added from multiple sources (e.g. the same paper appears in
        both ``"user"`` refs and was also found via ``"online"`` search), all
        tags are present in the returned set, regardless of which won the
        priority contest for :meth:`get_source`.
        """
        return set(self._all_sources.get(paper_id, set()))

    def remove(self, paper_id: str) -> bool:
        if paper_id in self._papers:
            del self._papers[paper_id]
            self._sources.pop(paper_id, None)
            self._all_sources.pop(paper_id, None)
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

    def load(self, path: str | Path, source: str = "user") -> None:
        """Load papers from a JSON file, merging into the current store.

        Parameters
        ----------
        path:
            Path to a JSON file containing a list of reference paper
            objects (as produced by :meth:`save`).
        source:
            Source label applied to every paper loaded from this file.
            Defaults to ``"user"`` (the most common call-site usage).
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
