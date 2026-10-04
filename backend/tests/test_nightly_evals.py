from datetime import UTC, datetime

from app.core.config import get_settings
from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.workers.handlers.evals import NIGHTLY_EVALS, nightly_evals_schedule

NIGHT = datetime(2026, 10, 4, 21, 0, tzinfo=UTC)  # 02:30 in India
AFTERNOON = datetime(2026, 10, 4, 9, 0, tzinfo=UTC)  # 14:30 in India


async def test_queued_once_per_night_and_engine_inside_the_window() -> None:
    settings = get_settings().model_copy(
        update={"eval_nightly": True, "eval_nightly_engines": ["builtin", "openhands"]}
    )
    queue, now = InMemoryJobQueue(), [AFTERNOON]
    tick = nightly_evals_schedule(queue, settings, clock=lambda: now[0])

    await tick()
    assert queue.jobs == []  # a worker started in the afternoon doesn't start a run
    now[0] = NIGHT
    await tick()
    await tick()

    assert [(j.kind, j.payload["engine"]) for j in queue.jobs] == [
        (NIGHTLY_EVALS, "builtin"),
        (NIGHTLY_EVALS, "openhands"),
    ]
    assert queue.jobs[0].unique_key == "evals.nightly:2026-10-05:builtin"


async def test_off_unless_switched_on() -> None:
    settings = get_settings().model_copy(update={"eval_nightly": False})
    queue = InMemoryJobQueue()

    await nightly_evals_schedule(queue, settings, clock=lambda: NIGHT)()

    assert queue.jobs == []
