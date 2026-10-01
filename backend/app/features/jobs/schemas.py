"""What a job is: one piece of background work, kept in Postgres until it's done."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class JobStatus(StrEnum):
    QUEUED = "queued"  # waiting for a worker (or for `run_after`, when retrying)
    RUNNING = "running"  # claimed by a worker that holds the lease until `locked_until`
    DONE = "done"
    FAILED = "failed"  # gave up: out of attempts, or a permanent error


class Job(BaseModel):
    id: int
    kind: str  # which handler runs it, e.g. "build.start"
    payload: dict[str, Any]
    status: JobStatus
    attempts: int  # claims so far, including the current one
    max_attempts: int
    run_after: datetime
    locked_by: str | None = None
    locked_until: datetime | None = None
    unique_key: str | None = None  # enqueueing the same key twice is a no-op
    last_error: str | None = None
    result: dict[str, Any] | None = None
    created_at: datetime
    finished_at: datetime | None = None
