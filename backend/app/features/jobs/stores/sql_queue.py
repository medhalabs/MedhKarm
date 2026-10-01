"""JobQueue on Postgres. Workers claim with `FOR UPDATE SKIP LOCKED`, so any number of them can
poll the same table without taking the same job. Times come from the database clock."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select, true, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.jobs.models import JobRow
from app.features.jobs.schemas import Job, JobStatus


class SqlJobQueue:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def enqueue(
        self,
        kind: str,
        payload: dict[str, Any],
        *,
        unique_key: str | None = None,
        run_after: datetime | None = None,
        max_attempts: int = 3,
    ) -> Job | None:
        values: dict[str, Any] = {
            "kind": kind,
            "payload": payload,
            "unique_key": unique_key,
            "max_attempts": max_attempts,
        }
        if run_after:
            values["run_after"] = run_after
        statement = insert(JobRow).values(**values)
        if unique_key:
            statement = statement.on_conflict_do_nothing(index_elements=["unique_key"])
        async with self._sessions() as session, session.begin():
            row = (await session.scalars(statement.returning(JobRow))).one_or_none()
            return _to_job(row) if row else None

    async def claim(
        self, worker_id: str, lease: timedelta, kinds: list[str] | None = None
    ) -> Job | None:
        due = (
            select(JobRow.id)
            .where(
                or_(
                    (JobRow.status == JobStatus.QUEUED) & (JobRow.run_after <= func.now()),
                    (JobRow.status == JobStatus.RUNNING) & (JobRow.locked_until < func.now()),
                ),
                JobRow.kind.in_(kinds) if kinds is not None else true(),
            )
            .order_by(JobRow.id)
            .limit(1)
            .with_for_update(skip_locked=True)
            .scalar_subquery()
        )
        statement = (
            update(JobRow)
            .where(JobRow.id == due)
            .values(
                status=JobStatus.RUNNING,
                attempts=JobRow.attempts + 1,
                locked_by=worker_id,
                locked_until=func.now() + lease,
            )
            .returning(JobRow)
        )
        async with self._sessions() as session, session.begin():
            row = (await session.scalars(statement)).one_or_none()
            return _to_job(row) if row else None

    async def extend(self, job_id: int, worker_id: str, lease: timedelta) -> bool:
        statement = (
            update(JobRow)
            .where(
                JobRow.id == job_id,
                JobRow.locked_by == worker_id,
                JobRow.status == JobStatus.RUNNING,
            )
            .values(locked_until=func.now() + lease)
            .returning(JobRow.id)
        )
        async with self._sessions() as session, session.begin():
            return (await session.scalars(statement)).one_or_none() is not None

    async def complete(self, job_id: int, result: dict[str, Any] | None = None) -> None:
        await self._update(
            job_id,
            status=JobStatus.DONE,
            result=result,
            finished_at=func.now(),
            locked_by=None,
            locked_until=None,
        )

    async def fail(self, job_id: int, error: str, retry_after: timedelta | None) -> None:
        if retry_after is None:
            await self._update(
                job_id,
                status=JobStatus.FAILED,
                last_error=error,
                finished_at=func.now(),
                locked_by=None,
                locked_until=None,
            )
        else:
            await self._update(
                job_id,
                status=JobStatus.QUEUED,
                last_error=error,
                run_after=func.now() + retry_after,
                locked_by=None,
                locked_until=None,
            )

    async def release(self, job_id: int) -> None:
        await self._update(
            job_id,
            status=JobStatus.QUEUED,
            attempts=func.greatest(JobRow.attempts - 1, 0),
            locked_by=None,
            locked_until=None,
        )

    async def get(self, job_id: int) -> Job | None:
        async with self._sessions() as session:
            row = await session.get(JobRow, job_id)
            return _to_job(row) if row else None

    async def _update(self, job_id: int, **values: Any) -> None:
        async with self._sessions() as session, session.begin():
            await session.execute(update(JobRow).where(JobRow.id == job_id).values(**values))


def _to_job(row: JobRow) -> Job:
    return Job(
        id=row.id,
        kind=row.kind,
        payload=row.payload,
        status=JobStatus(row.status),
        attempts=row.attempts,
        max_attempts=row.max_attempts,
        run_after=row.run_after,
        locked_by=row.locked_by,
        locked_until=row.locked_until,
        unique_key=row.unique_key,
        last_error=row.last_error,
        result=row.result,
        created_at=row.created_at,
        finished_at=row.finished_at,
    )
