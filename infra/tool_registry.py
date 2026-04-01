"""
infra/tool_registry.py

ToolRegistry: records which tools were invoked in a run and provides a thin
call-and-log interface.

Usage:
    registry = ToolRegistry(context)
    result = registry.call("search_semantic_scholar", query="attention mechanism")
    # result is the return value of the registered callable
    # the call is automatically logged to context.tool_list and tool_call_log
"""

from __future__ import annotations

from typing import Any, Callable

from infra.run_context import RunContext


LOG_TRUNCATE_LENGTH = 200  # max chars to store per tool call argument/result


class ToolRegistry:
    """
    Thin registry that maps tool names to callables and records usage.

    Tracks may register any callable as a tool. When the tool is called via
    registry.call(), the invocation is recorded in the RunContext.tool_list and
    in an internal call log that can be retrieved for the report appendix.
    """

    def __init__(self, context: RunContext) -> None:
        self._context = context
        self._tools: dict[str, Callable[..., Any]] = {}
        self._call_log: list[dict[str, Any]] = []

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        """Register a callable under the given name."""
        self._tools[name] = fn

    def call(self, name: str, **kwargs: Any) -> Any:
        """
        Call a registered tool by name, log the invocation, and return its result.

        Raises KeyError if the tool is not registered.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered in ToolRegistry.")
        fn = self._tools[name]
        result = fn(**kwargs)
        self._context.record_tool(name)
        self._call_log.append(
            {
                "tool": name,
                "kwargs": {k: str(v)[:LOG_TRUNCATE_LENGTH] for k, v in kwargs.items()},
                "summary": str(result)[:LOG_TRUNCATE_LENGTH] if result is not None else "None",
            }
        )
        return result

    def tool_call_log(self) -> list[dict[str, Any]]:
        """Return the full call log for use in the report audit appendix."""
        return list(self._call_log)

    def registered_names(self) -> list[str]:
        """Return the list of registered tool names."""
        return list(self._tools.keys())
