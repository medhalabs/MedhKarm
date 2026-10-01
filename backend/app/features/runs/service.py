"""Starting runs and deciding approvals. The API only records the request and queues a job;
workers do the work (see app/workers/handlers/build.py)."""

import uuid
from typing import Any

from app.features.jobs.interfaces import JobQueue
from app.features.runs.exceptions import RunNotFoundError, RunNotWaitingError
from app.features.runs.interfaces import RunRepository
from app.features.runs.schemas import ApprovalDecision, Run, RunStatus, StartRun

START_JOB = "build.start"
RESUME_JOB = "build.resume"


class RunService:
    def __init__(self, runs: RunRepository, jobs: JobQueue, max_attempts: int = 3) -> None:
        self._runs = runs
        self._jobs = jobs
        self._max_attempts = max_attempts

    async def start(self, body: StartRun) -> Run:
        run = await self._runs.create(uuid.uuid4().hex[:12], body.request, body.test_command)
        await self._jobs.enqueue(
            START_JOB,
            {"run_id": run.id},
            unique_key=f"{START_JOB}:{run.id}",
            max_attempts=self._max_attempts,
        )
        return run

    async def decide(self, run_id: str, decision: ApprovalDecision) -> Run:
        run = await self.get(run_id)
        if not await self._runs.transition(
            run_id, RunStatus.WAITING_FOR_APPROVAL, RunStatus.QUEUED
        ):
            raise RunNotWaitingError(f"Run {run_id} is {run.status}, not waiting for approval")
        await self._jobs.enqueue(
            RESUME_JOB,
            {"run_id": run_id, "approved": decision.approved, "feedback": decision.feedback},
            unique_key=f"{RESUME_JOB}:{run_id}",
            max_attempts=self._max_attempts,
        )
        return await self.get(run_id)

    async def get(self, run_id: str) -> Run:
        run = await self._runs.get(run_id)
        if run is None:
            raise RunNotFoundError(f"No run {run_id}")
        return run

    async def list(self, limit: int = 50) -> list[Run]:
        return await self._runs.list(min(max(limit, 1), 200))

    async def set_status(
        self,
        run_id: str,
        status: RunStatus,
        gate: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Workers report progress here."""
        await self._runs.set_status(run_id, status, gate, error)
