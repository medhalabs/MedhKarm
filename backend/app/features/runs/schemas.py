"""A run as the founder sees it: what was asked, where it stands, what it's waiting for."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    QUEUED = "queued"  # waiting for a worker
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RELEASED = "released"
    REJECTED = "rejected"
    FAILED = "failed"  # the work didn't pass its checks
    ERROR = "error"  # something broke (model, sandbox, worker) and retries ran out


class StartRun(BaseModel):
    request: str = Field(min_length=3, max_length=5000)  # what the founder wants built
    test_command: str = Field(default="pytest -q", min_length=1, max_length=500)


class ApprovalDecision(BaseModel):
    approved: bool
    feedback: str = Field(default="", max_length=2000)


class Run(BaseModel):
    id: str
    request: str
    test_command: str
    status: RunStatus
    gate: dict[str, Any] | None = None  # what the founder is asked to approve, while waiting
    error: str | None = None
    created_at: datetime
    updated_at: datetime
