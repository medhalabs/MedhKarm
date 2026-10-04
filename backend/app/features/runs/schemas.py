"""A run as the founder sees it: what was asked, where it stands, what it's waiting for."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.features.repos.schemas import NewRepo, RepoSource, check_repo_name
from app.features.starters.schemas import StackChoice


class RunStatus(StrEnum):
    QUEUED = "queued"  # waiting for a worker
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RELEASED = "released"
    REJECTED = "rejected"
    FAILED = "failed"  # the work didn't pass its checks
    ERROR = "error"  # something broke (model, sandbox, worker) and retries ran out
    CANCELLED = "cancelled"  # the founder stopped it


# A run in one of these is over: nothing more happens to it.
FINAL_STATUSES = frozenset(
    {
        RunStatus.RELEASED,
        RunStatus.REJECTED,
        RunStatus.FAILED,
        RunStatus.ERROR,
        RunStatus.CANCELLED,
    }
)


class StartRun(BaseModel):
    request: str = Field(min_length=3, max_length=5000)  # what the founder wants built
    # None: detected from the repository, or from the starter a new project begins with
    test_command: str | None = Field(default=None, min_length=1, max_length=500)
    repo: RepoSource | None = None  # an existing GitHub repository to change
    # Without `repo`: create a private repository with the released work (unless False)
    create_repo: bool = True
    new_repo_name: str | None = Field(default=None, max_length=100)  # None: from the request
    # Without `repo`: the stack and ready-made modules (empty choices: the team decides)
    stack: StackChoice = Field(default_factory=StackChoice)

    @field_validator("new_repo_name")
    @classmethod
    def _repo_name(cls, name: str | None) -> str | None:
        return check_repo_name(name)


class ApprovalDecision(BaseModel):
    approved: bool
    feedback: str = Field(default="", max_length=2000)


class Run(BaseModel):
    id: str
    company_id: str | None = None  # whose run it is (None: made before sign-in existed)
    request: str
    test_command: str  # empty: detected from the repository when the run starts
    repo: RepoSource | None = None
    new_repo: NewRepo | None = None  # a repository to create on release (new projects)
    stack: StackChoice | None = None  # the founder's stack choices (new projects)
    status: RunStatus
    gate: dict[str, Any] | None = None  # what the founder is asked to approve, while waiting
    error: str | None = None
    delivery: dict[str, Any] | None = None  # the pull request with the released work, if any
    deployment: dict[str, Any] | None = None  # where the released app is live, if deployed
    created_at: datetime
    updated_at: datetime
