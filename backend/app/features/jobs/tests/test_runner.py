"""The worker loop on the in-memory queue: success, retries, giving up, crashes, shutdown."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from app.features.jobs.exceptions import PermanentJobError
from app.features.jobs.schemas import JobStatus
from app.features.jobs.service import JobRunner
from app.features.jobs.stores.memory_queue import InMemoryJobQueue

T0 = datetime(2026, 10, 1, tzinfo=UTC)


class Handler:
    def __init__(self, fail_times: int = 0, error: Exception | None = None) -> None:
        self.fail_times = fail_times
        self.error = error or RuntimeError("model timed out")
        self.calls = 0
        self.gave_up: list[str] = []

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.error
        return {"echo": payload["n"]}

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        self.gave_up.append(error)


def runner(queue: InMemoryJobQueue, handler: Any, **kwargs: Any) -> JobRunner:
    return JobRunner(queue, {"echo": handler}, "w1", retry_base=timedelta(seconds=30), **kwargs)


async def test_job_runs_and_records_its_result() -> None:
    queue, handler = InMemoryJobQueue(), Handler()
    await queue.enqueue("echo", {"n": 1})

    await runner(queue, handler).run_once()

    job = queue.jobs[0]
    assert (job.status, job.result, job.attempts) == (JobStatus.DONE, {"echo": 1}, 1)


async def test_failures_retry_with_growing_delays_then_give_up() -> None:
    queue, handler = InMemoryJobQueue(), Handler(fail_times=5)
    queue.now = T0
    await queue.enqueue("echo", {"n": 1}, max_attempts=3)
    worker = runner(queue, handler)

    await worker.run_once()
    assert queue.jobs[0].status == JobStatus.QUEUED
    assert queue.jobs[0].run_after == T0 + timedelta(seconds=30)
    assert await worker.run_once() is None  # not due yet

    queue.now = T0 + timedelta(seconds=30)
    await worker.run_once()
    assert queue.jobs[0].run_after == T0 + timedelta(seconds=90)  # 30s after, doubled

    queue.now = T0 + timedelta(seconds=90)
    await worker.run_once()
    job = queue.jobs[0]
    assert (job.status, job.attempts) == (JobStatus.FAILED, 3)
    assert handler.gave_up == ["RuntimeError: model timed out"]


async def test_permanent_errors_fail_at_once() -> None:
    queue = InMemoryJobQueue()
    handler = Handler(fail_times=1, error=PermanentJobError("no such run"))
    await queue.enqueue("echo", {"n": 1})

    await runner(queue, handler).run_once()

    assert queue.jobs[0].status == JobStatus.FAILED
    assert len(handler.gave_up) == 1


async def test_workers_leave_kinds_they_cant_handle() -> None:
    queue = InMemoryJobQueue()
    await queue.enqueue("mystery", {})

    assert await runner(queue, Handler()).run_once() is None
    assert queue.jobs[0].status == JobStatus.QUEUED  # waits for a worker that knows it


async def test_unique_key_queues_once() -> None:
    queue = InMemoryJobQueue()

    first = await queue.enqueue("echo", {"n": 1}, unique_key="standup:2026-10-01")
    second = await queue.enqueue("echo", {"n": 1}, unique_key="standup:2026-10-01")

    assert first is not None and second is None
    assert len(queue.jobs) == 1


async def test_a_dead_workers_job_is_claimed_again_after_its_lease() -> None:
    queue = InMemoryJobQueue()
    queue.now = T0
    await queue.enqueue("echo", {"n": 1})
    lease = timedelta(seconds=60)

    crashed = await queue.claim("w1", lease)  # w1 dies holding it
    assert crashed is not None
    assert await queue.claim("w2", lease) is None  # lease still valid
    queue.now = T0 + timedelta(seconds=61)
    taken_over = await queue.claim("w2", lease)

    assert taken_over is not None
    assert (taken_over.id, taken_over.locked_by, taken_over.attempts) == (crashed.id, "w2", 2)


async def test_stopping_hands_running_jobs_back() -> None:
    queue = InMemoryJobQueue()
    started = asyncio.Event()

    class Slow(Handler):
        async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
            started.set()
            await asyncio.sleep(60)
            return None

    await queue.enqueue("echo", {"n": 1})
    stop = asyncio.Event()
    loop = asyncio.create_task(runner(queue, Slow(), poll_seconds=0.01).run_forever(stop))
    await started.wait()
    stop.set()
    await loop

    job = queue.jobs[0]
    assert (job.status, job.attempts, job.locked_by) == (JobStatus.QUEUED, 0, None)


async def test_losing_the_lease_stops_the_work() -> None:
    queue = InMemoryJobQueue()
    cancelled = asyncio.Event()

    class Slow(Handler):
        async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                cancelled.set()
                raise
            return None

    async def lost(job_id: int, worker_id: str, lease: timedelta) -> bool:
        return False  # another worker took the job over

    queue.extend = lost  # type: ignore[method-assign]
    await queue.enqueue("echo", {"n": 1})

    await runner(queue, Slow(), lease=timedelta(milliseconds=30)).run_once()

    assert cancelled.is_set()
    assert queue.jobs[0].status == JobStatus.RUNNING  # left to the worker that holds it


async def test_periodic_tasks_run_in_the_loop() -> None:
    queue, ticks = InMemoryJobQueue(), []
    stop = asyncio.Event()

    async def tick() -> None:
        ticks.append(1)
        stop.set()

    await runner(queue, Handler(), periodic=[tick], poll_seconds=0.01).run_forever(stop)

    assert ticks == [1]
