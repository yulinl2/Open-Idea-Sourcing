"""Tests for review_paper URL helpers and main() URL branch."""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import review_paper

# Import the helpers we want to test
from review_paper import _normalise_arxiv_url, _extract_arxiv_id, _download_paper, _build_llm, main
from open_idea_sourcing.reference_store import ReferenceStore

# ---------------------------------------------------------------------------
# _normalise_arxiv_url
# ---------------------------------------------------------------------------


class TestNormaliseArxivUrl:
    def test_abs_url_converted_to_pdf(self):
        assert _normalise_arxiv_url("https://arxiv.org/abs/2006.06138") == \
            "https://arxiv.org/pdf/2006.06138"

    def test_abs_url_with_version_converted(self):
        assert _normalise_arxiv_url("https://arxiv.org/abs/2006.06138v2") == \
            "https://arxiv.org/pdf/2006.06138v2"

    def test_pdf_url_unchanged(self):
        url = "https://arxiv.org/pdf/2006.06138"
        assert _normalise_arxiv_url(url) == url

    def test_non_arxiv_url_unchanged(self):
        url = "https://example.com/paper.pdf"
        assert _normalise_arxiv_url(url) == url

    def test_http_abs_url_converted(self):
        assert _normalise_arxiv_url("http://arxiv.org/abs/1234.5678") == \
            "http://arxiv.org/pdf/1234.5678"


# ---------------------------------------------------------------------------
# _extract_arxiv_id
# ---------------------------------------------------------------------------


class TestExtractArxivId:
    def test_abs_url_returns_id(self):
        assert _extract_arxiv_id("https://arxiv.org/abs/2006.06138") == "2006.06138"

    def test_pdf_url_returns_id(self):
        assert _extract_arxiv_id("https://arxiv.org/pdf/1706.03762") == "1706.03762"

    def test_abs_url_with_version(self):
        assert _extract_arxiv_id("https://arxiv.org/abs/2006.06138v2") == "2006.06138v2"

    def test_pdf_url_with_dot_pdf_suffix_returns_id(self):
        assert _extract_arxiv_id("https://arxiv.org/pdf/1706.03762.pdf") == "1706.03762"

    def test_pdf_url_with_version_and_dot_pdf_suffix_returns_id(self):
        assert _extract_arxiv_id("https://arxiv.org/pdf/2006.06138v2.pdf") == "2006.06138v2"

    def test_non_arxiv_url_returns_empty(self):
        assert _extract_arxiv_id("https://example.com/paper.pdf") == ""

    def test_local_path_returns_empty(self):
        assert _extract_arxiv_id("/path/to/paper.pdf") == ""

    def test_empty_string_returns_empty(self):
        assert _extract_arxiv_id("") == ""


# ---------------------------------------------------------------------------
# _download_paper
# ---------------------------------------------------------------------------


# 8.8.8.8 (Google Public DNS) is used because Python 3.12+ classifies TEST-NET
# addresses (e.g. 203.0.113.0/24) as private, which would trigger the IP check.
_FAKE_ADDRINFO = [(2, 1, 6, "", ("8.8.8.8", 0))]


class TestDownloadPaper:
    def test_downloads_pdf_to_dest_dir(self, tmp_path):
        fake_pdf_bytes = b"%PDF-1.4 fake content"
        mock_response = MagicMock()
        mock_response.getheader.return_value = None
        mock_response.geturl.return_value = "https://arxiv.org/pdf/2006.06138"
        mock_response.read.return_value = fake_pdf_bytes
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response), \
             patch("review_paper.socket.getaddrinfo", return_value=_FAKE_ADDRINFO):
            result = _download_paper("https://arxiv.org/pdf/2006.06138", str(tmp_path))

        assert result.exists()
        assert result.read_bytes() == fake_pdf_bytes

    def test_abs_url_normalised_before_download(self, tmp_path):
        """Abstract URL should be rewritten to PDF URL before the request."""
        fake_pdf_bytes = b"%PDF-1.4"
        mock_response = MagicMock()
        mock_response.getheader.return_value = None
        mock_response.geturl.return_value = "https://arxiv.org/pdf/2006.06138"
        mock_response.read.return_value = fake_pdf_bytes
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        captured = {}

        def fake_urlopen(req, timeout=None):  # timeout matches urlopen signature
            captured["url"] = req.full_url
            return mock_response

        with patch("urllib.request.urlopen", side_effect=fake_urlopen), \
             patch("review_paper.socket.getaddrinfo", return_value=_FAKE_ADDRINFO):
            _download_paper("https://arxiv.org/abs/2006.06138", str(tmp_path))

        assert captured["url"] == "https://arxiv.org/pdf/2006.06138"

    def test_network_error_raises_system_exit(self, tmp_path):
        with patch("urllib.request.urlopen", side_effect=OSError("network down")):
            with pytest.raises(SystemExit, match="network down"):
                _download_paper("https://arxiv.org/pdf/2006.06138", str(tmp_path))

    def test_http_url_rejected(self, tmp_path):
        """Plain http:// URLs should be rejected with a clear error."""
        with pytest.raises(SystemExit, match="only https://"):
            _download_paper("http://arxiv.org/pdf/2006.06138", str(tmp_path))

    def test_filename_gets_pdf_extension(self, tmp_path):
        """If the URL path has no .pdf suffix, one should be appended."""
        fake_pdf_bytes = b"%PDF-1.4"
        mock_response = MagicMock()
        mock_response.getheader.return_value = None
        mock_response.geturl.return_value = "https://arxiv.org/pdf/2006.06138"
        mock_response.read.return_value = fake_pdf_bytes
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response), \
             patch("review_paper.socket.getaddrinfo", return_value=_FAKE_ADDRINFO):
            result = _download_paper("https://arxiv.org/abs/2006.06138", str(tmp_path))

        assert result.suffix.lower() == ".pdf"


# ---------------------------------------------------------------------------
# main() — URL branch integration
# ---------------------------------------------------------------------------


class TestMainWithUrl:
    """Verify that main() accepts a URL, downloads the paper, and evaluates it."""

    _SAMPLE_TEXT = (
        "Attention Is All You Need\n\n"
        "Abstract\nWe propose the Transformer.\n\n"
        "1. Introduction\nNeural networks are great.\n"
    )

    def _make_fake_download(self, tmp_path: Path, text: str = _SAMPLE_TEXT):
        """Return a side-effect for _download_paper that writes a .txt file."""
        dest = tmp_path / "paper.txt"
        dest.write_text(text, encoding="utf-8")

        def fake_download(url: str, dest_dir: str) -> Path:
            return dest

        return fake_download

    def test_url_input_invokes_download(self, tmp_path):
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with (
            patch("review_paper._download_paper", side_effect=self._make_fake_download(tmp_path)),
            patch("review_paper._build_llm", return_value=fake_llm),
        ):
            rc = main(["https://arxiv.org/abs/2006.06138", "--format", "text",
                        "--reports-dir", str(tmp_path)])

        assert rc == 0

    def test_url_temp_dir_cleaned_up(self, tmp_path, monkeypatch):
        """Temp directory must be removed even after successful run."""
        created_dirs: list[str] = []
        real_mkdtemp = __import__("tempfile").mkdtemp

        def tracking_mkdtemp():
            d = real_mkdtemp()
            created_dirs.append(d)
            return d

        dest = tmp_path / "paper.txt"
        dest.write_text(self._SAMPLE_TEXT, encoding="utf-8")

        def fake_download(url: str, dest_dir: str) -> Path:
            return dest

        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: done.")

        with (
            patch("review_paper.tempfile.mkdtemp", side_effect=tracking_mkdtemp),
            patch("review_paper._download_paper", side_effect=fake_download),
            patch("review_paper._build_llm", return_value=fake_llm),
        ):
            main(["https://arxiv.org/abs/2006.06138", "--format", "text",
                  "--reports-dir", str(tmp_path)])

        for d in created_dirs:
            assert not Path(d).exists(), f"Temp dir {d} was not cleaned up"

    def test_file_path_still_works(self, tmp_path):
        """Passing a local file path must continue to work as before."""
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([str(paper), "--format", "text", "--reports-dir", str(tmp_path)])

        assert rc == 0

    def test_missing_file_returns_error(self, tmp_path):
        rc = main([str(tmp_path / "nonexistent.pdf")])
        assert rc == 1

    def test_bad_url_scheme_returns_error_not_raises(self):
        """main() must return 1 (not raise SystemExit) when URL has wrong scheme."""
        rc = main(["http://arxiv.org/pdf/2006.06138"])
        assert rc == 1

    def test_download_failure_returns_error_not_raises(self, tmp_path):
        """main() must return 1 (not raise SystemExit) on download failure."""
        with patch("urllib.request.urlopen", side_effect=OSError("network down")):
            rc = main(["https://arxiv.org/pdf/2006.06138"])
        assert rc == 1

    def test_parse_error_returns_error(self, tmp_path):
        """main() must return 1 with a message when parsing raises an exception."""
        paper = tmp_path / "paper.txt"
        paper.write_text("some content", encoding="utf-8")

        with patch(
            "review_paper.PaperParser.parse_file",
            side_effect=RuntimeError("corrupt file"),
        ):
            rc = main([str(paper)])

        assert rc == 1


class TestLoadEnvironment:
    def test_loads_repo_env_when_cwd_has_none(self, tmp_path, monkeypatch):
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".env").write_text("OPENAI_API_KEY=from_repo\n", encoding="utf-8")

        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)

        mock_loader = MagicMock()
        monkeypatch.setattr(review_paper, "load_dotenv", mock_loader)
        monkeypatch.setattr(review_paper, "__file__", str(repo_root / "review_paper.py"))

        review_paper._load_environment()

        mock_loader.assert_called_once_with(
            dotenv_path=(repo_root / ".env").resolve(),
            override=False,
        )

    def test_warns_if_dotenv_missing_and_no_key(self, monkeypatch, capsys):
        monkeypatch.setattr(review_paper, "load_dotenv", None)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        review_paper._load_environment()

        captured = capsys.readouterr()
        assert "python-dotenv is not installed" in captured.err


class TestBuildLlm:
    """Tests for _build_llm API-key handling."""

    def test_strips_whitespace_from_api_key(self, monkeypatch):
        """API keys with leading/trailing whitespace or newlines must be stripped
        before being passed to openai.OpenAI so that the HTTP Authorization
        header is never set to an illegal value.
        """
        captured_key: list[str] = []

        class FakeClient:
            def __init__(self, api_key: str):
                captured_key.append(api_key)

        monkeypatch.setenv("OPENAI_API_KEY", "  sk-test-key\n")

        mock_openai = MagicMock()
        mock_openai.OpenAI = FakeClient

        with patch.dict("sys.modules", {"openai": mock_openai}):
            _build_llm("gpt-4o")

        assert captured_key == ["sk-test-key"]

    def test_raises_when_api_key_blank_after_strip(self, monkeypatch):
        """A key that is only whitespace must trigger the 'not set' error."""
        monkeypatch.setenv("OPENAI_API_KEY", "   \n  ")

        mock_openai = MagicMock()
        with patch.dict("sys.modules", {"openai": mock_openai}):
            with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
                _build_llm("gpt-4o")


class TestMainLlmError:
    """Verify that main() handles LLM/API failures gracefully."""

    _SAMPLE_TEXT = (
        "Attention Is All You Need\n\n"
        "Abstract\nWe propose the Transformer.\n\n"
        "1. Introduction\nNeural networks are great.\n"
    )

    def test_llm_exception_returns_error_not_raises(self, tmp_path, capsys):
        """An exception from the LLM (e.g. connection error) must cause main()
        to return 1 with an error message rather than crashing with a traceback.
        This ensures the CI report file is never silently left empty.
        """
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")

        def failing_llm(_prompt: str) -> str:
            raise RuntimeError("Connection error")

        with patch("review_paper._build_llm", return_value=failing_llm):
            rc = main([str(paper), "--format", "text"])

        assert rc == 1
        captured = capsys.readouterr()
        assert "failed" in captured.err

    def test_llm_error_written_to_stdout_for_tee(self, tmp_path, capsys):
        """The error message must also appear on stdout so that the workflow's
        ``| tee report.md`` pipe captures it — preventing a silently empty report.
        """
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")

        def failing_llm(_prompt: str) -> str:
            raise RuntimeError("Connection error")

        with patch("review_paper._build_llm", return_value=failing_llm):
            rc = main([str(paper), "--format", "markdown"])

        assert rc == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out
        assert "failed" in captured.out

    def test_missing_api_key_written_to_stdout_for_tee(self, tmp_path, capsys):
        """A missing API key (SystemExit from _build_llm) must produce stdout
        output so the report file is not left empty.
        """
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")

        with patch(
            "review_paper._build_llm",
            side_effect=SystemExit("OPENAI_API_KEY environment variable is not set."),
        ):
            rc = main([str(paper), "--format", "markdown"])

        assert rc == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out



class TestMainOutputFlag:
    """Verify that main() writes to a file when --output is given."""

    _SAMPLE_TEXT = (
        "Attention Is All You Need\n\n"
        "Abstract\nWe propose the Transformer.\n\n"
        "1. Introduction\nNeural networks are great.\n"
    )

    def test_output_flag_writes_file(self, tmp_path):
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        out_file = tmp_path / "report.md"
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([str(paper), "--format", "markdown", "--output", str(out_file)])

        assert rc == 0
        assert out_file.exists()
        assert len(out_file.read_text(encoding="utf-8")) > 0

    def test_output_flag_not_stdout(self, tmp_path, capsys):
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        out_file = tmp_path / "report.md"
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            main([str(paper), "--format", "markdown", "--output", str(out_file)])

        captured = capsys.readouterr()
        # The report body should NOT appear on stdout when --output is used.
        assert "# Novelty Evaluation" not in captured.out

    def test_output_json_file(self, tmp_path):
        import json as _json
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        out_file = tmp_path / "report.json"
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([str(paper), "--format", "json", "--output", str(out_file)])

        assert rc == 0
        data = _json.loads(out_file.read_text(encoding="utf-8"))
        assert "paper_title" in data


class TestMainMetadata:
    """Verify that run metadata is attached to the generated report."""

    _SAMPLE_TEXT = (
        "Attention Is All You Need\n\n"
        "Abstract\nWe propose the Transformer.\n\n"
        "1. Introduction\nNeural networks are great.\n"
    )

    def test_metadata_present_in_markdown_output(self, tmp_path, capsys):
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([str(paper), "--format", "markdown", "--model", "gpt-4o-test",
                        "--reports-dir", str(tmp_path)])

        assert rc == 0
        captured = capsys.readouterr()
        assert "## Run Metadata" in captured.out
        assert "gpt-4o-test" in captured.out

    def test_metadata_present_in_json_output(self, tmp_path, capsys):
        import json as _json
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([str(paper), "--format", "json", "--reports-dir", str(tmp_path)])

        assert rc == 0
        captured = capsys.readouterr()
        data = _json.loads(captured.out)
        assert "metadata" in data
        assert data["metadata"]["model"] != ""
        assert data["metadata"]["input_source"] != ""
        assert data["metadata"]["timestamp"] != ""

    def test_metadata_contains_input_source(self, tmp_path, capsys):
        import json as _json
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            main([str(paper), "--format", "json", "--reports-dir", str(tmp_path)])

        captured = capsys.readouterr()
        data = _json.loads(captured.out)
        assert "paper.txt" in data["metadata"]["input_source"]

    def test_metadata_stage_runtimes_keys(self, tmp_path, capsys):
        import json as _json
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            main([str(paper), "--format", "json", "--reports-dir", str(tmp_path)])

        captured = capsys.readouterr()
        data = _json.loads(captured.out)
        stage_runtimes = data["metadata"]["stage_runtimes"]
        assert "parsing" in stage_runtimes
        assert "similarity" in stage_runtimes
        assert "evaluation" in stage_runtimes

    def test_metadata_code_version_set(self, tmp_path, capsys):
        import json as _json
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            main([str(paper), "--format", "json", "--reports-dir", str(tmp_path)])

        captured = capsys.readouterr()
        data = _json.loads(captured.out)
        assert data["metadata"]["code_version"] != ""


class TestMainReportsDir:
    """Verify the reports directory auto-save behaviour."""

    _SAMPLE_TEXT = (
        "Attention Is All You Need\n\n"
        "Abstract\nWe propose the Transformer.\n\n"
        "1. Introduction\nNeural networks are great.\n"
    )

    def test_auto_save_creates_file_in_reports_dir(self, tmp_path):
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        reports_dir = tmp_path / "my_reports"
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([str(paper), "--format", "markdown",
                        "--reports-dir", str(reports_dir)])

        assert rc == 0
        assert reports_dir.exists()
        files = list(reports_dir.glob("*.md"))
        assert len(files) == 1

    def test_reports_dir_created_if_missing(self, tmp_path):
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        reports_dir = tmp_path / "new_dir" / "nested"
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([str(paper), "--format", "text",
                        "--reports-dir", str(reports_dir)])

        assert rc == 0
        assert reports_dir.exists()

    def test_auto_save_filename_contains_paper_title(self, tmp_path):
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        reports_dir = tmp_path / "reports"
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            main([str(paper), "--format", "markdown",
                  "--reports-dir", str(reports_dir)])

        files = list(reports_dir.glob("*.md"))
        assert len(files) == 1
        # Filename should begin with the paper title, not a fixed prefix
        assert "Attention_Is_All_You_Need" in files[0].name
        assert not files[0].name.startswith("novelty_report")

    def test_explicit_output_does_not_use_reports_dir(self, tmp_path):
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        out_file = tmp_path / "explicit.md"
        reports_dir = tmp_path / "reports"
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([str(paper), "--format", "markdown",
                        "--output", str(out_file),
                        "--reports-dir", str(reports_dir)])

        assert rc == 0
        assert out_file.exists()
        # reports_dir should NOT have been populated
        assert not reports_dir.exists()

    def test_default_format_is_pdf(self):
        """Verify that the --format argument defaults to 'pdf'."""
        import review_paper as rp
        ns = rp._parse_args(["dummy_paper.pdf"])
        assert ns.format == "pdf"

    def test_default_reports_dir_is_reports(self):
        """Verify that --reports-dir defaults to 'reports'."""
        import review_paper as rp
        ns = rp._parse_args(["dummy_paper.pdf"])
        assert ns.reports_dir == "reports"


# ---------------------------------------------------------------------------
# _read_papers_file
# ---------------------------------------------------------------------------


class TestReadPapersFile:
    """Tests for the NDJSON batch-input reader."""

    def _write(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def test_reads_url_entries(self, tmp_path):
        from review_paper import _read_papers_file
        f = tmp_path / "p.ndjson"
        self._write(f, '{"url": "https://arxiv.org/abs/2006.06138"}\n{"url": "https://arxiv.org/pdf/2602.04770"}\n')
        result = _read_papers_file(f)
        assert result == [
            "https://arxiv.org/abs/2006.06138",
            "https://arxiv.org/pdf/2602.04770",
        ]

    def test_reads_path_entries(self, tmp_path):
        from review_paper import _read_papers_file
        f = tmp_path / "p.ndjson"
        self._write(f, '{"path": "/some/paper.pdf"}\n{"path": "/other/paper.txt"}\n')
        result = _read_papers_file(f)
        assert result == ["/some/paper.pdf", "/other/paper.txt"]

    def test_skips_blank_lines(self, tmp_path):
        from review_paper import _read_papers_file
        f = tmp_path / "p.ndjson"
        self._write(f, '\n{"url": "https://example.com/p.pdf"}\n\n')
        assert len(_read_papers_file(f)) == 1

    def test_skips_comment_lines(self, tmp_path):
        from review_paper import _read_papers_file
        f = tmp_path / "p.ndjson"
        self._write(f, '# a comment\n{"url": "https://example.com/p.pdf"}\n')
        assert len(_read_papers_file(f)) == 1

    def test_invalid_json_raises_exit(self, tmp_path):
        from review_paper import _read_papers_file
        f = tmp_path / "p.ndjson"
        self._write(f, "not valid json\n")
        with pytest.raises(SystemExit, match="invalid JSON"):
            _read_papers_file(f)

    def test_missing_url_or_path_key_raises_exit(self, tmp_path):
        from review_paper import _read_papers_file
        f = tmp_path / "p.ndjson"
        self._write(f, '{"title": "some paper"}\n')
        with pytest.raises(SystemExit, match="'url' or 'path'"):
            _read_papers_file(f)

    def test_empty_file_raises_exit(self, tmp_path):
        from review_paper import _read_papers_file
        f = tmp_path / "p.ndjson"
        self._write(f, "")
        with pytest.raises(SystemExit, match="no papers"):
            _read_papers_file(f)

    def test_missing_file_raises_exit(self, tmp_path):
        from review_paper import _read_papers_file
        with pytest.raises(SystemExit, match="could not read"):
            _read_papers_file(tmp_path / "nonexistent.ndjson")


# ---------------------------------------------------------------------------
# Argument parsing — batch mode
# ---------------------------------------------------------------------------


class TestPaperArgOptional:
    """Verify that the paper positional arg is optional when --papers-file is given."""

    def test_paper_defaults_to_none(self):
        import review_paper as rp
        ns = rp._parse_args(["--papers-file", "batch.ndjson"])
        assert ns.paper is None
        assert ns.papers_file == "batch.ndjson"

    def test_paper_still_works_positionally(self):
        import review_paper as rp
        ns = rp._parse_args(["my_paper.pdf"])
        assert ns.paper == "my_paper.pdf"
        assert ns.papers_file is None

    def test_papers_file_default_is_none(self):
        import review_paper as rp
        ns = rp._parse_args(["my_paper.pdf"])
        assert ns.papers_file is None


# ---------------------------------------------------------------------------
# main() — batch mode integration
# ---------------------------------------------------------------------------


class TestMainBatchMode:
    """Verify batch review behaviour via --papers-file."""

    _SAMPLE_TEXT = (
        "Attention Is All You Need\n\n"
        "Abstract\nWe propose the Transformer.\n\n"
        "1. Introduction\nNeural networks are great.\n"
    )

    def _write_ndjson(self, path: Path, entries: list) -> None:
        import json
        path.write_text(
            "\n".join(json.dumps(e) for e in entries), encoding="utf-8"
        )

    def test_batch_reviews_multiple_papers(self, tmp_path):
        paper1 = tmp_path / "paper1.txt"
        paper2 = tmp_path / "paper2.txt"
        paper1.write_text(
            "Attention Is All You Need\n\n"
            "Abstract\nWe propose the Transformer.\n\n"
            "1. Introduction\nNeural networks are great.\n",
            encoding="utf-8",
        )
        paper2.write_text(
            "BERT: Pre-training Deep Bidirectional Transformers\n\n"
            "Abstract\nWe introduce BERT for language representation.\n\n"
            "1. Introduction\nBidirectional training matters.\n",
            encoding="utf-8",
        )

        batch_file = tmp_path / "batch.ndjson"
        self._write_ndjson(batch_file, [
            {"path": str(paper1)},
            {"path": str(paper2)},
        ])

        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")
        reports_dir = tmp_path / "reports"

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([
                "--papers-file", str(batch_file),
                "--format", "text",
                "--reports-dir", str(reports_dir),
            ])

        assert rc == 0
        assert len(list(reports_dir.glob("*.txt"))) == 2

    def test_batch_partial_failure_returns_nonzero(self, tmp_path):
        paper_good = tmp_path / "paper1.txt"
        paper_good.write_text(self._SAMPLE_TEXT, encoding="utf-8")

        batch_file = tmp_path / "batch.ndjson"
        self._write_ndjson(batch_file, [
            {"path": str(paper_good)},
            {"path": str(tmp_path / "missing.txt")},  # does not exist
        ])

        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([
                "--papers-file", str(batch_file),
                "--format", "text",
                "--reports-dir", str(tmp_path / "reports"),
            ])

        assert rc == 1

    def test_no_paper_and_no_file_returns_error(self, capsys):
        rc = main([])
        assert rc == 1
        assert "papers-file" in capsys.readouterr().err

    def test_both_paper_and_file_returns_error(self, tmp_path, capsys):
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        batch_file = tmp_path / "batch.ndjson"
        batch_file.write_text('{"path": "x.txt"}', encoding="utf-8")

        rc = main([str(paper), "--papers-file", str(batch_file)])
        assert rc == 1
        assert "not both" in capsys.readouterr().err

    def test_output_with_batch_returns_error(self, tmp_path, capsys):
        batch_file = tmp_path / "batch.ndjson"
        batch_file.write_text('{"path": "x.txt"}', encoding="utf-8")

        rc = main([
            "--papers-file", str(batch_file),
            "--output", str(tmp_path / "out.txt"),
        ])
        assert rc == 1
        assert "--output" in capsys.readouterr().err

    def test_batch_file_not_found_returns_error(self, tmp_path, capsys):
        rc = main(["--papers-file", str(tmp_path / "nonexistent.ndjson")])
        assert rc == 1
        err = capsys.readouterr().err
        assert "could not read" in err.lower() or "nonexistent" in err


# ---------------------------------------------------------------------------
# Bundled default reference store
# ---------------------------------------------------------------------------

_BUNDLED_REFS_PATH = Path(__file__).resolve().parent.parent / "data" / "references.json"


class TestBundledReferences:
    """Verify the bundled data/references.json file and default-loading behaviour."""

    def test_bundled_references_file_exists(self):
        assert _BUNDLED_REFS_PATH.exists(), (
            "data/references.json must exist as the bundled reference store"
        )

    def test_bundled_references_is_valid_json_list(self):
        data = _json.loads(_BUNDLED_REFS_PATH.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_bundled_references_required_fields(self):
        data = _json.loads(_BUNDLED_REFS_PATH.read_text(encoding="utf-8"))
        for entry in data:
            assert "id" in entry, f"Entry missing 'id': {entry}"
            assert "title" in entry, f"Entry missing 'title': {entry}"
            assert "abstract" in entry, f"Entry missing 'abstract': {entry}"

    def test_bundled_references_arxiv_paper_present(self):
        """The paper from arXiv:1904.06019 must be in the bundled store."""
        store = ReferenceStore.from_file(_BUNDLED_REFS_PATH)
        ids = {p.id for p in store.all_papers()}
        assert any("1904.06019" in pid for pid in ids), (
            "arXiv paper 1904.06019 must be present in data/references.json"
        )

    def test_bundled_references_url_set(self):
        """Every bundled entry should have a non-empty URL."""
        data = _json.loads(_BUNDLED_REFS_PATH.read_text(encoding="utf-8"))
        for entry in data:
            assert entry.get("url"), f"Entry {entry.get('id')} is missing a URL"

    def test_bundled_references_loadable_by_reference_store(self):
        store = ReferenceStore.from_file(_BUNDLED_REFS_PATH)
        assert len(store) >= 1
        for p in store.all_papers():
            assert p.searchable_text  # title + abstract must be non-empty


_SAMPLE_TEXT = (
    "Attention Is All You Need\n\n"
    "Abstract\nWe propose the Transformer.\n\n"
    "1. Introduction\nNeural networks are great.\n"
)


class TestBundledReferencesLoadedByDefault:
    """Verify that _review_one() always loads bundled references."""

    def test_bundled_refs_loaded_even_without_references_flag(self, tmp_path, capsys):
        """Running without --references must still load the bundled store."""
        paper = tmp_path / "paper.txt"
        paper.write_text(_SAMPLE_TEXT, encoding="utf-8")
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: ok.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([str(paper), "--format", "text", "--reports-dir", str(tmp_path)])

        assert rc == 0
        err = capsys.readouterr().err
        assert "bundled reference" in err.lower()

    def test_user_references_merged_on_top_of_bundled(self, tmp_path, capsys):
        """When --references is given, user refs are added to the bundled set."""
        paper = tmp_path / "paper.txt"
        paper.write_text(_SAMPLE_TEXT, encoding="utf-8")

        # Create a small user reference store
        user_refs = [
            {
                "id": "user-paper-001",
                "title": "A custom reference paper",
                "abstract": "Custom abstract content.",
                "authors": ["Test Author"],
                "year": 2022,
                "venue": "NeurIPS",
                "url": "https://example.com/user-paper-001",
            }
        ]
        user_refs_path = tmp_path / "user_refs.json"
        user_refs_path.write_text(_json.dumps(user_refs), encoding="utf-8")

        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: ok.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([
                str(paper), "--format", "text",
                "--references", str(user_refs_path),
                "--reports-dir", str(tmp_path),
            ])

        assert rc == 0
        err = capsys.readouterr().err
        # Both the bundled load and user references load messages should appear
        assert "bundled reference" in err.lower()
        assert "user_refs.json" in err

    def test_bundled_refs_path_constant_is_set(self):
        """The _BUNDLED_REFERENCES constant must point to data/references.json."""
        from review_paper import _BUNDLED_REFERENCES
        assert _BUNDLED_REFERENCES.name == "references.json"
        assert _BUNDLED_REFERENCES.exists()

    def test_references_default_is_bundled_file(self):
        """--references defaults to the bundled baseline corpus path."""
        from review_paper import _parse_args, _BUNDLED_REFERENCES
        args = _parse_args(["paper.txt", "--format", "text"])
        assert args.references == str(_BUNDLED_REFERENCES)

    def test_references_can_be_overridden_on_cli(self, tmp_path):
        """Passing --references overrides the default bundled path."""
        from review_paper import _parse_args
        custom = str(tmp_path / "custom.json")
        args = _parse_args(["paper.txt", "--references", custom, "--format", "text"])
        assert args.references == custom


# ---------------------------------------------------------------------------
# Online reference search integration
# ---------------------------------------------------------------------------

_ONLINE_SEARCH_SAMPLE_TEXT = (
    "Attention Is All You Need\n\n"
    "Abstract\nWe propose the Transformer.\n\n"
    "1. Introduction\nNeural networks are great.\n"
)


class TestOnlineSearchIntegration:
    """Verify that online reference search is invoked by default and can be
    disabled via --no-online-search."""

    def test_online_search_called_by_default(self, tmp_path):
        """OnlineReferenceSearch.search must be called when the flag is absent."""
        paper = tmp_path / "paper.txt"
        paper.write_text(_ONLINE_SEARCH_SAMPLE_TEXT, encoding="utf-8")
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")
        call_count = {"n": 0}

        def tracking_search(self_obj, title, abstract="", arxiv_id="", queries=None):
            call_count["n"] += 1
            return []  # empty so the rest of the pipeline is unaffected

        with (
            patch("review_paper._build_llm", return_value=fake_llm),
            patch(
                "open_idea_sourcing.online_search.OnlineReferenceSearch.search",
                side_effect=tracking_search,
            ),
        ):
            rc = main([str(paper), "--format", "text", "--reports-dir", str(tmp_path)])

        assert rc == 0
        assert call_count["n"] >= 1

    def test_online_search_skipped_with_flag(self, tmp_path):
        """OnlineReferenceSearch.search must NOT be called with --no-online-search."""
        paper = tmp_path / "paper.txt"
        paper.write_text(_ONLINE_SEARCH_SAMPLE_TEXT, encoding="utf-8")
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")
        call_count = {"n": 0}

        def tracking_search(self_obj, title, abstract="", arxiv_id="", queries=None):
            call_count["n"] += 1
            return []

        with (
            patch("review_paper._build_llm", return_value=fake_llm),
            patch(
                "open_idea_sourcing.online_search.OnlineReferenceSearch.search",
                side_effect=tracking_search,
            ),
        ):
            rc = main([
                str(paper), "--format", "text",
                "--no-online-search",
                "--reports-dir", str(tmp_path),
            ])

        assert rc == 0
        assert call_count["n"] == 0

    def test_no_online_search_flag_default_is_false(self):
        """--no-online-search defaults to False (online search enabled)."""
        from review_paper import _parse_args
        args = _parse_args(["paper.txt", "--format", "text"])
        assert args.no_online_search is False

    def test_no_online_search_flag_can_be_set(self):
        """--no-online-search can be explicitly set."""
        from review_paper import _parse_args
        args = _parse_args(["paper.txt", "--format", "text", "--no-online-search"])
        assert args.no_online_search is True
