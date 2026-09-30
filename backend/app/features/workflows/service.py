"""Starts and resumes build runs. Callers (worker, later the API) never touch LangGraph directly."""

from collections.abc import Callable
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from app.features.workflows.schemas import RunOutcome, StepUpdate
from app.features.workflows.state import BuildState

OnStep = Callable[[StepUpdate], None]


class WorkflowService:
    def __init__(self, graph: CompiledStateGraph[BuildState, None, BuildState, BuildState]) -> None:
        self._graph = graph

    async def start(
        self, run_id: str, request: str, test_command: str, on_step: OnStep | None = None
    ) -> RunOutcome:
        initial: BuildState = {"request": request, "test_command": test_command}
        return await self._run(run_id, initial, on_step)

    async def resume(
        self, run_id: str, approved: bool, feedback: str = "", on_step: OnStep | None = None
    ) -> RunOutcome:
        decision: Command[Any] = Command(resume={"approved": approved, "feedback": feedback})
        return await self._run(run_id, decision, on_step)

    async def get(self, run_id: str) -> RunOutcome:
        return await self._outcome(run_id)

    async def _run(self, run_id: str, graph_input: Any, on_step: OnStep | None) -> RunOutcome:
        config: RunnableConfig = {"configurable": {"thread_id": run_id}}
        async for update in self._graph.astream(graph_input, config, stream_mode="updates"):
            for node, data in update.items():
                if on_step and node != "__interrupt__":
                    on_step(StepUpdate(node=node, data=dict(data or {})))
        return await self._outcome(run_id)

    async def _outcome(self, run_id: str) -> RunOutcome:
        snapshot = await self._graph.aget_state({"configurable": {"thread_id": run_id}})
        interrupts = [i for task in snapshot.tasks for i in task.interrupts]
        return RunOutcome(
            run_id=run_id,
            waiting_for_approval=bool(interrupts),
            gate=interrupts[0].value if interrupts else None,
            state=dict(snapshot.values),
        )
