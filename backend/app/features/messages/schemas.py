"""Messages between the founder and the team, in a thread on a run or a project."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class ThreadKind(StrEnum):
    RUN = "run"
    PROJECT = "project"


class NewMessage(BaseModel):
    """The founder writes to one agent about one run or one project."""

    run_id: str | None = None
    project_id: str | None = None
    to: str = Field(default="cto", pattern=r"^[a-z][a-z_]*$")  # role id: pm, cto, qa, …
    body: str = Field(min_length=1, max_length=10_000)

    @model_validator(mode="after")
    def _one_thread(self) -> "NewMessage":
        if bool(self.run_id) == bool(self.project_id):
            raise ValueError("Write about either a run or a project")
        return self

    @property
    def thread(self) -> tuple[ThreadKind, str]:
        if self.run_id:
            return ThreadKind.RUN, self.run_id
        return ThreadKind.PROJECT, str(self.project_id)


class Message(BaseModel):
    id: int
    company_id: str
    thread: ThreadKind
    thread_id: str
    author: str  # "founder", or the agent's role id (pm, cto, …)
    name: str  # who: "You", "Mira", "Kabir", …
    to: str  # the role it's addressed to (for the founder's), or "founder"
    body: str
    created_at: datetime
