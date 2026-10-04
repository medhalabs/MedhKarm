"""CompanyRepository on Postgres."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.companies.models import CompanyRow
from app.features.companies.schemas import Company


class SqlCompanyRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def create(self, name: str) -> Company:
        row = CompanyRow(id=uuid.uuid4(), name=name)
        async with self._sessions() as session, session.begin():
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return _to_company(row)

    async def get(self, company_id: str) -> Company | None:
        try:
            key = uuid.UUID(company_id)
        except ValueError:
            return None
        async with self._sessions() as session:
            row = await session.get(CompanyRow, key)
            return _to_company(row) if row else None

    async def count(self) -> int:
        async with self._sessions() as session:
            return int(await session.scalar(select(func.count()).select_from(CompanyRow)) or 0)


def _to_company(row: CompanyRow) -> Company:
    return Company(id=str(row.id), name=row.name, created_at=row.created_at)
