"""Tests for review_paper URL helpers and main() URL branch."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import review_paper

# Import the helpers we want to test
from review_paper import _normalise_arxiv_url, _download_paper, _build_llm, main

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
        assert "novelty evaluation failed" in captured.err

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
        assert "novelty evaluation failed" in captured.out

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
        assert files[0].name.startswith("novelty_")

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
