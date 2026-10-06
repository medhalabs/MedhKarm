from app.core.database import session_factory
from app.features.autonomy.repository import SqlAutonomyRepository
from app.features.autonomy.service import AutonomyService
from app.features.projects.dependencies import get_project_service
from app.features.projects.repository import SqlProjectRepository
from app.features.teams.dependencies import get_team_service


class ProjectsOfRuns:
    """Which project a run belongs to: the backlog item that started it."""

    def __init__(self, projects: SqlProjectRepository) -> None:
        self._projects = projects

    async def project_of(self, run_id: str) -> str | None:
        item = await self._projects.item_for_run(run_id)
        return item.project_id if item else None


def get_autonomy_service() -> AutonomyService:
    template = get_team_service().get_template("software")
    return AutonomyService(
        SqlAutonomyRepository(session_factory),
        template.approval,
        ProjectsOfRuns(SqlProjectRepository(session_factory)),
        get_project_service(),
    )
