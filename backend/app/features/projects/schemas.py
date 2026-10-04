"""A founder's project and its backlog: the goal, the PM's plan, and where each item stands."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.features.repos.schemas import RepoSource
from app.features.starters.schemas import StackChoice


class ProjectStatus(StrEnum):
    PLANNING = "planning"  # the PM is writing the backlog
    PLAN_READY = "plan_ready"  # a proposed backlog waits for the founder's approval
    ACTIVE = "active"  # the team works through the backlog
    PAUSED = "paused"  # stopped by the founder, or by something that needs them (see `error`)
    DONE = "done"  # every item done or skipped


class ItemStatus(StrEnum):
    PROPOSED = "proposed"  # in the PM's plan, not yet approved
    TODO = "todo"
    IN_PROGRESS = "in_progress"  # its run is working, or waiting at the release gate
    WAITING_FOR_MERGE = "waiting_for_merge"  # released as a pull request on the founder's repo
    DONE = "done"
    BLOCKED = "blocked"  # rejected or failed: the founder retries or skips it (see `note`)
    SKIPPED = "skipped"


OPEN_ITEMS = (ItemStatus.PROPOSED, ItemStatus.TODO)
BUSY_ITEMS = (ItemStatus.IN_PROGRESS, ItemStatus.WAITING_FOR_MERGE, ItemStatus.BLOCKED)


class Size(StrEnum):
    S = "S"  # an hour of a developer's work
    M = "M"  # half a day
    L = "L"  # a day or more: worth splitting


class ItemFields(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=3000)  # what and why, for the team
    acceptance: list[str] = Field(default_factory=list, max_length=10)  # "done when" checks
    size: Size = Size.M


class BacklogItem(ItemFields):
    id: str
    project_id: str
    position: int  # order in the backlog, from 1
    status: ItemStatus
    run_id: str | None = None  # the run working on it (the latest one, after a retry)
    attempts: int = 0
    note: str = ""  # why it's blocked or waiting, for the founder
    pull_request_url: str = ""
    started_at: datetime | None = None
    done_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=3000)
    acceptance: list[str] | None = Field(default=None, max_length=10)
    size: Size | None = None
    position: int | None = Field(default=None, ge=1)  # move it to this place


class NewProject(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    goal: str = Field(min_length=10, max_length=5000)  # what the founder wants, in their words
    repo: RepoSource | None = None  # an existing repository; None = a new project
    test_command: str | None = Field(default=None, min_length=1, max_length=500)
    # A new project's stack and ready-made modules (empty choices: the team decides)
    stack: StackChoice = Field(default_factory=StackChoice)
    autopilot: bool = False  # work through the backlog on its own, day after day
    daily_limit: int = Field(default=2, ge=1, le=10)  # items started per day on autopilot


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    goal: str | None = Field(default=None, min_length=10, max_length=5000)
    test_command: str | None = Field(default=None, max_length=500)
    autopilot: bool | None = None
    daily_limit: int | None = Field(default=None, ge=1, le=10)


class Project(BaseModel):
    id: str
    name: str
    goal: str
    repo: RepoSource | None = None
    repo_owned: bool = False  # MedhKarm created the repository (its PRs merge on approval)
    test_command: str = ""
    stack: StackChoice | None = None  # the founder's stack choices (new projects)
    status: ProjectStatus
    autopilot: bool
    daily_limit: int
    questions: list[str] = Field(default_factory=list)  # the PM's open questions/assumptions
    error: str = ""  # why it paused on its own, or why planning failed
    created_at: datetime
    updated_at: datetime


class ProjectDetail(Project):
    items: list[BacklogItem]
