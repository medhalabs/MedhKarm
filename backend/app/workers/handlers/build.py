"""Job handlers for build runs: start a run, and resume it after the founder's decision.

Both are safe to repeat. Before doing anything they look at the run's checkpoint: a fresh run
starts, a run interrupted mid-way (worker died, deploy) carries on from its last finished
step, and a run already at the gate or finished is only reported.
"""

import asyncio
import contextlib
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
CANCEL_POLL_SECONDS = 3.0  # how often a running build checks whether the founder cancelled it
CANCELLED = {"status": RunStatus.CANCELLED}


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
        if run.status == RunStatus.CANCELLED:
            return {"run_id": run.id, **CANCELLED}
        await self._runs.set_status(run.id, RunStatus.RUNNING)
        try:
            async with self._workflow() as workflow:
                outcome = await self._until_cancelled(run.id, self._advance(workflow, run, payload))
        except Exception:
            if await self._cancelled(run.id):  # its sandbox was removed under it: expected
                return {"run_id": run.id, **CANCELLED}
            raise
        if outcome is None or await self._cancelled(run.id):
            return {"run_id": run.id, **CANCELLED}
        status = await self._report(outcome)
        if self._listener and status != RunStatus.WAITING_FOR_APPROVAL:
            # A failure here retries the job; the run is already finished, so only this repeats.
            await self._listener.on_run_finished(run.id, status, outcome.state.get("delivery"))
        return {"run_id": run.id, "status": status}

    async def _advance(
        self, workflow: WorkflowService, run: Run, payload: dict[str, Any]
    ) -> RunOutcome:
        raise NotImplementedError

    async def _until_cancelled(self, run_id: str, work: Any) -> RunOutcome | None:
        """Runs `work`, stopping it as soon as the founder cancels the run (None then)."""
        task: asyncio.Task[RunOutcome] = asyncio.ensure_future(work)
        watch = asyncio.ensure_future(self._watch(run_id))
        done, _ = await asyncio.wait({task, watch}, return_when=asyncio.FIRST_COMPLETED)
        if task in done:
            watch.cancel()
            return task.result()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await task
        return None

    async def _watch(self, run_id: str) -> None:
        while not await self._cancelled(run_id):  # noqa: ASYNC110 (polls the database)
            await asyncio.sleep(CANCEL_POLL_SECONDS)

    async def _cancelled(self, run_id: str) -> bool:
        try:
            return (await self._runs.get(run_id)).status == RunStatus.CANCELLED
        except RunNotFoundError:
            return False

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        """Out of retries: mark the run, tell the log, and remove its sandbox."""
        run_id = str(payload.get("run_id", ""))
        if not run_id or await self._cancelled(run_id):
            return  # a cancelled run stays cancelled; the cancel job tidies up
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
                run.id,
                run.request,
                run.test_command,
                repo=repo,
                new_repo=new_repo,
                stack=run.stack.model_dump(mode="json") if run.stack else None,
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


class CancelBuild:
    """After the founder cancels: remove the run's sandbox, record it, and tell the backlog.
    Safe to repeat."""

    def __init__(
        self,
        workflow: WorkflowFactory,
        sandboxes: SandboxProvider,
        events: EventStore | None = None,
        listener: RunListener | None = None,
    ) -> None:
        self._workflow = workflow
        self._sandboxes = sandboxes
        self._events = events
        self._listener = listener

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        run_id = str(payload.get("run_id", ""))
        if not run_id:
            raise PermanentJobError(f"No run in cancel job: {payload}")
        async with self._workflow() as workflow:
            sandbox_id = (await workflow.get(run_id)).state.get("sandbox_id")
        if sandbox_id:
            await self._sandboxes.destroy(sandbox_id)
        await RunRecorder(self._events, run_id).record(
            Actor.FOUNDER, EventType.RUN_FINISHED, "Cancelled by you", {"status": "cancelled"}
        )
        if self._listener:
            await self._listener.on_run_finished(run_id, RunStatus.CANCELLED)
        return {"run_id": run_id, **CANCELLED}

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        logger.error("Couldn't tidy up cancelled run %s: %s", payload.get("run_id"), error)
