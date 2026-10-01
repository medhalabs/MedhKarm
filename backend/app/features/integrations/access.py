"""Per-agent limits on MCP tools. Pure functions: which tools an agent sees, under what name."""

from fnmatch import fnmatch

from mcp.types import Tool

from app.features.integrations.schemas import McpAccess

SEPARATOR = "__"
MAX_NAME = 64  # model APIs reject longer tool names


def exposed_name(server: str, tool: str) -> str:
    """The name the model sees: "<server>__<tool>", so tools from different servers never clash."""
    return f"{server}{SEPARATOR}{tool}"[:MAX_NAME]


def permitted(tool: Tool, access: McpAccess) -> bool:
    """Named by the access list, and read-only when the access requires it. A tool is read-only
    only if its server says so (`readOnlyHint`); no hint counts as "may change things"."""
    if not any(fnmatch(tool.name, pattern) for pattern in access.tools):
        return False
    if access.read_only:
        hints = tool.annotations
        return bool(hints and hints.readOnlyHint)
    return True
