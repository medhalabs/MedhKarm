"""The nightly eval suite as a job: the worker queues one per engine per night (between
EVAL_NIGHTLY_HOUR and four hours later, India time), and the handler runs the whole suite and
saves the report with cost and time per task. The unique key means once per night, however
many workers run; a worker started in the afternoon doesn't start a surprise run."""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.core.config import Settings
from app.features.jobs.interfaces import JobQueue
from app.workers.run_evals import BACKEND_DIR, run_suite

NIGHTLY_EVALS = "evals.nightly"
WINDOW_HOURS = 4


class NightlyEvals:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        settings = self._settings.model_copy(update={"developer_engine": payload["engine"]})
        report, path, _ = await run_suite(settings, None, self._settings.eval_nightly_parallel)
        return {
            "engine": report.engine,
            "model": report.model,
            "passed": report.passed,
            "scored": len(report.scored),
            "errored": len(report.errored),
            "report": str(path.relative_to(BACKEND_DIR)),
        }

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        return None


def nightly_evals_schedule(
    queue: JobQueue,
    settings: Settings,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Callable[[], Awaitable[None]]:
    zone = ZoneInfo(settings.standup_timezone)

    async def queue_tonights_evals() -> None:
        now = clock().astimezone(zone)
        if not settings.eval_nightly:
            return
        if not settings.eval_nightly_hour <= now.hour < settings.eval_nightly_hour + WINDOW_HOURS:
            return
        for engine in settings.eval_nightly_engines:
            await queue.enqueue(
                NIGHTLY_EVALS,
                {"engine": engine, "night": now.date().isoformat()},
                unique_key=f"{NIGHTLY_EVALS}:{now.date()}:{engine}",
                max_attempts=1,
            )

    return queue_tonights_evals
