from typing import Any

from pydantic import BaseModel, Field


class QualityCheck(BaseModel):
    """One of QA's checks: a name the founder reads ("build", "lint") and its shell command."""

    name: str
    command: str


class CheckRun(BaseModel):
    """A check as it ran. Blocks the release when it failed, unless the tool isn't installed or
    it already failed before the team started."""

    name: str
    command: str
    passed: bool
    skipped: bool = False  # the tool isn't installed in this sandbox
    already_failing: bool = False  # failed on the project as the team found it
    output: str = ""

    @property
    def blocks(self) -> bool:
        return not self.passed and not self.skipped and not self.already_failing


class CheckResult(BaseModel):
    passed: bool
    output: str = ""
    checks: list[CheckRun] = Field(default_factory=list)  # each check, when there are several


class StepUpdate(BaseModel):
    """One node finishing, as it happens. Later this feeds the event log and the office view."""

    node: str
    data: dict[str, Any]


class RunOutcome(BaseModel):
    run_id: str
    waiting_for_approval: bool
    gate: dict[str, Any] | None = None  # what the founder is asked, when waiting
    next_nodes: list[str] = Field(default_factory=list)  # left to run (stopped mid-way if any)
    state: dict[str, Any] = Field(default_factory=dict)
