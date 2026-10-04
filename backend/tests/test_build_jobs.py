"""Build runs through the job queue, end to end in memory: the API queues, a worker runs the
graph, the founder approves over the API, a worker resumes. Also: a worker crash mid-run,
giving up, and the morning standup schedule."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.schemas import EventType
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.jobs.interfaces import JobHandler
from app.features.jobs.schemas import JobStatus
from app.features.jobs.service import JobRunner
from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, Message, ToolCall, ToolSpec
from app.features.runs.exceptions import RunAlreadyFinishedError, RunNotWaitingError
from app.features.runs.memory_repository import InMemoryRunRepository
from app.features.runs.schemas import ApprovalDecision, RunStatus, StartRun
from app.features.runs.service import CANCEL_JOB, RESUME_JOB, START_JOB, RunService
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.standups.schemas import Standup
from app.features.standups.service import StandupService
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService
from app.workers.handlers.build import CancelBuild, ResumeBuild, StartBuild
from app.workers.handlers.standup import SEND_STANDUP, SendStandup, standup_schedule


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


SCRIPT = [
    tool("submit_plan", summary="Plan", developers=1, tasks=[{"title": "Write a.py"}]),
    tool("write_file", path="a.py", content="1"),
    tool("finish", summary="done"),
    tool("submit_review", decision="approve", feedback=""),
]


class FlakyLLM(ScriptedLLMProvider):
    """Raises on chosen calls, like Ollama failing after LiteLLM's own retries."""

    def __init__(self, responses: list[LLMResponse], fail_on: set[int]) -> None:
        super().__init__(responses)
        self.fail_on = fail_on
        self.attempts = 0

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> LLMResponse:
        self.attempts += 1
        if self.attempts in self.fail_on:
            raise RuntimeError("Ollama Cloud returned 500")
        return await super().complete(messages, tools)


class Office:
    """API side and worker side, sharing in-memory storage."""

    def __init__(
        self, llm: ScriptedLLMProvider, max_attempts: int = 3, listener: Any = None
    ) -> None:
        self.queue = InMemoryJobQueue()
        self.events = InMemoryEventStore()
        self.repo = InMemoryRunRepository()
        self.runs = RunService(self.repo, self.queue, max_attempts)
        self.sandboxes = InMemorySandboxProvider(
            lambda command, files: CommandResult(exit_code=0, output="ok")
        )
        graph = build_app_graph(
            llm, ToolLoopEngine(llm), self.sandboxes, InMemorySaver(), events=self.events
        )
        self.workflow_service = WorkflowService(graph, self.events)

        @asynccontextmanager
        async def workflow() -> AsyncIterator[WorkflowService]:
            yield self.workflow_service

        handlers: dict[str, JobHandler] = {
            START_JOB: StartBuild(self.runs, workflow, self.sandboxes, self.events, listener),
            RESUME_JOB: ResumeBuild(self.runs, workflow, self.sandboxes, self.events, listener),
            CANCEL_JOB: CancelBuild(workflow, self.sandboxes, self.events, listener),
        }
        self.worker = JobRunner(self.queue, handlers, "w1", retry_base=timedelta(0))

    def types(self) -> list[EventType]:
        return [e.type for e in self.events.events]


async def test_start_over_the_api_then_approve() -> None:
    office = Office(ScriptedLLMProvider(list(SCRIPT)))

    run = await office.runs.start(StartRun(request="Build a.py", test_command="pytest"))
    await office.worker.run_once()

    waiting = await office.runs.get(run.id)
    assert waiting.status == RunStatus.WAITING_FOR_APPROVAL
    assert waiting.gate is not None

    await office.runs.decide(run.id, ApprovalDecision(approved=True))
    await office.worker.run_once()

    assert (await office.runs.get(run.id)).status == RunStatus.RELEASED
    assert [j.status for j in office.queue.jobs] == [JobStatus.DONE, JobStatus.DONE]
    assert office.types()[-1] == EventType.RUN_FINISHED


async def test_a_failed_attempt_continues_from_the_checkpoint() -> None:
    llm = FlakyLLM(list(SCRIPT), fail_on={2})  # the developer's first model call fails
    office = Office(llm)
    run = await office.runs.start(StartRun(request="Build a.py", test_command="pytest"))

    await office.worker.run_once()  # plan done and saved, then the error
    assert office.queue.jobs[0].status == JobStatus.QUEUED  # queued to retry
    await office.worker.run_once()

    assert (await office.runs.get(run.id)).status == RunStatus.WAITING_FOR_APPROVAL
    types = office.types()
    assert types.count(EventType.RUN_STARTED) == 1
    assert types.count(EventType.PLAN_CREATED) == 1  # the CTO didn't plan twice
    assert types.count(EventType.RUN_RESUMED) == 1


async def test_giving_up_marks_the_run_and_removes_the_sandbox() -> None:
    llm = FlakyLLM(list(SCRIPT), fail_on={2, 3})
    office = Office(llm, max_attempts=2)
    run = await office.runs.start(StartRun(request="Build a.py", test_command="pytest"))

    await office.worker.run_once()
    await office.worker.run_once()

    failed = await office.runs.get(run.id)
    assert failed.status == RunStatus.ERROR
    assert "Ollama Cloud returned 500" in (failed.error or "")
    assert office.events.events[-1].data["status"] == "error"
    sandbox_id = (await office.workflow_service.get(run.id)).state["sandbox_id"]
    assert sandbox_id not in office.sandboxes.sandboxes
    assert office.sandboxes.sandboxes == {}  # retries re-attached; nothing leaked


async def test_standup_is_queued_once_a_day_after_the_hour() -> None:
    queue, sent = InMemoryJobQueue(), []
    now = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)  # 08:30 in India

    class Delivery:
        async def send(self, standup: Standup, text: str) -> str:
            sent.append(text)
            return "log"

    standups = StandupService(InMemoryEventStore(), clock=lambda: now)
    tick = standup_schedule(queue, standups)
    worker = JobRunner(queue, {SEND_STANDUP: SendStandup(standups, Delivery())}, "w1")

    await tick()
    assert queue.jobs == []  # before 09:00
    now += timedelta(hours=1)
    await tick()
    await tick()
    await worker.run_once()

    [job] = queue.jobs
    assert (job.unique_key, job.status) == ("standup.send:2026-10-01", JobStatus.DONE)
    assert job.result is not None and job.result["sent_to"] == "log"
    assert sent[0].startswith("Standup for Thu 01 Oct 2026")


class Listener:
    def __init__(self) -> None:
        self.calls: list[tuple[str, RunStatus]] = []

    async def on_run_finished(
        self, run_id: str, status: RunStatus, delivery: dict[str, Any] | None = None
    ) -> None:
        self.calls.append((run_id, status))


async def test_the_listener_hears_finished_runs_not_paused_ones() -> None:
    listener = Listener()
    office = Office(ScriptedLLMProvider(list(SCRIPT)), listener=listener)
    run = await office.runs.start(StartRun(request="Build a.py", test_command="pytest"))

    await office.worker.run_once()  # paused at the gate: not finished
    assert listener.calls == []
    await office.runs.decide(run.id, ApprovalDecision(approved=False))
    await office.worker.run_once()

    assert listener.calls == [(run.id, RunStatus.REJECTED)]


async def test_the_listener_hears_runs_that_give_up() -> None:
    listener = Listener()
    office = Office(FlakyLLM(list(SCRIPT), fail_on={2}), max_attempts=1, listener=listener)
    run = await office.runs.start(StartRun(request="Build a.py", test_command="pytest"))

    await office.worker.run_once()

    assert listener.calls == [(run.id, RunStatus.ERROR)]


async def test_cancel_at_the_gate_removes_the_sandbox() -> None:
    office = Office(ScriptedLLMProvider(list(SCRIPT)))
    run = await office.runs.start(StartRun(request="Build a.py", test_command="pytest"))
    await office.worker.run_once()
    assert len(office.sandboxes.sandboxes) == 1  # kept while waiting

    cancelled = await office.runs.cancel(run.id)
    await office.worker.run_once()  # the cancel job

    assert cancelled.status == RunStatus.CANCELLED
    assert office.sandboxes.sandboxes == {}
    assert office.events.events[-1].summary == "Cancelled by you"
    with pytest.raises(RunNotWaitingError):  # nothing left to approve
        await office.runs.decide(run.id, ApprovalDecision(approved=True))
    with pytest.raises(RunAlreadyFinishedError):
        await office.runs.cancel(run.id)


async def test_a_run_cancelled_before_a_worker_picks_it_up_never_starts() -> None:
    office = Office(ScriptedLLMProvider([]))  # any model call would fail the test
    run = await office.runs.start(StartRun(request="Build a.py", test_command="pytest"))

    await office.runs.cancel(run.id)
    await office.worker.run_once()  # the start job: skipped
    await office.worker.run_once()  # the cancel job

    assert (await office.runs.get(run.id)).status == RunStatus.CANCELLED
    assert EventType.PLAN_CREATED not in office.types()
    assert [j.status for j in office.queue.jobs] == [JobStatus.DONE, JobStatus.DONE]


class StuckLLM(ScriptedLLMProvider):
    """Never answers: like a long model call the founder gets tired of."""

    def __init__(self) -> None:
        super().__init__([])
        self.called = asyncio.Event()

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> LLMResponse:
        self.called.set()
        await asyncio.Event().wait()
        raise AssertionError("unreachable")


async def test_cancel_stops_a_run_in_the_middle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.workers.handlers.build.CANCEL_POLL_SECONDS", 0.01)
    llm = StuckLLM()
    office = Office(llm)
    run = await office.runs.start(StartRun(request="Build a.py", test_command="pytest"))

    working = asyncio.create_task(office.worker.run_once())
    await asyncio.wait_for(llm.called.wait(), 5)  # the CTO is thinking
    await office.runs.cancel(run.id)
    await asyncio.wait_for(working, 5)  # the worker let go

    assert (await office.runs.get(run.id)).status == RunStatus.CANCELLED
    assert office.queue.jobs[0].status == JobStatus.DONE
