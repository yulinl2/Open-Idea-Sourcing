"""Tests for open_idea_sourcing.paper_parser."""

import pytest

from open_idea_sourcing.paper_parser import PaperParser, ParsedPaper, PaperSection


SAMPLE_TEXT = """Attention Is All You Need

Abstract
We present a novel sequence-to-sequence architecture, the Transformer,
that relies entirely on attention mechanisms. Experiments on machine
translation show state-of-the-art results.

1. Introduction
Neural sequence transduction models generally rely on recurrent neural
networks. In this paper we propose a different approach.

2. Model Architecture
The Transformer follows an encoder-decoder structure using stacked
self-attention and point-wise, fully connected layers.

References
[1] Bahdanau et al., 2014. Neural machine translation by jointly
learning to align and translate.
"""


class TestPaperParser:
    def setup_method(self):
        self.parser = PaperParser()

    def test_parse_text_returns_parsed_paper(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        assert isinstance(result, ParsedPaper)

    def test_extracts_title(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        assert result.title == "Attention Is All You Need"

    def test_extracts_abstract(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        assert "Transformer" in result.abstract
        assert "attention" in result.abstract.lower()

    def test_full_text_preserved(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        assert "encoder-decoder" in result.full_text

    def test_extracts_sections(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        titles = [s.title for s in result.sections]
        # At least one section should be found
        assert len(result.sections) >= 1

    def test_sections_have_content(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        for section in result.sections:
            assert isinstance(section, PaperSection)
            assert len(section.content) > 0

    def test_empty_text_returns_empty_paper(self):
        result = self.parser.parse_text("")
        assert result.title == ""
        assert result.abstract == ""
        assert result.full_text == ""
        assert result.sections == []

    def test_normalise_removes_excess_whitespace(self):
        messy = "Title\n\n\n\n\nAbstract\n  line one  \n  line two"
        result = self.parser.parse_text(messy)
        # Two or fewer consecutive newlines after normalisation
        assert "\n\n\n" not in result.full_text

    def test_key_content_includes_title_and_abstract(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        kc = result.key_content()
        assert result.title in kc
        assert result.abstract[:30] in kc

    def test_key_content_respects_max_chars(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        kc = result.key_content(max_chars=100)
        assert len(kc) <= 100

    def test_key_content_accurate_budget(self):
        """Budget calculation should use the full max_chars allowance accurately."""
        from open_idea_sourcing.paper_parser import ParsedPaper

        title = "T" * 10
        abstract = "A" * 20
        body = "B" * 10000
        paper = ParsedPaper(title=title, abstract=abstract, full_text=body)
        max_chars = 200
        kc = paper.key_content(max_chars=max_chars)
        assert len(kc) == max_chars, (
            f"key_content should fill exactly max_chars={max_chars} "
            f"but got {len(kc)}"
        )

    def test_parse_file_txt(self, tmp_path):
        f = tmp_path / "paper.txt"
        f.write_text(SAMPLE_TEXT, encoding="utf-8")
        result = self.parser.parse_file(str(f))
        assert result.title == "Attention Is All You Need"

    def test_parse_file_unknown_extension_treated_as_text(self, tmp_path):
        f = tmp_path / "paper.md"
        f.write_text(SAMPLE_TEXT, encoding="utf-8")
        result = self.parser.parse_file(str(f))
        assert "Transformer" in result.full_text

    def test_parse_pdf_raises_without_pdfplumber(self, monkeypatch, tmp_path):
        """If pdfplumber is not importable, a clear error is raised."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pdfplumber":
                raise ImportError("pdfplumber not installed")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        dummy_pdf = tmp_path / "test.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4 fake")
        with pytest.raises(ImportError, match="pdfplumber"):
            self.parser.parse_pdf(str(dummy_pdf))
