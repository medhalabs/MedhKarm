"""The founder's autonomy dial. Settings are kept for the company, and a project can have its
own. A run's release gate uses its project's settings, else the company's, else the team
template's rules untouched (so a company that never opens this page behaves as before)."""

from app.features.approvals.schemas import ApprovalPolicy
from app.features.autonomy.exceptions import NoProjectSettingsError
from app.features.autonomy.interfaces import AutonomyRepository, ProjectOwner, RunProjects
from app.features.autonomy.policy import build_policy, describe
from app.features.autonomy.schemas import AutonomySettings, AutonomyView, Scope


class AutonomyService:
    def __init__(
        self,
        settings: AutonomyRepository,
        base_policy: ApprovalPolicy,
        runs: RunProjects,
        projects: ProjectOwner,
    ) -> None:
        self._settings = settings
        self._base = base_policy
        self._runs = runs
        self._projects = projects

    async def view(self, company_id: str, project_id: str | None = None) -> AutonomyView:
        await self._check(company_id, project_id)
        own = await self._settings.get(company_id, project_id)
        found = own
        if found is None and project_id:  # no settings of its own: the company's
            found = await self._settings.get(company_id, None)
        return self._view(project_id, own is not None, found or AutonomySettings())

    async def save(
        self, company_id: str, project_id: str | None, settings: AutonomySettings
    ) -> AutonomyView:
        await self._check(company_id, project_id)
        await self._settings.save(company_id, project_id, settings)
        return self._view(project_id, True, settings)

    async def reset(self, company_id: str, project_id: str | None) -> AutonomyView:
        """A project goes back to the company's settings."""
        if not project_id:
            raise NoProjectSettingsError("Only a project can go back to the company's settings")
        await self._check(company_id, project_id)
        await self._settings.delete(company_id, project_id)
        return await self.view(company_id, project_id)

    async def for_run(self, company_id: str | None, run_id: str) -> tuple[ApprovalPolicy, bool]:
        """The release policy and whether to go live, for a run (evals have no company: the
        template's own rules)."""
        if company_id is None:
            return self._base, True
        project_id = await self._runs.project_of(run_id)
        found = await self._settings.get(company_id, project_id) if project_id else None
        found = found or await self._settings.get(company_id, None)
        if found is None:
            return self._base, True
        return build_policy(self._base, found), found.go_live

    async def _check(self, company_id: str, project_id: str | None) -> None:
        if project_id:
            await self._projects.owned(project_id, company_id)

    @staticmethod
    def _view(project_id: str | None, own: bool, settings: AutonomySettings) -> AutonomyView:
        return AutonomyView(
            scope=Scope.PROJECT if project_id else Scope.COMPANY,
            project_id=project_id,
            own=own,
            settings=settings,
            summary=describe(settings),
        )
