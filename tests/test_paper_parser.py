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

# Simulate a PDF-extracted paper with a multi-line title and author header
MULTILINE_TITLE_TEXT = """Conformal Inference
of Counterfactuals and Individual Treatment Effects
Lihua Lei
DepartmentofStatistics,StanfordUniversity
E-mail: lihualei@stanford.edu
Emmanuel J. Candes
DepartmentofStatisticsandDepartmentofMathematics,StanfordUniversity

Abstract
We propose a framework for constructing reliable prediction intervals
for counterfactuals and individual treatment effects, combining conformal
inference with the potential outcomes framework.

1. Introduction
Estimating individual treatment effects is central to precision medicine.
"""
# Note: the "Department..." lines intentionally omit spaces — this mirrors
# the output of PDF text extraction tools (e.g. pdfplumber) that sometimes
# merge words without inter-word spaces in the affiliation header.


class TestPaperParser:
    def setup_method(self):
        self.parser = PaperParser()

    def test_parse_text_returns_parsed_paper(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        assert isinstance(result, ParsedPaper)

    def test_extracts_title(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        assert result.title == "Attention Is All You Need"

    def test_extracts_multiline_title(self):
        """Multi-line PDF titles should be joined into a single string."""
        result = self.parser.parse_text(MULTILINE_TITLE_TEXT)
        assert result.title == (
            "Conformal Inference of Counterfactuals and Individual Treatment Effects"
        )

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
        assert result.authors == []

    def test_authors_field_defaults_empty(self):
        result = self.parser.parse_text(SAMPLE_TEXT)
        assert isinstance(result.authors, list)

    def test_extracts_authors_from_multiline_header(self):
        """Author names appearing after the title should be extracted."""
        result = self.parser.parse_text(MULTILINE_TITLE_TEXT)
        # Both authors should be detected
        assert "Lihua Lei" in result.authors
        assert "Emmanuel J. Candes" in result.authors

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


# ---------------------------------------------------------------------------
# LLMPaperParser
# ---------------------------------------------------------------------------

from open_idea_sourcing.paper_parser import LLMPaperParser


_MOCK_LLM_PARSE_RESPONSE = (
    "TITLE: Attention Is All You Need\n"
    "AUTHORS: Vaswani, Shazeer, Parmar\n"
    "ABSTRACT: We propose a new simple network architecture.\n"
    "SECTIONS:\n"
    "1. Introduction\n"
    "2. Background\n"
    "3. Model Architecture\n"
    "4. Experiments\n"
    "5. Conclusion\n"
)


class TestLLMPaperParser:
    def _mock_llm(self, prompt: str) -> str:
        return _MOCK_LLM_PARSE_RESPONSE

    def test_extracts_title(self):
        parser = LLMPaperParser(self._mock_llm)
        paper = parser.parse_text("Some raw PDF text.")
        assert paper.title == "Attention Is All You Need"

    def test_extracts_abstract(self):
        parser = LLMPaperParser(self._mock_llm)
        paper = parser.parse_text("Some raw PDF text.")
        assert "simple network architecture" in paper.abstract

    def test_extracts_authors(self):
        parser = LLMPaperParser(self._mock_llm)
        paper = parser.parse_text("Some raw PDF text.")
        assert "Vaswani" in paper.authors

    def test_extracts_sections(self):
        parser = LLMPaperParser(self._mock_llm)
        paper = parser.parse_text("Some raw PDF text.")
        section_titles = [s.title for s in paper.sections]
        assert "Introduction" in section_titles
        assert "Model Architecture" in section_titles

    def test_full_text_preserved(self):
        parser = LLMPaperParser(self._mock_llm)
        raw = "Some raw PDF text with body content."
        paper = parser.parse_text(raw)
        assert "body content" in paper.full_text

    def test_falls_back_on_llm_failure(self):
        """A failing LLM raises RuntimeError after 3 retries."""
        import pytest
        call_count = 0
        def failing_llm(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("LLM unavailable")

        parser = LLMPaperParser(failing_llm)
        with pytest.raises(RuntimeError, match="failed to extract"):
            parser.parse_text("Some Title\nAbstract: A short abstract.\nBody text.")
        assert call_count == 3

    def test_falls_back_on_empty_llm_output(self):
        """When LLM returns no title+abstract, fall back to regex parser."""
        parser = LLMPaperParser(lambda p: "TITLE: \nABSTRACT: ")
        paper = parser.parse_text("Some Title\nAbstract: A short abstract.\n")
        assert isinstance(paper, ParsedPaper)

    def test_returns_parsed_paper_type(self):
        parser = LLMPaperParser(self._mock_llm)
        paper = parser.parse_text("Any text.")
        assert isinstance(paper, ParsedPaper)

    def test_llm_parser_flag_parsed(self):
        from review_paper import _parse_args
        args = _parse_args(["paper.txt", "--format", "text", "--llm-parser"])
        assert args.llm_parser is True

    def test_llm_parser_default_is_false(self):
        from review_paper import _parse_args
        args = _parse_args(["paper.txt", "--format", "text"])
        assert args.llm_parser is False
