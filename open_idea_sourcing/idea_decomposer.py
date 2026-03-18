"""Hierarchical idea decomposition with per-node online reference search.

This module orchestrates a **top-down** exploration of a research idea:

1. **Decomposition** — the LLM breaks the root idea into focused sub-topics.
2. **Online search** — each node is queried against Semantic Scholar to
   surface relevant references.
3. **Recursion** — steps 1–2 repeat for each child node down to *depth*
   levels.

The result is a tree of :class:`IdeaNode` objects that the report generator
can render as a hierarchy diagram with hyperlinks and backlinks.

Example usage::

    from open_idea_sourcing.idea_decomposer import IdeaDecomposer
    from open_idea_sourcing.online_search import OnlineReferenceSearch

    decomposer = IdeaDecomposer(llm=my_llm)
    tree = decomposer.decompose("Attention mechanisms in deep learning", depth=2)
    for node in tree.all_nodes():
        print(node.topic, [r.title for r in node.references])
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from .online_search import OnlineReferenceSearch
from .reference_store import ReferencePaper

# Type alias matching the rest of the package
LLMCallable = Callable[[str], str]

# Maximum number of sub-topics the LLM may return for a single node
_MAX_SUBTOPICS = 5


@dataclass
class IdeaNode:
    """A single node in the idea decomposition tree.

    Attributes
    ----------
    topic:
        Short name for this concept (e.g. ``"Attention Mechanisms"``).
    description:
        One-sentence description of the concept.
    children:
        Child nodes produced by one further level of decomposition.
    references:
        Academic papers found for this node via online search.
    """

    topic: str
    description: str = ""
    children: list["IdeaNode"] = field(default_factory=list)
    references: list[ReferencePaper] = field(default_factory=list)

    def all_nodes(self) -> list["IdeaNode"]:
        """Return this node and all descendants in pre-order (depth-first)."""
        result: list[IdeaNode] = [self]
        for child in self.children:
            result.extend(child.all_nodes())
        return result


class IdeaDecomposer:
    """Decompose a research idea into a hierarchy and search for references.

    Parameters
    ----------
    llm:
        Callable that receives a prompt string and returns the LLM response.
    online_search:
        Optional :class:`~open_idea_sourcing.online_search.OnlineReferenceSearch`
        instance.  When *None* a default instance is created automatically.
        Pass a pre-configured or stubbed instance to override behaviour
        (e.g. in tests or when online search is disabled).
    max_refs_per_node:
        Maximum number of online references to fetch for each node
        (default: 5).
    """

    def __init__(
        self,
        llm: LLMCallable,
        online_search: Optional[OnlineReferenceSearch] = None,
        max_refs_per_node: int = 5,
    ) -> None:
        self._llm = llm
        self._searcher = (
            online_search if online_search is not None else OnlineReferenceSearch()
        )
        self._max_refs = max_refs_per_node

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decompose(
        self,
        idea: str,
        depth: int = 2,
    ) -> IdeaNode:
        """Decompose *idea* into a hierarchy of sub-topics with references.

        Parameters
        ----------
        idea:
            The research idea, question, or topic to explore.
        depth:
            How many levels of decomposition to perform (default: 2).
            A depth of 1 produces the root node plus its immediate children;
            depth 2 adds a further level of grandchildren, and so on.

        Returns
        -------
        IdeaNode
            Root node of the decomposition tree.  Call
            :meth:`IdeaNode.all_nodes` to iterate over the whole tree.
        """
        depth = max(1, depth)
        root = IdeaNode(topic=idea, description="Root research idea")
        root.references = self._searcher.search(idea, max_results=self._max_refs)
        self._decompose_node(root, remaining_depth=depth)
        return root

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _decompose_node(self, node: IdeaNode, remaining_depth: int) -> None:
        """Recursively decompose *node* and populate its children."""
        if remaining_depth <= 0:
            return
        children = self._get_subtopics(node.topic, node.description)
        for child in children:
            child.references = self._searcher.search(
                child.topic, max_results=self._max_refs
            )
            self._decompose_node(child, remaining_depth - 1)
        node.children = children

    def _get_subtopics(self, topic: str, description: str) -> list[IdeaNode]:
        """Ask the LLM to break *topic* into focused sub-topics."""
        prompt = _DECOMPOSITION_PROMPT.format(
            topic=topic,
            description=description or topic,
            max_subtopics=_MAX_SUBTOPICS,
        )
        response = self._llm(prompt)
        return _parse_subtopics(response)


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_DECOMPOSITION_PROMPT = """\
You are a research expert helping to map out a research landscape.

TASK: Break the following research topic into {max_subtopics} or fewer distinct
sub-topics or component concepts that together cover the main aspects of the topic.
Each sub-topic should be focused, non-overlapping, and searchable in academic databases.

TOPIC: {topic}
CONTEXT: {description}

INSTRUCTIONS:
Respond ONLY with a numbered list using the exact format shown below.
Do not include any preamble, commentary, or trailing text.

1. TOPIC: <short topic name>
   DESCRIPTION: <one sentence describing this sub-topic>
2. TOPIC: <short topic name>
   DESCRIPTION: <one sentence describing this sub-topic>
"""

# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

_SUBTOPIC_RE = re.compile(
    r"\d+\.\s+TOPIC:\s*(.+?)\n\s*DESCRIPTION:\s*(.+?)(?=\n\d+\.|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def _parse_subtopics(text: str) -> list[IdeaNode]:
    """Parse the LLM-generated numbered sub-topic list into :class:`IdeaNode` objects."""
    nodes: list[IdeaNode] = []
    for m in _SUBTOPIC_RE.finditer(text):
        topic = m.group(1).strip()
        description = re.sub(r"\s+", " ", m.group(2)).strip()
        if topic:
            nodes.append(IdeaNode(topic=topic, description=description))
        if len(nodes) >= _MAX_SUBTOPICS:
            break
    return nodes
