"""Extra tools (MCP) reach the model through tool sources, and only offered tools ever run."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.developer_engine.interfaces import ToolSession
from app.features.developer_engine.schemas import DevTask
from app.features.events.service import RunRecorder
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall, ToolSpec
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider


def call(tool: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{tool}", name=tool, arguments=arguments)])


class Docs:
    name = "docs"

    def __init__(self) -> None:
        self.opened = self.closed = 0

    @asynccontextmanager
    async def session(self) -> AsyncIterator[ToolSession]:
        self.opened += 1
        yield DocsSession()
        self.closed += 1


class DocsSession:
    async def list_tools(self) -> list[ToolSpec]:
        return [
            {
                "type": "function",
                "function": {"name": "docs__lookup", "description": "", "parameters": {}},
            }
        ]

    async def call(self, name: str, arguments: dict[str, Any]) -> str:
        return f"docs for {arguments['name']}"


class Spy(ScriptedLLMProvider):
    offered: list[str]

    async def complete(self, messages, tools=None):  # type: ignore[no-untyped-def]
        self.offered = [t["function"]["name"] for t in tools or []]
        return await super().complete(messages, tools)


async def test_extra_tools_are_offered_called_and_closed() -> None:
    llm = Spy(
        [
            call("docs__lookup", name="csv.writer"),
            call("write_file", path="secret.txt", content="x"),  # not this role's tool
            call("finish", summary="done"),
        ]
    )
    docs, events = Docs(), InMemoryEventStore()
    sandbox = await InMemorySandboxProvider().create()
    engine = ToolLoopEngine(llm, tools=["read_file", "run_command"], tool_sources=[docs])

    await engine.run_task(
        DevTask(description="t", test_command="true"), sandbox, RunRecorder(events, "r")
    )

    assert llm.offered == ["read_file", "run_command", "finish", "docs__lookup"]
    tool_results = [m["content"] for m in llm.calls[2] if m["role"] == "tool"]
    assert tool_results == [
        "docs for csv.writer",
        "Not allowed: write_file isn't one of your tools.",
    ]
    assert await sandbox.list_files() == []  # the refused write never happened
    assert (docs.opened, docs.closed) == (1, 1)
    used = [e.summary for e in events.events if e.type == "tool.used"]
    assert used == [
        "Used docs: lookup (csv.writer)",
        "Tried write_file, which isn't one of its tools",
    ]
