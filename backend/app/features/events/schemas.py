"""What an event is. The office, the standup and cost tracking are all built from these."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventType(StrEnum):
    RUN_STARTED = "run.started"
    RUN_RESUMED = "run.resumed"
    RUN_FINISHED = "run.finished"
    PROJECT_SCAFFOLDED = "project.scaffolded"
    CODEBASE_MAPPED = "codebase.mapped"
    PLAN_CREATED = "plan.created"
    TASK_ASSIGNED = "task.assigned"
    REVIEW_FINISHED = "review.finished"
    WORK_STARTED = "work.started"
    TOOL_USED = "tool.used"
    MODEL_USED = "model.used"
    WORK_FINISHED = "work.finished"
    CHECK_FINISHED = "check.finished"
    SECURITY_FINISHED = "security.finished"
    DEPLOY_FINISHED = "deploy.finished"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_DECIDED = "approval.decided"
    CHANGES_DELIVERED = "changes.delivered"
    MESSAGE_POSTED = "message.posted"  # the founder and an agent talking about the run


class Actor(StrEnum):
    """Who did it. Agent roles match the team template; founder and system are not agents."""

    FOUNDER = "founder"
    PM = "pm"
    CTO = "cto"
    DEVELOPER = "developer"
    QA = "qa"
    SECURITY = "security"
    DEVOPS = "devops"
    SYSTEM = "system"


# Events that end a run: live streams stop after one of these.
FINAL_TYPES = frozenset({EventType.RUN_FINISHED})


class NewEvent(BaseModel):
    run_id: str
    actor: Actor
    type: EventType
    summary: str = Field(max_length=500)  # one plain sentence for the activity feed
    data: dict[str, Any] = Field(default_factory=dict)  # details for the office and debugging
    tokens: int = Field(default=0, ge=0)  # model tokens this event cost


class Event(NewEvent):
    id: int  # increases with every event: the order things happened in
    occurred_at: datetime


class RunTotals(BaseModel):
    run_id: str
    events: int
    tokens: int
