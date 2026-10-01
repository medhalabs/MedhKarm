"""What a standup is: the founder's morning summary, built from the activity log."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel


class ProjectStatus(StrEnum):
    """Where a run stands at the end of the standup window."""

    IN_PROGRESS = "in_progress"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    STALLED = "stalled"  # open, but no activity for a while: the worker may have stopped
    RELEASED = "released"
    REJECTED = "rejected"
    FAILED = "failed"
    ERROR = "error"  # something broke and the worker gave up


class StandupItem(BaseModel):
    run_id: str
    project: str  # the founder's request, shortened
    text: str  # one plain sentence
    member: str | None = None  # who it's about, e.g. "Isha"
    at: datetime | None = None  # when it happened, or since when it has been waiting


class ProjectSummary(BaseModel):
    run_id: str
    project: str
    status: ProjectStatus
    tasks_done: int
    tasks_total: int
    tokens: int  # model tokens used inside the window


class Standup(BaseModel):
    day: date
    timezone: str
    since: datetime
    until: datetime
    headline: str
    done: list[StandupItem]
    planned: list[StandupItem]
    blocked: list[StandupItem]
    needs_you: list[StandupItem]
    projects: list[ProjectSummary]
    sent_back: int  # tasks the CTO sent back for changes inside the window
    tokens: int
