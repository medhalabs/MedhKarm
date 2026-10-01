from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol

from app.features.developer_engine.schemas import DevResult, DevTask
from app.features.events.service import RunRecorder
from app.features.models.schemas import ToolSpec
from app.features.sandbox.interfaces import Sandbox


class DeveloperEngine(Protocol):
    """The Developer contract: task + workspace in, changed files + test results out.

    Implementations: ToolLoopEngine (built in) now; OpenHands and the Claude Agent SDK later.
    """

    async def run_task(
        self, task: DevTask, sandbox: Sandbox, recorder: RunRecorder | None = None
    ) -> DevResult:
        """`recorder`, when given, receives each tool use and model call (with tokens)."""
        ...


class ToolSession(Protocol):
    """Extra tools for one task, from outside the sandbox (e.g. an MCP server). The source
    decides which tools the agent sees and enforces its limits on every call."""

    async def list_tools(self) -> list[ToolSpec]: ...

    async def call(self, name: str, arguments: dict[str, Any]) -> str:
        """The text the model sees. Refusals and errors are returned, not raised."""
        ...


class ToolSource(Protocol):
    """Opens a `ToolSession` for one task and closes it afterwards."""

    name: str  # e.g. "python_docs"

    def session(self) -> AbstractAsyncContextManager[ToolSession]: ...
