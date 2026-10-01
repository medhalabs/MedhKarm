"""Checks software work by running the run's test command in its sandbox. Fails at once if the
workspace contains a file that replaces the test tool (QA never trusts a pass it can't see)."""

from app.features.sandbox.interfaces import Sandbox
from app.features.workflows.guards import shadow_feedback, shadowed_test_tools
from app.features.workflows.schemas import CheckResult
from app.features.workflows.state import BuildState


class TestCommandChecker:
    __test__ = False  # not a pytest test class, despite the name

    async def check(self, state: BuildState, sandbox: Sandbox) -> CheckResult:
        shadows = shadowed_test_tools(await sandbox.list_files())
        if shadows:
            return CheckResult(passed=False, output=shadow_feedback(shadows))
        result = await sandbox.run(state["test_command"])
        return CheckResult(passed=result.ok, output=result.output[-4000:])
