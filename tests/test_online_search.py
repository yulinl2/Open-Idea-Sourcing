"""Tests for open_idea_sourcing.online_search."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from open_idea_sourcing.online_search import OnlineReferenceSearch
from open_idea_sourcing.reference_store import ReferencePaper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_api_response(items: list[dict]) -> MagicMock:
    """Build a fake urllib response returning *items* as JSON."""
    payload = json.dumps({"data": items}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


_SAMPLE_ITEM = {
    "paperId": "abc123",
    "title": "Attention Is All You Need",
    "abstract": "We propose the Transformer.",
    "year": 2017,
    "authors": [{"name": "Vaswani"}, {"name": "Shazeer"}],
    "url": "https://www.semanticscholar.org/paper/abc123",
    "externalIds": {},
}


# ---------------------------------------------------------------------------
# OnlineReferenceSearch.search()
# ---------------------------------------------------------------------------

class TestOnlineReferenceSearchSearch:
    def test_returns_list_of_reference_papers(self):
        mock_resp = _make_api_response([_SAMPLE_ITEM])
        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch("time.sleep"):
            searcher = OnlineReferenceSearch(rate_limit_delay=0)
            results = searcher.search("attention transformer")

        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], ReferencePaper)

    def test_paper_fields_populated_correctly(self):
        mock_resp = _make_api_response([_SAMPLE_ITEM])
        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch("time.sleep"):
            searcher = OnlineReferenceSearch(rate_limit_delay=0)
            results = searcher.search("attention")

        paper = results[0]
        assert paper.id == "abc123"
        assert paper.title == "Attention Is All You Need"
        assert paper.abstract == "We propose the Transformer."
        assert paper.year == 2017
        assert "Vaswani" in paper.authors

    def test_url_from_semanticscholar_when_missing(self):
        item = dict(_SAMPLE_ITEM)
        item["url"] = ""
        mock_resp = _make_api_response([item])
        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch("time.sleep"):
            searcher = OnlineReferenceSearch(rate_limit_delay=0)
            results = searcher.search("attention")

        assert "abc123" in results[0].url

    def test_empty_query_returns_empty_list(self):
        searcher = OnlineReferenceSearch(rate_limit_delay=0)
        results = searcher.search("   ")
        assert results == []

    def test_network_error_returns_empty_list(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
            searcher = OnlineReferenceSearch(rate_limit_delay=0)
            results = searcher.search("transformer")
        assert results == []

    def test_json_decode_error_returns_empty_list(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            searcher = OnlineReferenceSearch(rate_limit_delay=0)
            results = searcher.search("transformer")
        assert results == []

    def test_max_results_capped_at_ten(self):
        captured = {}

        mock_resp = _make_api_response([])

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            searcher = OnlineReferenceSearch(rate_limit_delay=0)
            searcher.search("test", max_results=50)

        assert "limit=10" in captured["url"]

    def test_max_results_minimum_is_one(self):
        captured = {}
        mock_resp = _make_api_response([])

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            searcher = OnlineReferenceSearch(rate_limit_delay=0)
            searcher.search("test", max_results=0)

        assert "limit=1" in captured["url"]

    def test_missing_paper_id_skipped(self):
        item = dict(_SAMPLE_ITEM)
        item["paperId"] = ""
        item["externalIds"] = {}
        mock_resp = _make_api_response([item])
        with patch("urllib.request.urlopen", return_value=mock_resp):
            searcher = OnlineReferenceSearch(rate_limit_delay=0)
            results = searcher.search("test")
        assert results == []

    def test_multiple_results_returned(self):
        item2 = dict(_SAMPLE_ITEM)
        item2["paperId"] = "def456"
        item2["title"] = "BERT"
        mock_resp = _make_api_response([_SAMPLE_ITEM, item2])
        with patch("urllib.request.urlopen", return_value=mock_resp):
            searcher = OnlineReferenceSearch(rate_limit_delay=0)
            results = searcher.search("language models")
        assert len(results) == 2

    def test_rate_limit_throttle_called(self):
        mock_resp = _make_api_response([])
        sleep_calls = []
        with patch("urllib.request.urlopen", return_value=mock_resp), \
             patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)), \
             patch("time.monotonic", return_value=0.0):
            searcher = OnlineReferenceSearch(rate_limit_delay=1.0)
            searcher._last_request_time = 0.0
            searcher.search("test")
        # Should have slept because no time has passed
        assert len(sleep_calls) >= 1


# ---------------------------------------------------------------------------
# OnlineReferenceSearch._parse_paper()
# ---------------------------------------------------------------------------

class TestParsePaper:
    def test_returns_none_when_no_paper_id(self):
        result = OnlineReferenceSearch._parse_paper({"title": "Test"})
        assert result is None

    def test_year_none_when_missing(self):
        item = dict(_SAMPLE_ITEM)
        item["year"] = None
        result = OnlineReferenceSearch._parse_paper(item)
        assert result is not None
        assert result.year is None

    def test_authors_empty_list_when_missing(self):
        item = dict(_SAMPLE_ITEM)
        item["authors"] = []
        result = OnlineReferenceSearch._parse_paper(item)
        assert result is not None
        assert result.authors == []

    def test_doi_fallback_for_paper_id(self):
        item = {
            "paperId": "",
            "title": "DOI paper",
            "abstract": "",
            "year": 2020,
            "authors": [],
            "url": "",
            "externalIds": {"DOI": "10.1234/test"},
        }
        result = OnlineReferenceSearch._parse_paper(item)
        assert result is not None
        assert result.id == "10.1234/test"
