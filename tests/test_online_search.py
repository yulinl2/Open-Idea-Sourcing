"""Tests for open_idea_sourcing.online_search."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from open_idea_sourcing.online_search import (
    OnlineReferenceSearch,
    _extract_query_from_abstract,
    _parse_semantic_scholar_item,
)
from open_idea_sourcing.reference_store import ReferencePaper


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_SAMPLE_ITEM = {
    "paperId": "abc123",
    "title": "Attention Is All You Need",
    "abstract": "We propose the Transformer architecture.",
    "year": 2017,
    "authors": [{"authorId": "1", "name": "Vaswani"}, {"authorId": "2", "name": "Shazeer"}],
    "externalIds": {"ArXiv": "1706.03762"},
    "url": "https://www.semanticscholar.org/paper/abc123",
}

_SAMPLE_API_RESPONSE = {
    "total": 1,
    "offset": 0,
    "data": [_SAMPLE_ITEM],
}


def _make_mock_response(body: bytes, status: int = 200):
    """Return a context-manager mock that simulates urllib.request.urlopen."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# _parse_semantic_scholar_item
# ---------------------------------------------------------------------------


class TestParseSemanticScholarItem:
    def test_parses_full_item(self):
        paper = _parse_semantic_scholar_item(_SAMPLE_ITEM)
        assert paper is not None
        assert paper.id == "abc123"
        assert paper.title == "Attention Is All You Need"
        assert paper.abstract == "We propose the Transformer architecture."
        assert paper.year == 2017
        assert "Vaswani" in paper.authors
        assert "Shazeer" in paper.authors

    def test_url_from_response(self):
        paper = _parse_semantic_scholar_item(_SAMPLE_ITEM)
        assert paper is not None
        assert paper.url == "https://www.semanticscholar.org/paper/abc123"

    def test_url_falls_back_to_arxiv(self):
        item = dict(_SAMPLE_ITEM)
        item["url"] = None
        paper = _parse_semantic_scholar_item(item)
        assert paper is not None
        assert paper.url == "https://arxiv.org/abs/1706.03762"

    def test_url_empty_when_no_arxiv_and_no_url(self):
        item = dict(_SAMPLE_ITEM)
        item["url"] = None
        item["externalIds"] = {}
        paper = _parse_semantic_scholar_item(item)
        assert paper is not None
        assert paper.url == ""

    def test_returns_none_when_paper_id_missing(self):
        item = dict(_SAMPLE_ITEM)
        del item["paperId"]
        assert _parse_semantic_scholar_item(item) is None

    def test_returns_none_when_title_missing(self):
        item = dict(_SAMPLE_ITEM)
        item["title"] = None
        assert _parse_semantic_scholar_item(item) is None

    def test_returns_none_when_title_empty_string(self):
        item = dict(_SAMPLE_ITEM)
        item["title"] = "   "
        assert _parse_semantic_scholar_item(item) is None

    def test_handles_missing_abstract(self):
        item = dict(_SAMPLE_ITEM)
        item["abstract"] = None
        paper = _parse_semantic_scholar_item(item)
        assert paper is not None
        assert paper.abstract == ""

    def test_handles_missing_authors(self):
        item = dict(_SAMPLE_ITEM)
        item["authors"] = None
        paper = _parse_semantic_scholar_item(item)
        assert paper is not None
        assert paper.authors == []

    def test_handles_non_integer_year(self):
        item = dict(_SAMPLE_ITEM)
        item["year"] = "2017"  # string instead of int
        paper = _parse_semantic_scholar_item(item)
        assert paper is not None
        assert paper.year is None

    def test_handles_missing_year(self):
        item = dict(_SAMPLE_ITEM)
        del item["year"]
        paper = _parse_semantic_scholar_item(item)
        assert paper is not None
        assert paper.year is None

    def test_returns_reference_paper_instance(self):
        paper = _parse_semantic_scholar_item(_SAMPLE_ITEM)
        assert isinstance(paper, ReferencePaper)


# ---------------------------------------------------------------------------
# _extract_query_from_abstract
# ---------------------------------------------------------------------------


class TestExtractQueryFromAbstract:
    def test_returns_up_to_max_words(self):
        abstract = " ".join(f"word{i}" for i in range(30))
        result = _extract_query_from_abstract(abstract, max_words=15)
        assert len(result.split()) == 15

    def test_returns_full_abstract_when_shorter_than_max(self):
        abstract = "Short abstract text."
        result = _extract_query_from_abstract(abstract, max_words=15)
        assert result == abstract

    def test_empty_abstract_returns_empty_string(self):
        assert _extract_query_from_abstract("") == ""

    def test_default_max_words_is_15(self):
        abstract = " ".join(f"w{i}" for i in range(20))
        result = _extract_query_from_abstract(abstract)
        assert len(result.split()) == 15


# ---------------------------------------------------------------------------
# OnlineReferenceSearch._query
# ---------------------------------------------------------------------------


class TestOnlineReferenceSearchQuery:
    def test_successful_query_returns_papers(self):
        body = json.dumps(_SAMPLE_API_RESPONSE).encode()
        mock_resp = _make_mock_response(body)

        searcher = OnlineReferenceSearch()
        with patch("urllib.request.urlopen", return_value=mock_resp):
            papers = searcher._query("Attention Is All You Need")

        assert len(papers) == 1
        assert papers[0].id == "abc123"
        assert papers[0].title == "Attention Is All You Need"

    def test_network_error_returns_empty_list(self):
        searcher = OnlineReferenceSearch()
        with patch("urllib.request.urlopen", side_effect=OSError("network down")):
            papers = searcher._query("any query")
        assert papers == []

    def test_invalid_json_returns_empty_list(self):
        mock_resp = _make_mock_response(b"not json")
        searcher = OnlineReferenceSearch()
        with patch("urllib.request.urlopen", return_value=mock_resp):
            papers = searcher._query("any query")
        assert papers == []

    def test_empty_data_list_returns_empty(self):
        body = json.dumps({"total": 0, "data": []}).encode()
        mock_resp = _make_mock_response(body)
        searcher = OnlineReferenceSearch()
        with patch("urllib.request.urlopen", return_value=mock_resp):
            papers = searcher._query("obscure query")
        assert papers == []

    def test_items_without_required_fields_are_skipped(self):
        body = json.dumps({
            "data": [
                {"paperId": None, "title": "Missing ID"},
                {"paperId": "ok1", "title": "Valid Paper", "year": 2020,
                 "abstract": "", "authors": [], "externalIds": {}, "url": ""},
            ]
        }).encode()
        mock_resp = _make_mock_response(body)
        searcher = OnlineReferenceSearch()
        with patch("urllib.request.urlopen", return_value=mock_resp):
            papers = searcher._query("test")
        assert len(papers) == 1
        assert papers[0].id == "ok1"

    def test_request_uses_correct_user_agent(self):
        body = json.dumps({"data": []}).encode()
        mock_resp = _make_mock_response(body)
        captured_req = {}

        def fake_urlopen(req, timeout=None):
            captured_req["req"] = req
            return mock_resp

        searcher = OnlineReferenceSearch()
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            searcher._query("test")

        assert "open-idea-sourcing" in captured_req["req"].get_header("User-agent")

    def test_query_param_is_url_encoded(self):
        body = json.dumps({"data": []}).encode()
        mock_resp = _make_mock_response(body)
        captured_url = {}

        def fake_urlopen(req, timeout=None):
            captured_url["url"] = req.full_url
            return mock_resp

        searcher = OnlineReferenceSearch()
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            searcher._query("attention mechanism transformers")

        assert "query=attention+mechanism+transformers" in captured_url["url"] or \
               "query=attention%20mechanism%20transformers" in captured_url["url"]


# ---------------------------------------------------------------------------
# OnlineReferenceSearch.search
# ---------------------------------------------------------------------------


class TestOnlineReferenceSearchSearch:
    def _make_api_response(self, paper_ids: list[str]) -> bytes:
        data = [
            {
                "paperId": pid,
                "title": f"Paper {pid}",
                "abstract": "Some abstract text.",
                "year": 2020,
                "authors": [],
                "externalIds": {},
                "url": f"https://example.com/{pid}",
            }
            for pid in paper_ids
        ]
        return json.dumps({"total": len(data), "data": data}).encode()

    def test_returns_papers_from_title_query(self):
        body = self._make_api_response(["p1", "p2", "p3"])
        mock_resp = _make_mock_response(body)
        searcher = OnlineReferenceSearch(max_results=5)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            papers = searcher.search("My Paper Title")
        assert len(papers) == 3

    def test_fallback_query_used_when_primary_sparse(self):
        """When the title query returns too few results, the abstract query fires."""
        # First call returns 1 paper (sparse), second call returns 3 more.
        resp1 = self._make_api_response(["p1"])
        resp2 = self._make_api_response(["p2", "p3", "p4"])

        call_count = {"n": 0}

        def fake_urlopen(req, timeout=None):
            call_count["n"] += 1
            body = resp1 if call_count["n"] == 1 else resp2
            return _make_mock_response(body)

        searcher = OnlineReferenceSearch(max_results=5)
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            papers = searcher.search(
                "Sparse Title",
                abstract="Some detailed abstract about neural networks.",
            )

        assert call_count["n"] == 2  # both queries fired
        assert len(papers) == 4  # p1 + p2 + p3 + p4

    def test_no_fallback_when_primary_sufficient(self):
        """When primary returns enough results, no second query is made."""
        body = self._make_api_response(["p1", "p2", "p3", "p4", "p5"])
        call_count = {"n": 0}

        def fake_urlopen(req, timeout=None):
            call_count["n"] += 1
            return _make_mock_response(body)

        searcher = OnlineReferenceSearch(max_results=5)
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            papers = searcher.search("Rich Title", abstract="Some abstract.")

        assert call_count["n"] == 1

    def test_fallback_not_used_when_abstract_empty(self):
        resp1 = self._make_api_response(["p1"])
        call_count = {"n": 0}

        def fake_urlopen(req, timeout=None):
            call_count["n"] += 1
            return _make_mock_response(resp1)

        searcher = OnlineReferenceSearch(max_results=5)
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            papers = searcher.search("Any Title", abstract="")

        assert call_count["n"] == 1

    def test_duplicates_deduplicated(self):
        """Papers with the same ID from both queries should appear only once."""
        body = self._make_api_response(["p1", "p2"])
        call_count = {"n": 0}

        def fake_urlopen(req, timeout=None):
            call_count["n"] += 1
            return _make_mock_response(body)

        searcher = OnlineReferenceSearch(max_results=5)
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            papers = searcher.search("Title", abstract="abstract triggers fallback")

        ids = [p.id for p in papers]
        assert len(ids) == len(set(ids))

    def test_max_results_respected(self):
        body = self._make_api_response([f"p{i}" for i in range(20)])
        mock_resp = _make_mock_response(body)
        searcher = OnlineReferenceSearch(max_results=3)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            papers = searcher.search("My Title")
        assert len(papers) <= 3

    def test_network_error_returns_empty_list(self):
        searcher = OnlineReferenceSearch()
        with patch("urllib.request.urlopen", side_effect=OSError("offline")):
            papers = searcher.search("Any Title", abstract="Any abstract.")
        assert papers == []

    def test_timeout_error_returns_empty_list(self):
        import socket
        searcher = OnlineReferenceSearch(timeout=1)
        with patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
            papers = searcher.search("Any Title")
        assert papers == []
