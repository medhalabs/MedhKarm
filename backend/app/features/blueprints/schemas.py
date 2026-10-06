"""A blueprint: the plan Lekha writes for the founder to read and approve before any code."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.features.runs.schemas import StartRun


class BlueprintStatus(StrEnum):
    WRITING = "writing"  # Lekha is writing the documents
    READY = "ready"  # waiting for the founder to read, comment or approve
    REVISING = "revising"  # Lekha is rewriting after a comment
    APPROVED = "approved"  # approved: the build run started
    FAILED = "failed"  # Lekha couldn't finish (model errors); the founder can ask again


class Doc(BaseModel):
    id: str
    title: str
    path: str  # where it goes in the project's repository, e.g. docs/05-architecture.md
    content: str
    format: Literal["markdown", "html"] = "markdown"  # html: screen mockups, shown in a sandbox


class Comment(BaseModel):
    author: str  # "founder" or "lekha"
    text: str
    at: datetime


class NewBlueprint(BaseModel):
    """What the founder agreed with the CTO: the same fields as starting a run."""

    brief: StartRun


class NewComment(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class Blueprint(BaseModel):
    id: str
    company_id: str
    title: str
    brief: StartRun
    status: BlueprintStatus
    docs: list[Doc] = Field(default_factory=list)
    comments: list[Comment] = Field(default_factory=list)
    progress: str = ""  # "Writing the architecture (3 of 7)"
    error: str = ""
    run_id: str | None = None  # the build run, once approved
    revision: int = 0  # 0 = first draft; +1 for each rewrite after a comment
    created_at: datetime
    updated_at: datetime


class ApprovedPlan(BaseModel):
    """What the build run is given: the documents to put in the repository, and a summary."""

    docs: list[Doc]


class BlueprintSummary(BaseModel):
    """A blueprint in a list (no documents)."""

    id: str
    title: str
    status: BlueprintStatus
    progress: str = ""
    run_id: str | None = None
    created_at: datetime
    updated_at: datetime
