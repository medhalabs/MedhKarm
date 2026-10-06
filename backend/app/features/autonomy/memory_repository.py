"""AutonomyRepository in memory, for tests."""

from app.features.autonomy.schemas import AutonomySettings


class InMemoryAutonomyRepository:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], AutonomySettings] = {}

    async def get(self, company_id: str, project_id: str | None) -> AutonomySettings | None:
        return self.rows.get((company_id, project_id or ""))

    async def save(
        self, company_id: str, project_id: str | None, settings: AutonomySettings
    ) -> None:
        self.rows[(company_id, project_id or "")] = settings

    async def delete(self, company_id: str, project_id: str) -> None:
        self.rows.pop((company_id, project_id), None)
