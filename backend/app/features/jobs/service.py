"""The worker loop: claims jobs, runs their handlers, keeps leases alive, retries failures.

A worker that dies leaves its job `running` with a lease that runs out; any worker then claims
it again. A worker that is stopped (Ctrl+C, deploy) hands its jobs straight back.
"""

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta

from app.features.jobs.exceptions import PermanentJobError
from app.features.jobs.interfaces import JobHandler, JobQueue
from app.features.jobs.schemas import Job

logger = logging.getLogger(__name__)

Periodic = Callable[[], Awaitable[None]]


class JobRunner:
    def __init__(
        self,
        queue: JobQueue,
        handlers: dict[str, JobHandler],
        worker_id: str,
        lease: timedelta = timedelta(seconds=60),
        retry_base: timedelta = timedelta(seconds=30),
        concurrency: int = 2,
        poll_seconds: float = 2.0,
        periodic: list[Periodic] | None = None,
        periodic_seconds: float = 60.0,
    ) -> None:
        self._queue = queue
        self._handlers = handlers
        self._kinds = list(handlers)  # only claim what this worker can do
        self.worker_id = worker_id
        self._lease = lease
        self._retry_base = retry_base
        self._concurrency = max(1, concurrency)
        self._poll = poll_seconds
        self._periodic = periodic or []
        self._periodic_seconds = periodic_seconds

    async def run_once(self) -> Job | None:
        """Claim one due job and run it to the end. None when nothing was due."""
        job = await self._queue.claim(self.worker_id, self._lease, self._kinds)
        if job:
            await self.process(job)
        return job

    async def run_forever(self, stop: asyncio.Event) -> None:
        active: set[asyncio.Task[None]] = set()
        loop = asyncio.get_running_loop()
        next_periodic = 0.0
        try:
            while not stop.is_set():
                if loop.time() >= next_periodic:
                    await self._run_periodic()
                    next_periodic = loop.time() + self._periodic_seconds
                while len(active) < self._concurrency:
                    job = await self._queue.claim(self.worker_id, self._lease, self._kinds)
                    if not job:
                        break
                    task = asyncio.create_task(self.process(job))
                    active.add(task)
                    task.add_done_callback(active.discard)
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), self._poll)
        finally:
            for task in active:
                task.cancel()
            await asyncio.gather(*active, return_exceptions=True)

    async def process(self, job: Job) -> None:
        handler = self._handlers.get(job.kind)
        if handler is None:
            await self._queue.fail(job.id, f"No handler for job kind {job.kind!r}", None)
            return
        if job.attempts > job.max_attempts:
            await self._give_up(job, handler, job.last_error or "Out of attempts")
            return

        logger.info("Job %s (%s) attempt %s started", job.id, job.kind, job.attempts)
        work = asyncio.create_task(handler.run(job.payload))
        lost_lease = asyncio.Event()
        heartbeat = asyncio.create_task(self._keep_lease(job, work, lost_lease))
        try:
            result = await work
        except asyncio.CancelledError:
            if lost_lease.is_set():
                logger.warning("Job %s lost its lease; another worker has it", job.id)
                return
            work.cancel()
            await self._queue.release(job.id)  # stopping: hand it back, attempt not counted
            raise
        except PermanentJobError as error:
            await self._give_up(job, handler, _describe(error))
            return
        except Exception as error:
            logger.exception("Job %s (%s) attempt %s failed", job.id, job.kind, job.attempts)
            if job.attempts >= job.max_attempts:
                await self._give_up(job, handler, _describe(error))
            else:
                delay = self._retry_base * 2 ** (job.attempts - 1)
                await self._queue.fail(job.id, _describe(error), delay)
            return
        finally:
            heartbeat.cancel()
        await self._queue.complete(job.id, result)
        logger.info("Job %s (%s) done", job.id, job.kind)

    async def _keep_lease(
        self, job: Job, work: asyncio.Task[object], lost_lease: asyncio.Event
    ) -> None:
        while True:
            await asyncio.sleep(self._lease.total_seconds() / 3)
            if not await self._queue.extend(job.id, self.worker_id, self._lease):
                lost_lease.set()
                work.cancel()
                return

    async def _give_up(self, job: Job, handler: JobHandler, error: str) -> None:
        await self._queue.fail(job.id, error, None)
        try:
            await handler.give_up(job.payload, error)
        except Exception:
            logger.exception("give_up failed for job %s", job.id)

    async def _run_periodic(self) -> None:
        for task in self._periodic:
            try:
                await task()
            except Exception:
                logger.exception("Periodic task failed")


def _describe(error: BaseException) -> str:
    return f"{type(error).__name__}: {error}"[:2000]
