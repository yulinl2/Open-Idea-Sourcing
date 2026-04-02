"""Tests for open_idea_sourcing.reference_store."""

import json
import pytest

from open_idea_sourcing.reference_store import ReferencePaper, ReferenceStore


def _make_paper(pid: str = "p1") -> ReferencePaper:
    return ReferencePaper(
        id=pid,
        title=f"Paper {pid}",
        abstract=f"Abstract for {pid}",
        authors=["Alice", "Bob"],
        year=2020,
        venue="NeurIPS",
    )


class TestReferenceStore:
    def setup_method(self):
        self.store = ReferenceStore()

    def test_add_and_retrieve(self):
        p = _make_paper("p1")
        self.store.add(p)
        assert self.store.get("p1") is p

    def test_get_missing_returns_none(self):
        assert self.store.get("nonexistent") is None

    def test_remove_existing(self):
        self.store.add(_make_paper("p1"))
        removed = self.store.remove("p1")
        assert removed is True
        assert self.store.get("p1") is None

    def test_remove_missing_returns_false(self):
        assert self.store.remove("ghost") is False

    def test_len(self):
        assert len(self.store) == 0
        self.store.add(_make_paper("p1"))
        self.store.add(_make_paper("p2"))
        assert len(self.store) == 2

    def test_all_papers(self):
        self.store.add(_make_paper("a"))
        self.store.add(_make_paper("b"))
        ids = {p.id for p in self.store.all_papers()}
        assert ids == {"a", "b"}

    def test_add_overwrites_existing(self):
        p1 = _make_paper("p1")
        p1_updated = ReferencePaper(id="p1", title="Updated Title", abstract="New abstract")
        self.store.add(p1)
        self.store.add(p1_updated)
        assert self.store.get("p1").title == "Updated Title"
        assert len(self.store) == 1

    def test_save_and_load(self, tmp_path):
        p = _make_paper("p1")
        self.store.add(p)
        path = tmp_path / "refs.json"
        self.store.save(str(path))

        new_store = ReferenceStore()
        new_store.load(str(path))
        loaded = new_store.get("p1")
        assert loaded is not None
        assert loaded.title == p.title
        assert loaded.year == p.year

    def test_from_file(self, tmp_path):
        p = _make_paper("p2")
        self.store.add(p)
        path = tmp_path / "refs.json"
        self.store.save(str(path))

        loaded_store = ReferenceStore.from_file(str(path))
        assert loaded_store.get("p2") is not None

    def test_save_creates_valid_json(self, tmp_path):
        self.store.add(_make_paper("p1"))
        path = tmp_path / "refs.json"
        self.store.save(str(path))
        data = json.loads(path.read_text())
        assert isinstance(data, list)
        assert data[0]["id"] == "p1"

    def test_searchable_text_combines_title_and_abstract(self):
        p = _make_paper("p1")
        assert p.title in p.searchable_text
        assert p.abstract in p.searchable_text

    def test_load_merges_with_existing(self, tmp_path):
        self.store.add(_make_paper("existing"))
        store2 = ReferenceStore()
        store2.add(_make_paper("from_file"))
        path = tmp_path / "refs.json"
        store2.save(str(path))

        self.store.load(str(path))
        assert self.store.get("existing") is not None
        assert self.store.get("from_file") is not None


# ---------------------------------------------------------------------------
# Source tracking
# ---------------------------------------------------------------------------

class TestReferenceStoreSourceTracking:
    def test_add_with_source_label(self):
        store = ReferenceStore()
        paper = ReferencePaper(id="p1", title="Paper 1", abstract="")
        store.add(paper, source="online")
        assert store.get_source("p1") == "online"

    def test_default_source_is_unknown(self):
        store = ReferenceStore()
        paper = ReferencePaper(id="p1", title="Paper 1", abstract="")
        store.add(paper)
        assert isinstance(store.get_source("p1"), str)
        assert store.get_source("p1") == "unknown"

    def test_get_source_missing_returns_empty(self):
        store = ReferenceStore()
        assert store.get_source("nonexistent") == ""

    def test_load_tags_papers_with_source(self, tmp_path):
        papers = [{"id": "p1", "title": "Paper 1", "abstract": "A.", "authors": [], "year": 2020}]
        path = tmp_path / "refs.json"
        import json
        path.write_text(json.dumps(papers), encoding="utf-8")
        store = ReferenceStore()
        store.load(str(path), source="user")
        assert store.get_source("p1") == "user"

    def test_load_user_source_label(self, tmp_path):
        papers = [{"id": "u1", "title": "User Paper", "abstract": "B.", "authors": [], "year": 2021}]
        path = tmp_path / "user_refs.json"
        import json
        path.write_text(json.dumps(papers), encoding="utf-8")
        store = ReferenceStore()
        store.load(str(path), source="user")
        assert store.get_source("u1") == "user"

    def test_load_default_source_is_bundled(self, tmp_path):
        papers = [{"id": "b1", "title": "Bundled Paper", "abstract": "C.", "authors": [], "year": 2019}]
        path = tmp_path / "bundled_refs.json"
        import json
        path.write_text(json.dumps(papers), encoding="utf-8")
        store = ReferenceStore()
        store.load(str(path))
        assert store.get_source("b1") == "user"

    def test_remove_also_clears_source(self):
        store = ReferenceStore()
        paper = ReferencePaper(id="p1", title="Paper 1", abstract="")
        store.add(paper, source="online")
        store.remove("p1")
        assert store.get_source("p1") == ""

    def test_overwrite_updates_source(self):
        # "user" has higher priority than "online", so adding with "online"
        # after "user" should NOT demote the primary source.
        store = ReferenceStore()
        paper = ReferencePaper(id="p1", title="Paper 1", abstract="")
        store.add(paper, source="user")
        store.add(paper, source="online")
        assert store.get_source("p1") == "user"

    def test_priority_lower_source_does_not_overwrite_higher(self):
        store = ReferenceStore()
        paper = ReferencePaper(id="p1", title="Paper 1", abstract="")
        store.add(paper, source="domain")
        store.add(paper, source="online")
        store.add(paper, source="paper-cited")
        store.add(paper, source="user")
        assert store.get_source("p1") == "user"

    def test_priority_higher_source_wins_regardless_of_order(self):
        store = ReferenceStore()
        paper = ReferencePaper(id="p1", title="Paper 1", abstract="")
        store.add(paper, source="online")
        store.add(paper, source="paper-cited")
        assert store.get_source("p1") == "paper-cited"

    def test_get_all_sources_tracks_every_tag(self):
        store = ReferenceStore()
        paper = ReferencePaper(id="p1", title="Paper 1", abstract="")
        store.add(paper, source="user")
        store.add(paper, source="online")
        store.add(paper, source="domain")
        assert store.get_all_sources("p1") == {"user", "online", "domain"}

    def test_get_all_sources_missing_returns_empty_set(self):
        store = ReferenceStore()
        assert store.get_all_sources("ghost") == set()

    def test_remove_also_clears_all_sources(self):
        store = ReferenceStore()
        paper = ReferencePaper(id="p1", title="Paper 1", abstract="")
        store.add(paper, source="user")
        store.add(paper, source="online")
        store.remove("p1")
        assert store.get_all_sources("p1") == set()

    def test_multiple_sources_tracked_independently(self):
        store = ReferenceStore()
        store.add(ReferencePaper(id="b1", title="B", abstract=""), source="user")
        store.add(ReferencePaper(id="u1", title="U", abstract=""), source="user")
        store.add(ReferencePaper(id="o1", title="O", abstract=""), source="online")
        assert store.get_source("b1") == "user"
        assert store.get_source("u1") == "user"
        assert store.get_source("o1") == "online"


# ---------------------------------------------------------------------------
# Title-based deduplication tests
# ---------------------------------------------------------------------------


class TestTitleBasedDedup:
    """ReferenceStore must reject papers whose titles match an existing entry."""

    def test_exact_duplicate_title_different_id_rejected(self):
        """Adding a paper with the same title under a different ID is a no-op."""
        store = ReferenceStore()
        title = "Model-Robust Counterfactual Prediction Method"
        p1 = ReferencePaper(id="id1", title=title, abstract="")
        p2 = ReferencePaper(id="id2", title=title, abstract="")
        store.add(p1)
        store.add(p2)
        assert len(store) == 1
        assert store.get("id1") is not None
        assert store.get("id2") is None

    def test_case_insensitive_title_dedup(self):
        """Title comparison is case-insensitive."""
        store = ReferenceStore()
        p1 = ReferencePaper(id="id1", title="Model-Robust Counterfactual Prediction Method", abstract="")
        p2 = ReferencePaper(id="id2", title="MODEL-ROBUST COUNTERFACTUAL PREDICTION METHOD", abstract="")
        store.add(p1)
        store.add(p2)
        assert len(store) == 1

    def test_garbled_prefix_title_dedup(self):
        """A garbled PDF-extraction prefix is detected via suffix containment.

        S2 sometimes returns a paper under two IDs: one with a clean title and
        one with a garbled header prepended (e.g. journal/date artefacts).
        The clean title should be kept; the garbled duplicate should be rejected.
        """
        from open_idea_sourcing.reference_store import _MIN_TITLE_SUFFIX_LEN
        clean_title = "Model-Robust Counterfactual Prediction Method for Long Papers"
        garbled_title = "ST ] 2 8 M ay 2 01 8 1 " + clean_title
        # Verify the clean title is long enough to trigger the check
        from open_idea_sourcing.reference_store import _alphanum_title_key
        assert len(_alphanum_title_key(clean_title)) >= _MIN_TITLE_SUFFIX_LEN

        store = ReferenceStore()
        p1 = ReferencePaper(id="clean", title=clean_title, abstract="")
        p2 = ReferencePaper(id="garbled", title=garbled_title, abstract="")

        # Add the clean title first; the garbled duplicate must be rejected.
        store.add(p1)
        store.add(p2)
        assert len(store) == 1
        assert store.get("clean") is not None
        assert store.get("garbled") is None

    def test_garbled_added_first_clean_rejected(self):
        """The first-added entry wins regardless of which title looks cleaner."""
        clean_title = "Model-Robust Counterfactual Prediction Method for Long Papers"
        garbled_title = "ST ] 2 8 M ay 2 01 8 1 " + clean_title

        store = ReferenceStore()
        p_garbled = ReferencePaper(id="garbled", title=garbled_title, abstract="")
        p_clean = ReferencePaper(id="clean", title=clean_title, abstract="")
        store.add(p_garbled)
        store.add(p_clean)
        assert len(store) == 1
        assert store.get("garbled") is not None
        assert store.get("clean") is None

    def test_distinct_titles_both_added(self):
        """Two papers with genuinely different titles are both kept."""
        store = ReferenceStore()
        p1 = ReferencePaper(id="a", title="Conformal Prediction Under Covariate Shift", abstract="")
        p2 = ReferencePaper(id="b", title="Distribution-Free Causal Inference via Counterfactual Prediction", abstract="")
        store.add(p1)
        store.add(p2)
        assert len(store) == 2

    def test_short_title_not_deduplicated_as_suffix(self):
        """Short titles below the suffix threshold are not collapsed."""
        from open_idea_sourcing.reference_store import _MIN_TITLE_SUFFIX_LEN, _alphanum_title_key
        short_title = "GPT-4"
        longer_title = "A Survey of Approaches Including GPT-4"
        # The short title must be below the threshold
        assert len(_alphanum_title_key(short_title)) < _MIN_TITLE_SUFFIX_LEN

        store = ReferenceStore()
        store.add(ReferencePaper(id="s", title=short_title, abstract=""))
        store.add(ReferencePaper(id="l", title=longer_title, abstract=""))
        # Both must be kept because the short title is below the dedup threshold
        assert len(store) == 2

    def test_same_id_readded_is_updated(self):
        """Re-adding the same paper ID always updates the record (no dedup block)."""
        store = ReferenceStore()
        title = "Model-Robust Counterfactual Prediction Method"
        p1 = ReferencePaper(id="id1", title=title, abstract="original")
        p2 = ReferencePaper(id="id1", title=title, abstract="updated")
        store.add(p1)
        store.add(p2)
        assert len(store) == 1
        assert store.get("id1").abstract == "updated"

    def test_remove_clears_title_index(self):
        """After removing a paper, its title slot is freed for a new entry."""
        title = "Model-Robust Counterfactual Prediction Method"
        store = ReferenceStore()
        p1 = ReferencePaper(id="id1", title=title, abstract="")
        p2 = ReferencePaper(id="id2", title=title, abstract="")
        store.add(p1)
        store.remove("id1")
        # Now the title slot is free; adding a different ID with the same title succeeds.
        store.add(p2)
        assert len(store) == 1
        assert store.get("id2") is not None

    def test_title_dedup_source_priority_preserved(self):
        """When a title-duplicate is rejected, the canonical entry's source is
        updated if the new entry's source has higher priority."""
        title = "Model-Robust Counterfactual Prediction Method"
        store = ReferenceStore()
        p_online = ReferencePaper(id="id_online", title=title, abstract="")
        p_user = ReferencePaper(id="id_user", title=title, abstract="")
        store.add(p_online, source="online")
        store.add(p_user, source="user")  # higher priority; should upgrade the canonical
        assert len(store) == 1
        assert store.get_source("id_online") == "user"
