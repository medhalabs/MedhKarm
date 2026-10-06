"""Public share links: a founder can show one finished build to anyone, with no sign-in. What
the public sees is a safe, whitelisted view of the run (service.py), never the whole log."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Share(BaseModel):
    """The founder's side: the link and how often it was opened."""

    token: str
    run_id: str
    views: int = 0
    created_at: datetime


class PublicMember(BaseModel):
    role: str
    title: str
    name: str


class PublicEvent(BaseModel):
    """An event in the shape the office replay reads (ActivityEvent), with only safe fields."""

    id: int
    run_id: str  # the share token, never the real run id
    actor: str
    type: str
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime
    tokens: int = 0


class PublicStats(BaseModel):
    tasks: int  # tasks the team built
    minutes: int  # from the first event to the last
    checks_passed: bool
    security_clean: bool
    docs_updated: bool


class PublicShare(BaseModel):
    title: str
    status: str  # "released", "waiting_for_approval", "rejected", ...
    team: list[PublicMember]
    events: list[PublicEvent]
    stats: PublicStats
    has_demo: bool
    live_url: str = ""  # the app, if it was put online
