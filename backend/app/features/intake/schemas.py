"""Starting a run by talking: the founder describes what they want, the CTO asks what's
unclear, and the conversation ends in a brief the founder confirms."""

from typing import Literal

from pydantic import BaseModel, Field

from app.features.starters.schemas import StackChoice


class Turn(BaseModel):
    role: Literal["founder", "agent"]
    text: str = Field(min_length=1, max_length=50_000)


class About(BaseModel):
    """The live project a conversation is about (a change request on a released run)."""

    repo_url: str = Field(max_length=300)
    name: str = Field(default="", max_length=200)  # what it is, e.g. the first request's title


class Conversation(BaseModel):
    turns: list[Turn] = Field(min_length=1, max_length=40)
    about: About | None = None  # set: a change to this existing project


class Brief(BaseModel):
    """Everything a run needs, agreed in the conversation (StartRun-shaped)."""

    request: str = Field(min_length=3, max_length=50_000)  # the whole ask, answers included
    summary: str = ""  # two or three lines for the founder to check
    repo_url: str | None = None  # an existing GitHub repository
    branch: str | None = None
    create_repo: bool = True  # new project: a private repo on release
    new_repo_name: str | None = None
    stack: StackChoice = Field(default_factory=StackChoice)
    test_command: str | None = None
    scale: Literal["small", "big"] | None = None  # the CTO's view of a change's size


class Reply(BaseModel):
    agent: str  # who answered ("Kabir")
    text: str  # the agent's message (Markdown)
    brief: Brief | None = None  # set when the agent thinks it's ready to start


class ProjectBrief(BaseModel):
    """A project agreed with the PM (NewProject-shaped): she plans its backlog next."""

    name: str = Field(min_length=2, max_length=80)
    goal: str = Field(min_length=10, max_length=50_000)  # the whole product, answers included
    summary: str = ""
    repo_url: str | None = None
    stack: StackChoice = Field(default_factory=StackChoice)
    autopilot: bool = False  # work through the backlog on its own
    daily_limit: int = Field(default=2, ge=1, le=10)


class ProjectReply(BaseModel):
    agent: str
    text: str
    brief: ProjectBrief | None = None
