"""Starts and resumes build runs. Callers (worker, later the API) never touch LangGraph directly."""

from collections.abc import Callable
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from app.features.events.interfaces import EventStore
from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.workflows.activity import record_step
from app.features.workflows.schemas import RunOutcome, StepUpdate
from app.features.workflows.state import BuildState

OnStep = Callable[[StepUpdate], None]


class WorkflowService:
    def __init__(
        self,
        graph: CompiledStateGraph[BuildState, None, BuildState, BuildState],
        events: EventStore | None = None,
    ) -> None:
        self._graph = graph
        self._events = events

    async def start(
        self,
        run_id: str,
        request: str,
        test_command: str,
        on_step: OnStep | None = None,
        sandbox_id: str | None = None,
    ) -> RunOutcome:
        """Start a run. Pass `sandbox_id` to work in an existing, prepared sandbox."""
        initial: BuildState = {"run_id": run_id, "request": request, "test_command": test_command}
        if sandbox_id:
            initial["sandbox_id"] = sandbox_id
        await self._recorder(run_id).record(
            Actor.FOUNDER,
            EventType.RUN_STARTED,
            f"Asked for: {request[:200]}",
            {"request": request},
        )
        return await self._run(run_id, initial, on_step)

    async def resume(
        self, run_id: str, approved: bool, feedback: str = "", on_step: OnStep | None = None
    ) -> RunOutcome:
        decision: Command[Any] = Command(resume={"approved": approved, "feedback": feedback})
        await self._recorder(run_id).record(
            Actor.FOUNDER,
            EventType.APPROVAL_DECIDED,
            ("Approved the release" if approved else "Did not approve the release")
            + (f": {feedback}" if feedback else ""),
            {"approved": approved, "feedback": feedback},
        )
        return await self._run(run_id, decision, on_step)

    async def continue_run(self, run_id: str, on_step: OnStep | None = None) -> RunOutcome:
        """Carry on from the last checkpoint after a worker stopped mid-run. The interrupted
        step starts again from its beginning, in the same sandbox."""
        await self._recorder(run_id).record(
            Actor.SYSTEM, EventType.RUN_RESUMED, "Picked up again after an interruption"
        )
        return await self._run(run_id, None, on_step)

    async def get(self, run_id: str) -> RunOutcome:
        return await self._outcome(run_id)

    async def _run(self, run_id: str, graph_input: Any, on_step: OnStep | None) -> RunOutcome:
        config: RunnableConfig = {"configurable": {"thread_id": run_id}}
        recorder = self._recorder(run_id)
        async for update in self._graph.astream(graph_input, config, stream_mode="updates"):
            for node, data in update.items():
                if node == "__interrupt__":
                    continue
                await record_step(recorder, node, dict(data or {}))
                if on_step:
                    on_step(StepUpdate(node=node, data=dict(data or {})))
        outcome = await self._outcome(run_id)
        if outcome.waiting_for_approval:
            gate = outcome.gate or {}
            why = " ".join(gate.get("reasons", [])) if gate.get("rules") else ""
            await recorder.record(
                Actor.CTO,
                EventType.APPROVAL_REQUESTED,
                "Waiting for your approval to release" + (f": {why}" if why else ""),
                {"gate": gate},
            )
        return outcome

    def _recorder(self, run_id: str) -> RunRecorder:
        return RunRecorder(self._events, run_id)

    async def _outcome(self, run_id: str) -> RunOutcome:
        snapshot = await self._graph.aget_state({"configurable": {"thread_id": run_id}})
        interrupts = [i for task in snapshot.tasks for i in task.interrupts]
        return RunOutcome(
            run_id=run_id,
            waiting_for_approval=bool(interrupts),
            gate=interrupts[0].value if interrupts else None,
            next_nodes=list(snapshot.next),
            state=dict(snapshot.values),
        )
