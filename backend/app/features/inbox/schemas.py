"""The founder's inbox: everything waiting for them, in one place."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.features.messages.schemas import Message


class Approval(BaseModel):
    """A run waiting at the release gate."""

    run_id: str
    request: str
    summary: str = ""
    reasons: list[str] = Field(default_factory=list)  # why the rules asked
    preview_url: str = ""
    security: list[str] = Field(default_factory=list)  # the security engineer's warnings
    waiting_since: datetime


class Questions(BaseModel):
    """The PM's open questions on a project."""

    project_id: str
    project_name: str
    questions: list[str]


class Blocked(BaseModel):
    """A backlog item that stopped: retry or skip it."""

    project_id: str
    project_name: str
    item_id: str
    title: str
    note: str


class Inbox(BaseModel):
    approvals: list[Approval] = Field(default_factory=list)
    questions: list[Questions] = Field(default_factory=list)
    blocked: list[Blocked] = Field(default_factory=list)
    replies: list[Message] = Field(default_factory=list)  # the team's latest answers

    @property
    def count(self) -> int:
        """Things that need the founder (replies are for reading, not counted)."""
        return (
            len(self.approvals) + sum(len(q.questions) for q in self.questions) + len(self.blocked)
        )


class InboxCount(BaseModel):
    count: int
