"""JobQueue in memory, for tests. Set `now` to move its clock."""

from datetime import UTC, datetime, timedelta
from typing import Any

from app.features.jobs.schemas import Job, JobStatus


class InMemoryJobQueue:
    def __init__(self) -> None:
        self.jobs: list[Job] = []
        self.now: datetime | None = None

    def _now(self) -> datetime:
        return self.now or datetime.now(UTC)

    async def enqueue(
        self,
        kind: str,
        payload: dict[str, Any],
        *,
        unique_key: str | None = None,
        run_after: datetime | None = None,
        max_attempts: int = 3,
    ) -> Job | None:
        if unique_key and any(j.unique_key == unique_key for j in self.jobs):
            return None
        job = Job(
            id=len(self.jobs) + 1,
            kind=kind,
            payload=payload,
            status=JobStatus.QUEUED,
            attempts=0,
            max_attempts=max_attempts,
            run_after=run_after or self._now(),
            unique_key=unique_key,
            created_at=self._now(),
        )
        self.jobs.append(job)
        return job.model_copy()

    async def claim(
        self, worker_id: str, lease: timedelta, kinds: list[str] | None = None
    ) -> Job | None:
        now = self._now()
        for job in self.jobs:
            if kinds is not None and job.kind not in kinds:
                continue
            due = job.status == JobStatus.QUEUED and job.run_after <= now
            expired = (
                job.status == JobStatus.RUNNING
                and job.locked_until is not None
                and job.locked_until < now
            )
            if due or expired:
                job.status, job.attempts = JobStatus.RUNNING, job.attempts + 1
                job.locked_by, job.locked_until = worker_id, now + lease
                return job.model_copy()
        return None

    async def extend(self, job_id: int, worker_id: str, lease: timedelta) -> bool:
        job = self.jobs[job_id - 1]
        if job.status != JobStatus.RUNNING or job.locked_by != worker_id:
            return False
        job.locked_until = self._now() + lease
        return True

    async def complete(self, job_id: int, result: dict[str, Any] | None = None) -> None:
        job = self.jobs[job_id - 1]
        job.status, job.result, job.finished_at = JobStatus.DONE, result, self._now()
        job.locked_by = job.locked_until = None

    async def fail(self, job_id: int, error: str, retry_after: timedelta | None) -> None:
        job = self.jobs[job_id - 1]
        job.last_error, job.locked_by, job.locked_until = error, None, None
        if retry_after is None:
            job.status, job.finished_at = JobStatus.FAILED, self._now()
        else:
            job.status, job.run_after = JobStatus.QUEUED, self._now() + retry_after

    async def release(self, job_id: int) -> None:
        job = self.jobs[job_id - 1]
        job.status, job.attempts = JobStatus.QUEUED, max(job.attempts - 1, 0)
        job.locked_by = job.locked_until = None

    async def get(self, job_id: int) -> Job | None:
        return self.jobs[job_id - 1].model_copy() if 0 < job_id <= len(self.jobs) else None
