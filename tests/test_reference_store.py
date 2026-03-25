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
        store.load(str(path), source="bundled")
        assert store.get_source("p1") == "bundled"

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
        assert store.get_source("b1") == "bundled"

    def test_remove_also_clears_source(self):
        store = ReferenceStore()
        paper = ReferencePaper(id="p1", title="Paper 1", abstract="")
        store.add(paper, source="online")
        store.remove("p1")
        assert store.get_source("p1") == ""

    def test_overwrite_updates_source(self):
        store = ReferenceStore()
        paper = ReferencePaper(id="p1", title="Paper 1", abstract="")
        store.add(paper, source="bundled")
        store.add(paper, source="online")
        assert store.get_source("p1") == "online"

    def test_multiple_sources_tracked_independently(self):
        store = ReferenceStore()
        store.add(ReferencePaper(id="b1", title="B", abstract=""), source="bundled")
        store.add(ReferencePaper(id="u1", title="U", abstract=""), source="user")
        store.add(ReferencePaper(id="o1", title="O", abstract=""), source="online")
        assert store.get_source("b1") == "bundled"
        assert store.get_source("u1") == "user"
        assert store.get_source("o1") == "online"
