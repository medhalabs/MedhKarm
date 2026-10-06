from typing import Protocol

from app.features.sandbox.interfaces import Sandbox
from app.features.workflows.schemas import CheckResult, PlanDocs, RunAutonomy
from app.features.workflows.state import BuildState


class WorkChecker(Protocol):
    """Decides whether the team's work is good enough to put in front of the founder.

    One per kind of team: tests, build, type-check and lint for software (QualityChecker
    around TestCommandChecker); human review for
    content and approval rules for operations come later.
    """

    async def check(self, state: BuildState, sandbox: Sandbox) -> CheckResult: ...


class FounderNotes(Protocol):
    """The founder's messages to the team about a run, oldest first (messages feature). The
    CTO's plan and every developer brief include them."""

    async def for_run(self, run_id: str) -> list[str]: ...


class ApprovedPlans(Protocol):
    """The plan a run builds from, when the founder approved a blueprint first (the blueprints
    feature, through a small adapter in app/workers). None: the run didn't start from one."""

    async def for_run(self, run_id: str) -> "PlanDocs | None": ...


class SavedFile(Protocol):
    @property
    def id(self) -> int: ...


class ArtifactSink(Protocol):
    """Where a run keeps the files it produces for the founder (the artifacts feature): QA's
    demo video of the browser test."""

    async def save(
        self, run_id: str, kind: str, name: str, content_type: str, data: bytes
    ) -> SavedFile: ...


class RunAutonomies(Protocol):
    """The founder's autonomy settings for a run's release (the autonomy feature, through an
    adapter in app/workers). None: they set nothing, so the team template's rules apply."""

    async def for_run(self, run_id: str) -> RunAutonomy | None: ...
