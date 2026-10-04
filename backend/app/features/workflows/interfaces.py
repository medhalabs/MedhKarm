from typing import Protocol

from app.features.sandbox.interfaces import Sandbox
from app.features.workflows.schemas import CheckResult
from app.features.workflows.state import BuildState


class WorkChecker(Protocol):
    """Decides whether the team's work is good enough to put in front of the founder.

    One per kind of team: tests, build, type-check and lint for software (QualityChecker
    around TestCommandChecker); human review for
    content and approval rules for operations come later.
    """

    async def check(self, state: BuildState, sandbox: Sandbox) -> CheckResult: ...
