"""Tests for open_idea_sourcing.idea_decomposer."""

from __future__ import annotations

import pytest

from open_idea_sourcing.idea_decomposer import (
    IdeaDecomposer,
    IdeaNode,
    _parse_subtopics,
)
from open_idea_sourcing.reference_store import ReferencePaper


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_reference(paper_id: str = "p1", title: str = "Test Paper") -> ReferencePaper:
    return ReferencePaper(
        id=paper_id,
        title=title,
        abstract="An academic paper about the topic.",
        year=2023,
        url=f"https://example.com/{paper_id}",
    )


class _NoopSearch:
    """Stub for OnlineReferenceSearch that always returns empty results."""

    def search(self, query: str, max_results: int = 5) -> list[ReferencePaper]:
        return []


class _FixedSearch:
    """Stub that returns a fixed set of references for any query."""

    def __init__(self, papers: list[ReferencePaper]) -> None:
        self._papers = papers

    def search(self, query: str, max_results: int = 5) -> list[ReferencePaper]:
        return self._papers[:max_results]


_DECOMP_RESPONSE = """\
1. TOPIC: Self-Attention
   DESCRIPTION: The mechanism where each token attends to every other token.
2. TOPIC: Positional Encoding
   DESCRIPTION: Techniques for injecting position information into embeddings.
3. TOPIC: Multi-Head Attention
   DESCRIPTION: Running multiple attention operations in parallel.
"""


def _make_decomp_llm(response: str = _DECOMP_RESPONSE):
    """LLM stub that always returns the given decomposition response."""
    def llm(prompt: str) -> str:
        return response
    return llm


# ---------------------------------------------------------------------------
# _parse_subtopics
# ---------------------------------------------------------------------------

class TestParseSubtopics:
    def test_parses_three_subtopics(self):
        nodes = _parse_subtopics(_DECOMP_RESPONSE)
        assert len(nodes) == 3

    def test_topic_names_extracted(self):
        nodes = _parse_subtopics(_DECOMP_RESPONSE)
        topics = [n.topic for n in nodes]
        assert "Self-Attention" in topics
        assert "Positional Encoding" in topics
        assert "Multi-Head Attention" in topics

    def test_descriptions_extracted(self):
        nodes = _parse_subtopics(_DECOMP_RESPONSE)
        node_map = {n.topic: n for n in nodes}
        assert "attends to every other token" in node_map["Self-Attention"].description

    def test_empty_response_returns_empty_list(self):
        assert _parse_subtopics("") == []

    def test_malformed_response_returns_empty_list(self):
        assert _parse_subtopics("No numbered list here.") == []

    def test_caps_at_max_five_subtopics(self):
        many = "\n".join(
            f"{i}. TOPIC: Topic {i}\n   DESCRIPTION: Description {i}."
            for i in range(1, 10)
        )
        nodes = _parse_subtopics(many)
        assert len(nodes) <= 5

    def test_nodes_have_empty_children_and_references_by_default(self):
        nodes = _parse_subtopics(_DECOMP_RESPONSE)
        for node in nodes:
            assert node.children == []
            assert node.references == []

    def test_whitespace_normalised_in_description(self):
        text = "1. TOPIC: Topic A\n   DESCRIPTION:   Lots   of   spaces.  "
        nodes = _parse_subtopics(text)
        assert nodes[0].description == "Lots of spaces."


# ---------------------------------------------------------------------------
# IdeaNode
# ---------------------------------------------------------------------------

class TestIdeaNode:
    def test_all_nodes_single_node(self):
        node = IdeaNode(topic="Root")
        assert node.all_nodes() == [node]

    def test_all_nodes_with_children(self):
        child1 = IdeaNode(topic="Child 1")
        child2 = IdeaNode(topic="Child 2")
        root = IdeaNode(topic="Root", children=[child1, child2])
        all_nodes = root.all_nodes()
        assert len(all_nodes) == 3
        assert all_nodes[0] is root
        assert child1 in all_nodes
        assert child2 in all_nodes

    def test_all_nodes_nested(self):
        grandchild = IdeaNode(topic="Grandchild")
        child = IdeaNode(topic="Child", children=[grandchild])
        root = IdeaNode(topic="Root", children=[child])
        all_nodes = root.all_nodes()
        assert len(all_nodes) == 3

    def test_all_nodes_pre_order(self):
        grandchild = IdeaNode(topic="Grandchild")
        child = IdeaNode(topic="Child", children=[grandchild])
        root = IdeaNode(topic="Root", children=[child])
        all_nodes = root.all_nodes()
        # Pre-order: root, child, grandchild
        assert all_nodes[0].topic == "Root"
        assert all_nodes[1].topic == "Child"
        assert all_nodes[2].topic == "Grandchild"


# ---------------------------------------------------------------------------
# IdeaDecomposer
# ---------------------------------------------------------------------------

class TestIdeaDecomposer:
    def test_decompose_returns_idea_node(self):
        decomposer = IdeaDecomposer(
            llm=_make_decomp_llm(), online_search=_NoopSearch()
        )
        root = decomposer.decompose("Attention mechanisms", depth=1)
        assert isinstance(root, IdeaNode)

    def test_root_topic_matches_input(self):
        decomposer = IdeaDecomposer(
            llm=_make_decomp_llm(), online_search=_NoopSearch()
        )
        root = decomposer.decompose("Transformers in NLP", depth=1)
        assert root.topic == "Transformers in NLP"

    def test_depth_1_produces_children(self):
        decomposer = IdeaDecomposer(
            llm=_make_decomp_llm(), online_search=_NoopSearch()
        )
        root = decomposer.decompose("Attention mechanisms", depth=1)
        assert len(root.children) > 0

    def test_depth_1_no_grandchildren(self):
        decomposer = IdeaDecomposer(
            llm=_make_decomp_llm(), online_search=_NoopSearch()
        )
        root = decomposer.decompose("Attention mechanisms", depth=1)
        for child in root.children:
            assert child.children == []

    def test_depth_2_produces_grandchildren(self):
        decomposer = IdeaDecomposer(
            llm=_make_decomp_llm(), online_search=_NoopSearch()
        )
        root = decomposer.decompose("Attention mechanisms", depth=2)
        # At depth 2, children should themselves have children
        all_nodes = root.all_nodes()
        assert len(all_nodes) > len(root.children) + 1

    def test_references_attached_to_nodes(self):
        ref = _make_reference()
        decomposer = IdeaDecomposer(
            llm=_make_decomp_llm(),
            online_search=_FixedSearch([ref]),
        )
        root = decomposer.decompose("Attention mechanisms", depth=1)
        assert len(root.references) > 0
        assert root.references[0].id == "p1"

    def test_child_nodes_get_references(self):
        ref = _make_reference()
        decomposer = IdeaDecomposer(
            llm=_make_decomp_llm(),
            online_search=_FixedSearch([ref]),
        )
        root = decomposer.decompose("Attention mechanisms", depth=1)
        for child in root.children:
            assert len(child.references) > 0

    def test_noop_search_gives_empty_references(self):
        decomposer = IdeaDecomposer(
            llm=_make_decomp_llm(), online_search=_NoopSearch()
        )
        root = decomposer.decompose("Attention mechanisms", depth=1)
        assert root.references == []
        for child in root.children:
            assert child.references == []

    def test_depth_clamped_to_minimum_one(self):
        decomposer = IdeaDecomposer(
            llm=_make_decomp_llm(), online_search=_NoopSearch()
        )
        root = decomposer.decompose("Test idea", depth=0)
        # Even depth=0 should produce children (clamped to 1)
        assert len(root.children) > 0

    def test_llm_not_called_for_empty_response(self):
        calls = []

        def counting_llm(prompt: str) -> str:
            calls.append(prompt)
            return ""  # empty — no subtopics parsed

        decomposer = IdeaDecomposer(
            llm=counting_llm, online_search=_NoopSearch()
        )
        root = decomposer.decompose("Test", depth=2)
        # LLM is called for root decomposition only (no children to recurse into)
        assert len(calls) == 1
        assert root.children == []

    def test_default_online_search_created_when_none(self):
        """IdeaDecomposer should create an OnlineReferenceSearch when none is supplied."""
        from open_idea_sourcing.online_search import OnlineReferenceSearch

        decomposer = IdeaDecomposer(llm=_make_decomp_llm())
        assert isinstance(decomposer._searcher, OnlineReferenceSearch)
