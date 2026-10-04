"""Starting runs and deciding approvals. The API only records the request and queues a job;
workers do the work (see app/workers/handlers/build.py)."""

import uuid
from typing import Any

from app.features.jobs.interfaces import JobQueue
from app.features.repos.schemas import NewRepo
from app.features.runs.exceptions import (
    RunAlreadyFinishedError,
    RunNotFoundError,
    RunNotWaitingError,
)
from app.features.runs.interfaces import RunRepository
from app.features.runs.schemas import (
    FINAL_STATUSES,
    ApprovalDecision,
    Run,
    RunStatus,
    StartRun,
)

START_JOB = "build.start"
RESUME_JOB = "build.resume"
CANCEL_JOB = "build.cancel"


class RunService:
    def __init__(self, runs: RunRepository, jobs: JobQueue, max_attempts: int = 3) -> None:
        self._runs = runs
        self._jobs = jobs
        self._max_attempts = max_attempts

    async def start(self, body: StartRun, company_id: str | None = None) -> Run:
        # No test command: the run detects one from the repository or the starter.
        new_repo = NewRepo(name=body.new_repo_name) if not body.repo and body.create_repo else None
        run = await self._runs.create(
            uuid.uuid4().hex[:12],
            body.request,
            body.test_command or "",
            body.repo,
            new_repo,
            None if body.repo else body.stack,
            company_id,
        )
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

    async def cancel(self, run_id: str) -> Run:
        """Stop a run: queued, running or waiting at the gate. A worker running it stops at
        once (it watches the status), and a cancel job removes its sandbox."""
        run = await self.get(run_id)
        if run.status in FINAL_STATUSES:
            raise RunAlreadyFinishedError(f"Run {run_id} is already {run.status}")
        await self._runs.set_status(run_id, RunStatus.CANCELLED, error="Cancelled by you")
        await self._jobs.enqueue(
            CANCEL_JOB,
            {"run_id": run_id},
            unique_key=f"{CANCEL_JOB}:{run_id}",
            max_attempts=self._max_attempts,
        )
        return await self.get(run_id)

    async def get(self, run_id: str) -> Run:
        run = await self._runs.get(run_id)
        if run is None:
            raise RunNotFoundError(f"No run {run_id}")
        return run

    async def list(self, limit: int = 50, company_id: str | None = None) -> list[Run]:
        return await self._runs.list(min(max(limit, 1), 200), company_id)

    async def owned(self, run_id: str, company_id: str) -> Run:
        """The run, if it's this company's; otherwise "not found" (never "forbidden", which
        would tell another company it exists)."""
        run = await self.get(run_id)
        if run.company_id != company_id:
            raise RunNotFoundError(f"No run {run_id}")
        return run

    async def run_ids(self, company_id: str) -> set[str]:
        return await self._runs.ids_for(company_id)

    async def adopt_unowned(self, company_id: str) -> int:
        return await self._runs.adopt_unowned(company_id)

    async def set_status(
        self,
        run_id: str,
        status: RunStatus,
        gate: dict[str, Any] | None = None,
        error: str | None = None,
        delivery: dict[str, Any] | None = None,
        deployment: dict[str, Any] | None = None,
    ) -> None:
        """Workers report progress here."""
        await self._runs.set_status(run_id, status, gate, error, delivery, deployment)
