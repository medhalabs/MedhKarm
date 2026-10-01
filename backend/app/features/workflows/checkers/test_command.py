"""Checks software work by running the run's test command in its sandbox."""

from app.features.sandbox.interfaces import Sandbox
from app.features.workflows.schemas import CheckResult
from app.features.workflows.state import BuildState


class TestCommandChecker:
    __test__ = False  # not a pytest test class, despite the name

    async def check(self, state: BuildState, sandbox: Sandbox) -> CheckResult:
        result = await sandbox.run(state["test_command"])
        return CheckResult(passed=result.ok, output=result.output[-4000:])
