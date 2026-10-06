from enum import StrEnum

from pydantic import BaseModel, Field


class State(StrEnum):
    OK = "ok"  # signed off
    WARN = "warn"  # signed off, with something to know
    FAIL = "fail"  # a problem
    WAITING = "waiting"  # not done yet
    SKIPPED = "skipped"  # not part of this run


class Signoff(BaseModel):
    """One person's word on a release: who, what they checked, and how it went."""

    role: str
    name: str
    title: str  # "QA engineer"
    state: State
    headline: str  # one plain sentence
    details: list[str] = Field(default_factory=list)
    url: str = ""  # a preview, the live site or a pull request, if there is one
