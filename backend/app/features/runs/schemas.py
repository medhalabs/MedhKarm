"""A run as the founder sees it: what was asked, where it stands, what it's waiting for."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.features.repos.schemas import NewRepo, RepoSource, check_repo_name


class RunStatus(StrEnum):
    QUEUED = "queued"  # waiting for a worker
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    RELEASED = "released"
    REJECTED = "rejected"
    FAILED = "failed"  # the work didn't pass its checks
    ERROR = "error"  # something broke (model, sandbox, worker) and retries ran out


DEFAULT_TEST_COMMAND = "pytest -q"


class StartRun(BaseModel):
    request: str = Field(min_length=3, max_length=5000)  # what the founder wants built
    # None: detected from the repository, or DEFAULT_TEST_COMMAND for a new project
    test_command: str | None = Field(default=None, min_length=1, max_length=500)
    repo: RepoSource | None = None  # an existing GitHub repository to change
    # Without `repo`: create a private repository with the released work (unless False)
    create_repo: bool = True
    new_repo_name: str | None = Field(default=None, max_length=100)  # None: from the request

    @field_validator("new_repo_name")
    @classmethod
    def _repo_name(cls, name: str | None) -> str | None:
        return check_repo_name(name)


class ApprovalDecision(BaseModel):
    approved: bool
    feedback: str = Field(default="", max_length=2000)


class Run(BaseModel):
    id: str
    request: str
    test_command: str  # empty: detected from the repository when the run starts
    repo: RepoSource | None = None
    new_repo: NewRepo | None = None  # a repository to create on release (new projects)
    status: RunStatus
    gate: dict[str, Any] | None = None  # what the founder is asked to approve, while waiting
    error: str | None = None
    delivery: dict[str, Any] | None = None  # the pull request with the released work, if any
    created_at: datetime
    updated_at: datetime
