"""What the inbox reads, from the runs, projects and messages services."""

from typing import Protocol

from app.features.blueprints.schemas import BlueprintSummary
from app.features.messages.schemas import Message
from app.features.projects.schemas import Project, ProjectDetail
from app.features.runs.schemas import Run


class RunsReader(Protocol):
    async def list(self, limit: int = 50, company_id: str | None = None) -> list[Run]: ...


class ProjectsReader(Protocol):
    async def list(self, limit: int = 50, company_id: str | None = None) -> list[Project]: ...

    async def get(self, project_id: str) -> ProjectDetail: ...


class MessagesReader(Protocol):
    async def recent(self, company_id: str, limit: int = 20) -> list[Message]: ...


class BlueprintsReader(Protocol):
    async def list(self, company_id: str) -> list[BlueprintSummary]: ...
