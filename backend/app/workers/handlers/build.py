"""Job handlers for build runs: start a run, and resume it after the founder's decision.

Both are safe to repeat. Before doing anything they look at the run's checkpoint: a fresh run
starts, a run interrupted mid-way (worker died, deploy) carries on from its last finished
step, and a run already at the gate or finished is only reported.
"""

import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol

from app.features.events.interfaces import EventStore
from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.jobs.exceptions import PermanentJobError
from app.features.runs.exceptions import RunNotFoundError
from app.features.runs.schemas import Run, RunStatus
from app.features.runs.service import RunService
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.schemas import RunOutcome
from app.features.workflows.service import WorkflowService

WorkflowFactory = Callable[[], AbstractAsyncContextManager[WorkflowService]]
logger = logging.getLogger(__name__)


class RunListener(Protocol):
    """Told when a run ends (the backlog moves its item on). Must be safe to call twice."""

    async def on_run_finished(
        self, run_id: str, status: RunStatus, delivery: dict[str, Any] | None = None
    ) -> None: ...


FINISHED = {
    "released": RunStatus.RELEASED,
    "rejected": RunStatus.REJECTED,
    "failed": RunStatus.FAILED,
}


class _BuildHandler:
    def __init__(
        self,
        runs: RunService,
        workflow: WorkflowFactory,
        sandboxes: SandboxProvider,
        events: EventStore | None = None,
        listener: RunListener | None = None,
    ) -> None:
        self._runs = runs
        self._workflow = workflow
        self._sandboxes = sandboxes
        self._events = events
        self._listener = listener

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        run = await self._load(payload)
        await self._runs.set_status(run.id, RunStatus.RUNNING)
        async with self._workflow() as workflow:
            outcome = await self._advance(workflow, run, payload)
        status = await self._report(outcome)
        if self._listener and status != RunStatus.WAITING_FOR_APPROVAL:
            # A failure here retries the job; the run is already finished, so only this repeats.
            await self._listener.on_run_finished(run.id, status, outcome.state.get("delivery"))
        return {"run_id": run.id, "status": status}

    async def _advance(
        self, workflow: WorkflowService, run: Run, payload: dict[str, Any]
    ) -> RunOutcome:
        raise NotImplementedError

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        """Out of retries: mark the run, tell the log, and remove its sandbox."""
        run_id = str(payload.get("run_id", ""))
        if not run_id:
            return
        await self._runs.set_status(run_id, RunStatus.ERROR, error=error)
        await RunRecorder(self._events, run_id).record(
            Actor.SYSTEM,
            EventType.RUN_FINISHED,
            "Stopped: something went wrong",
            {"status": "error", "error": error[:500]},
        )
        async with self._workflow() as workflow:
            sandbox_id = (await workflow.get(run_id)).state.get("sandbox_id")
        if sandbox_id:
            await self._sandboxes.destroy(sandbox_id)
        if self._listener:
            try:
                await self._listener.on_run_finished(run_id, RunStatus.ERROR)
            except Exception:  # the backlog's tick catches up with the run's status later
                logger.exception("Couldn't report run %s's failure to its listener", run_id)

    async def _load(self, payload: dict[str, Any]) -> Run:
        try:
            return await self._runs.get(str(payload["run_id"]))
        except (KeyError, RunNotFoundError) as error:
            raise PermanentJobError(f"Unknown run in job payload: {payload}") from error

    async def _report(self, outcome: RunOutcome) -> RunStatus:
        if outcome.waiting_for_approval:
            status = RunStatus.WAITING_FOR_APPROVAL
            await self._runs.set_status(outcome.run_id, status, gate=outcome.gate)
            return status
        status = FINISHED.get(str(outcome.state.get("status")), RunStatus.ERROR)
        error = None if status != RunStatus.ERROR else "Run ended without a result"
        await self._runs.set_status(
            outcome.run_id,
            status,
            error=error,
            delivery=outcome.state.get("delivery"),
            deployment=outcome.state.get("deployment"),
        )
        return status


class StartBuild(_BuildHandler):
    async def _advance(
        self, workflow: WorkflowService, run: Run, payload: dict[str, Any]
    ) -> RunOutcome:
        current = await workflow.get(run.id)
        if not current.state:
            repo = run.repo.model_dump(mode="json") if run.repo else None
            new_repo = run.new_repo.model_dump(mode="json") if run.new_repo else None
            return await workflow.start(
                run.id, run.request, run.test_command, repo=repo, new_repo=new_repo
            )
        if current.next_nodes and not current.waiting_for_approval:
            return await workflow.continue_run(run.id)
        return current


class ResumeBuild(_BuildHandler):
    async def _advance(
        self, workflow: WorkflowService, run: Run, payload: dict[str, Any]
    ) -> RunOutcome:
        current = await workflow.get(run.id)
        if current.waiting_for_approval:
            return await workflow.resume(
                run.id, bool(payload.get("approved")), str(payload.get("feedback", ""))
            )
        if current.next_nodes:
            return await workflow.continue_run(run.id)
        return current
