from datetime import datetime, timedelta
from typing import Any, Protocol

from app.features.jobs.schemas import Job


class JobQueue(Protocol):
    """Background jobs. Workers claim a job with a lease and keep extending it while they work;
    a job whose lease runs out (the worker died) is claimed again by any worker."""

    async def enqueue(
        self,
        kind: str,
        payload: dict[str, Any],
        *,
        unique_key: str | None = None,
        run_after: datetime | None = None,
        max_attempts: int = 3,
    ) -> Job | None:
        """The new job, or None when a job with `unique_key` already exists."""
        ...

    async def claim(
        self, worker_id: str, lease: timedelta, kinds: list[str] | None = None
    ) -> Job | None:
        """The oldest job that is due (or whose lease ran out), now locked to `worker_id`.
        `kinds` limits it to jobs this worker can handle."""
        ...

    async def extend(self, job_id: int, worker_id: str, lease: timedelta) -> bool:
        """Keep the lease. False when this worker no longer holds the job."""
        ...

    async def complete(self, job_id: int, result: dict[str, Any] | None = None) -> None: ...

    async def fail(self, job_id: int, error: str, retry_after: timedelta | None) -> None:
        """Retry after `retry_after`, or give up for good when it's None."""
        ...

    async def release(self, job_id: int) -> None:
        """Hand the job back without counting the attempt (the worker is shutting down)."""
        ...

    async def get(self, job_id: int) -> Job | None: ...


class JobHandler(Protocol):
    """Does one kind of job. `run` may be called again for the same payload (a retry, or another
    worker taking over after a crash), so it must be safe to repeat."""

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None: ...

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        """Called once when the job has failed for good: tidy up, tell the founder."""
        ...
