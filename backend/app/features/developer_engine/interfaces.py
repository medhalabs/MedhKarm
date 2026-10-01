from typing import Protocol

from app.features.developer_engine.schemas import DevResult, DevTask
from app.features.events.service import RunRecorder
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
