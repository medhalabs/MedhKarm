"""RunRepository on Postgres."""

from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.repos.schemas import NewRepo, RepoSource
from app.features.runs.models import RunRow
from app.features.runs.schemas import Run, RunStatus


class SqlRunRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def create(
        self,
        run_id: str,
        request: str,
        test_command: str,
        repo: RepoSource | None = None,
        new_repo: NewRepo | None = None,
    ) -> Run:
        row = RunRow(
            id=run_id,
            request=request,
            test_command=test_command,
            repo=repo.model_dump(mode="json") if repo else None,
            new_repo=new_repo.model_dump(mode="json") if new_repo else None,
            status=RunStatus.QUEUED,
        )
        async with self._sessions() as session, session.begin():
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return _to_run(row)

    async def get(self, run_id: str) -> Run | None:
        async with self._sessions() as session:
            row = await session.get(RunRow, run_id)
            return _to_run(row) if row else None

    async def list(self, limit: int = 50) -> list[Run]:
        query = select(RunRow).order_by(RunRow.created_at.desc()).limit(limit)
        async with self._sessions() as session:
            return [_to_run(row) for row in (await session.scalars(query)).all()]

    async def set_status(
        self,
        run_id: str,
        status: RunStatus,
        gate: dict[str, Any] | None = None,
        error: str | None = None,
        delivery: dict[str, Any] | None = None,
        deployment: dict[str, Any] | None = None,
    ) -> None:
        values: dict[str, Any] = {"status": status, "gate": gate, "error": error}
        if delivery is not None:
            values["delivery"] = delivery
        if deployment is not None:
            values["deployment"] = deployment
        statement = (
            update(RunRow).where(RunRow.id == run_id).values(**values, updated_at=func.now())
        )
        async with self._sessions() as session, session.begin():
            await session.execute(statement)

    async def transition(self, run_id: str, from_status: RunStatus, to_status: RunStatus) -> bool:
        statement = (
            update(RunRow)
            .where(RunRow.id == run_id, RunRow.status == from_status)
            .values(status=to_status, updated_at=func.now())
            .returning(RunRow.id)
        )
        async with self._sessions() as session, session.begin():
            return (await session.scalars(statement)).one_or_none() is not None


def _to_run(row: RunRow) -> Run:
    return Run(
        id=row.id,
        request=row.request,
        test_command=row.test_command,
        repo=RepoSource.model_validate(row.repo) if row.repo else None,
        new_repo=NewRepo.model_validate(row.new_repo) if row.new_repo else None,
        status=RunStatus(row.status),
        gate=row.gate,
        error=row.error,
        delivery=row.delivery,
        deployment=row.deployment,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
