"""Tools from an MCP server, for one agent, within its limits (a developer_engine ToolSource).

Per task: start or connect to the server, list its tools, show the agent only the ones its
role may use (`access.py`), and on every call check the name again and count it against
`max_calls`. Refusals and server errors come back as text for the model, never as exceptions.
"""

import os
import sys
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult, TextContent, Tool

from app.features.developer_engine.interfaces import ToolSession
from app.features.integrations.access import exposed_name, permitted
from app.features.integrations.schemas import McpAccess, McpServer
from app.features.models.schemas import ToolSpec

MAX_RESULT_CHARS = 4000
BACKEND_DIR = Path(__file__).resolve().parents[3]


class McpToolSource:
    def __init__(self, server: McpServer, access: McpAccess) -> None:
        self.name = server.id
        self._server = server
        self._access = access

    @asynccontextmanager
    async def session(self) -> AsyncIterator[ToolSession]:
        async with AsyncExitStack() as stack:
            client = await _connect(self._server, stack)
            await client.initialize()
            tools = [t for t in (await client.list_tools()).tools if permitted(t, self._access)]
            yield McpToolSession(client, self._server, self._access, tools)


class McpToolSession:
    def __init__(
        self, client: ClientSession, server: McpServer, access: McpAccess, tools: list[Tool]
    ) -> None:
        self._client = client
        self._server = server
        self._access = access
        self._tools = {exposed_name(server.id, t.name): t for t in tools}
        self.calls = 0

    async def list_tools(self) -> list[ToolSpec]:
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": f"[{self._server.title}] {tool.description or tool.name}",
                    "parameters": tool.inputSchema,
                },
            }
            for name, tool in self._tools.items()
        ]

    async def call(self, name: str, arguments: dict[str, Any]) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"Not allowed: {name} isn't one of your tools."
        if self.calls >= self._access.max_calls:
            return (
                f"Limit reached: you may use {self._server.title} tools at most "
                f"{self._access.max_calls} times per task. Carry on without them."
            )
        self.calls += 1
        try:
            result = await self._client.call_tool(
                tool.name,
                arguments,
                read_timeout_seconds=timedelta(seconds=self._server.timeout_seconds),
            )
        except Exception as exc:  # the server failed or timed out: tell the model, keep going
            return f"Error from {self._server.title}: {type(exc).__name__}: {exc}"[:500]
        return _as_text(result)


async def _connect(server: McpServer, stack: AsyncExitStack) -> ClientSession:
    env = {name: os.environ[name] for name in server.env if name in os.environ}
    if server.transport == "stdio":
        params = StdioServerParameters(
            command=sys.executable if server.command == "{python}" else server.command,
            args=server.args,
            env={**_base_env(), **env},
        )
        read, write = await stack.enter_async_context(stdio_client(params))
    else:
        token = next((v for k, v in env.items() if k.endswith("TOKEN")), None)
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        http = await stack.enter_async_context(httpx.AsyncClient(headers=headers))
        read, write, _ = await stack.enter_async_context(
            streamable_http_client(server.url, http_client=http)
        )
    return await stack.enter_async_context(
        ClientSession(read, write, read_timeout_seconds=timedelta(seconds=server.timeout_seconds))
    )


def _base_env() -> dict[str, str]:
    """What a stdio server inherits: enough to run, never our secrets (API keys stay here)."""
    keep = ("PATH", "HOME", "LANG", "PYTHONPATH", "VIRTUAL_ENV", "TMPDIR", "SYSTEMROOT")
    env = {k: os.environ[k] for k in keep if k in os.environ}
    # So in-repo servers (`-m app.features.integrations.servers...`) import from any directory.
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(BACKEND_DIR), env.get("PYTHONPATH")]))
    return env


def _as_text(result: CallToolResult) -> str:
    parts = [c.text for c in result.content if isinstance(c, TextContent)]
    text = "\n".join(parts) or "(no text in the result)"
    if result.isError:
        text = f"Error: {text}"
    if len(text) > MAX_RESULT_CHARS:
        text = text[:MAX_RESULT_CHARS] + f"\n... ({len(text) - MAX_RESULT_CHARS} more characters)"
    return text
