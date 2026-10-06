"""AutonomyRepository on Postgres. The company default is stored with project_id ''."""

import uuid

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.autonomy.models import AutonomySettingsRow
from app.features.autonomy.schemas import AutonomySettings


class SqlAutonomyRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def get(self, company_id: str, project_id: str | None) -> AutonomySettings | None:
        async with self._sessions() as session:
            row = await session.get(AutonomySettingsRow, (uuid.UUID(company_id), project_id or ""))
            return AutonomySettings.model_validate(row.settings) if row else None

    async def save(
        self, company_id: str, project_id: str | None, settings: AutonomySettings
    ) -> None:
        values = {"settings": settings.model_dump(mode="json")}
        statement = (
            insert(AutonomySettingsRow)
            .values(company_id=uuid.UUID(company_id), project_id=project_id or "", **values)
            .on_conflict_do_update(index_elements=["company_id", "project_id"], set_=values)
        )
        async with self._sessions() as session, session.begin():
            await session.execute(statement)

    async def delete(self, company_id: str, project_id: str) -> None:
        statement = delete(AutonomySettingsRow).where(
            AutonomySettingsRow.company_id == uuid.UUID(company_id),
            AutonomySettingsRow.project_id == project_id,
        )
        async with self._sessions() as session, session.begin():
            await session.execute(statement)
