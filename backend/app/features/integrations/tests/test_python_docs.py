"""The python_docs MCP server, started for real over stdio, behind an agent's limits."""

from app.features.integrations.loader import load_servers
from app.features.integrations.mcp_source import McpToolSource
from app.features.integrations.schemas import McpAccess
from app.features.integrations.servers.python_docs import resolve


def source(**access: object) -> McpToolSource:
    return McpToolSource(load_servers()["python_docs"], McpAccess(server="python_docs", **access))


async def test_lists_only_granted_tools_and_answers() -> None:
    async with source(tools=["lookup"]).session() as session:
        names = [spec["function"]["name"] for spec in await session.list_tools()]
        answer = await session.call("python_docs__lookup", {"name": "csv.DictWriter"})
        refused = await session.call("python_docs__members", {"module": "csv"})

    assert names == ["python_docs__lookup"]
    assert "class DictWriter" in answer
    assert refused.startswith("Not allowed")


async def test_call_limit_per_task() -> None:
    async with source(max_calls=1).session() as session:
        first = await session.call("python_docs__members", {"module": "statistics"})
        second = await session.call("python_docs__members", {"module": "statistics"})

    assert "mean" in first
    assert second.startswith("Limit reached")


def test_only_standard_library_modules_are_opened() -> None:
    assert resolve("pathlib.Path.glob").__name__ == "glob"
    for name in ("requests", "antigravity", "", "os.nothing_here"):
        try:
            resolve(name)
        except (LookupError, AttributeError):
            continue
        raise AssertionError(f"{name!r} should not resolve")
