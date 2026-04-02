"""Manage a local store of reference papers used during novelty evaluation.

Papers are kept in memory (and can be persisted to / loaded from a JSON
file) so that the similarity search component can compare a submitted
paper against a known corpus.
"""

from __future__ import annotations

import json
import re
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

# Minimum number of alphanumeric characters in the shorter of two titles for
# the suffix-based duplicate check to trigger.  Keeps short titles (e.g.
# "GPT-4") from being falsely matched against longer titles that happen to
# share the same ending.
_MIN_TITLE_SUFFIX_LEN = 30


def _alphanum_title_key(title: str) -> str:
    """Return a lowercase, alphanumeric-only key for *title*.

    Used to detect title-based duplicates when the same paper is indexed
    under multiple Semantic Scholar IDs (e.g. preprint and journal version,
    or a garbled-prefix PDF-extraction artefact such as
    ``"ST ] 2 8 M ay 2 01 8 1 Model-Robust …"`` vs
    ``"Model-Robust …"``).
    """
    return re.sub(r'[^a-z0-9]', '', title.lower())


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
        # Mapping from alphanum title key → paper_id for title-based dedup.
        # When Semantic Scholar returns the same paper under multiple IDs
        # (e.g. preprint vs journal version, or a garbled-prefix PDF artefact),
        # this index lets us detect and skip the duplicate entry.
        self._title_keys: dict[str, str] = {}  # alphanum_key → paper_id

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

        Title-based deduplication is also applied: if a paper with an
        identical normalised title is already present (same paper indexed
        under a different Semantic Scholar ID), the new entry is silently
        dropped to avoid polluting the reference pool with duplicates.
        A suffix-containment check additionally catches PDF-extraction
        artefacts where the true title appears as a suffix of a garbled
        longer string (e.g. ``"ST ] 2 8 M ay … Model-Robust …"`` vs
        ``"Model-Robust …"``).

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
        new_key = _alphanum_title_key(paper.title)

        # Title-based duplicate check — skip if this paper is already
        # represented under a different S2 ID.
        if paper.id not in self._papers and new_key:
            for existing_key, existing_id in self._title_keys.items():
                if existing_id == paper.id:
                    # Same paper re-inserted under same id — fall through to
                    # the normal ID-based update path below.
                    break
                shorter = min(len(new_key), len(existing_key))
                if shorter < _MIN_TITLE_SUFFIX_LEN:
                    continue
                # Exact match or suffix containment (garbled-prefix artefact).
                if new_key == existing_key or new_key.endswith(existing_key) or existing_key.endswith(new_key):
                    # Duplicate by title — update source tracking for the
                    # canonical entry already in the store, then bail out.
                    self._all_sources.setdefault(existing_id, set()).add(source)
                    existing_src = self._sources.get(existing_id, "unknown")
                    if _SOURCE_PRIORITY.get(source, _SOURCE_PRIORITY["unknown"]) < _SOURCE_PRIORITY.get(existing_src, _SOURCE_PRIORITY["unknown"]):
                        self._sources[existing_id] = source
                    return

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

        # If this paper ID already existed with a different title, remove the
        # stale title-key entries before registering the updated key.
        if paper.id in self._papers:
            stale_keys = [
                k for k, pid in self._title_keys.items()
                if pid == paper.id and k != new_key
            ]
            for k in stale_keys:
                del self._title_keys[k]

        # Register the new key if it is non-empty and not yet claimed by a
        # different paper (first-entry-wins for title-based canonicalisation).
        if new_key:
            existing_id = self._title_keys.get(new_key)
            if existing_id is None or existing_id == paper.id:
                self._title_keys[new_key] = paper.id

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
            # Remove all title-index entries that point to this paper.
            keys_to_delete = [k for k, pid in self._title_keys.items() if pid == paper_id]
            for k in keys_to_delete:
                del self._title_keys[k]
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
