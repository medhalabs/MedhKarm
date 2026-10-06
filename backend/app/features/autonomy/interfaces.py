from typing import Any, Protocol

from app.features.autonomy.schemas import AutonomySettings


class AutonomyRepository(Protocol):
    async def get(self, company_id: str, project_id: str | None) -> AutonomySettings | None: ...

    async def save(
        self, company_id: str, project_id: str | None, settings: AutonomySettings
    ) -> None: ...

    async def delete(self, company_id: str, project_id: str) -> None: ...


class RunProjects(Protocol):
    """Which project a run belongs to, if any (a backlog item started it)."""

    async def project_of(self, run_id: str) -> str | None: ...


class ProjectOwner(Protocol):
    async def owned(self, project_id: str, company_id: str) -> Any:
        """Raises NotFoundError unless the project is the company's."""
        ...
