"""SettingsRepository on Postgres."""

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.notifications.models import NotificationSettingsRow
from app.features.notifications.schemas import CompanySettings, NotificationSettings


class SqlSettingsRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def get(self, company_id: str) -> CompanySettings | None:
        async with self._sessions() as session:
            row = await session.get(NotificationSettingsRow, uuid.UUID(company_id))
            return _to_settings(row) if row else None

    async def save(self, company_id: str, settings: NotificationSettings) -> CompanySettings:
        values = settings.model_dump()
        statement = (
            insert(NotificationSettingsRow)
            .values(company_id=uuid.UUID(company_id), **values)
            .on_conflict_do_update(index_elements=["company_id"], set_=values)
            .returning(NotificationSettingsRow)
        )
        async with self._sessions() as session, session.begin():
            row = (await session.scalars(statement)).one()
            return _to_settings(row)

    async def all(self) -> list[CompanySettings]:
        async with self._sessions() as session:
            rows = (await session.scalars(select(NotificationSettingsRow))).all()
            return [_to_settings(r) for r in rows]


def _to_settings(row: NotificationSettingsRow) -> CompanySettings:
    return CompanySettings(
        company_id=str(row.company_id),
        email=row.email,
        whatsapp=row.whatsapp,
        standup_on=row.standup_on,
        standup_hour=row.standup_hour,
        weekly_on=row.weekly_on,
        updated_at=row.updated_at,
    )
