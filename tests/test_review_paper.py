"""Tests for review_paper URL helpers and main() URL branch."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import review_paper

# Import the helpers we want to test
from review_paper import _normalise_arxiv_url, _download_paper, main

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


class TestDownloadPaper:
    def test_downloads_pdf_to_dest_dir(self, tmp_path):
        fake_pdf_bytes = b"%PDF-1.4 fake content"
        mock_response = MagicMock()
        mock_response.getheader.return_value = None
        mock_response.read.return_value = fake_pdf_bytes
        mock_response.getheader.return_value = None
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = _download_paper("https://arxiv.org/pdf/2006.06138", str(tmp_path))

        assert result.exists()
        assert result.read_bytes() == fake_pdf_bytes

    def test_abs_url_normalised_before_download(self, tmp_path):
        """Abstract URL should be rewritten to PDF URL before the request."""
        fake_pdf_bytes = b"%PDF-1.4"
        mock_response = MagicMock()
        mock_response.getheader.return_value = None
        mock_response.read.return_value = fake_pdf_bytes
        mock_response.getheader.return_value = None
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        captured = {}

        def fake_urlopen(req, timeout=None):  # timeout matches urlopen signature
            captured["url"] = req.full_url
            return mock_response

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
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
        mock_response.read.return_value = fake_pdf_bytes
        mock_response.getheader.return_value = None
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
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
            rc = main(["https://arxiv.org/abs/2006.06138", "--format", "text"])

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
            main(["https://arxiv.org/abs/2006.06138", "--format", "text"])

        for d in created_dirs:
            assert not Path(d).exists(), f"Temp dir {d} was not cleaned up"

    def test_file_path_still_works(self, tmp_path):
        """Passing a local file path must continue to work as before."""
        paper = tmp_path / "paper.txt"
        paper.write_text(self._SAMPLE_TEXT, encoding="utf-8")
        fake_llm = MagicMock(return_value="VERDICT: NOVEL\nEXPLANATION: original.")

        with patch("review_paper._build_llm", return_value=fake_llm):
            rc = main([str(paper), "--format", "text"])

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
