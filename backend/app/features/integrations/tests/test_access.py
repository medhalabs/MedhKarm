from mcp.types import Tool, ToolAnnotations

from app.features.integrations.access import exposed_name, permitted
from app.features.integrations.schemas import McpAccess


def tool(name: str, read_only: bool | None) -> Tool:
    hints = None if read_only is None else ToolAnnotations(readOnlyHint=read_only)
    return Tool(name=name, inputSchema={"type": "object"}, annotations=hints)


def test_only_listed_tools_and_patterns() -> None:
    access = McpAccess(server="github", tools=["get_*", "search_code"], read_only=False)

    assert permitted(tool("get_file_contents", False), access)
    assert permitted(tool("search_code", False), access)
    assert not permitted(tool("create_pull_request", False), access)


def test_read_only_access_needs_the_servers_read_only_hint() -> None:
    access = McpAccess(server="github")  # all tools, read-only (the defaults)

    assert permitted(tool("get_file_contents", True), access)
    assert not permitted(tool("delete_branch", False), access)
    assert not permitted(tool("mystery", None), access)  # no hint: assume it changes things


def test_names_are_prefixed_and_short_enough() -> None:
    assert exposed_name("python_docs", "lookup") == "python_docs__lookup"
    assert len(exposed_name("s" * 40, "t" * 40)) == 64
