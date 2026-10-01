from typing import Any

from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    passed: bool
    output: str = ""


class StepUpdate(BaseModel):
    """One node finishing, as it happens. Later this feeds the event log and the office view."""

    node: str
    data: dict[str, Any]


class RunOutcome(BaseModel):
    run_id: str
    waiting_for_approval: bool
    gate: dict[str, Any] | None = None  # what the founder is asked, when waiting
    state: dict[str, Any] = Field(default_factory=dict)
