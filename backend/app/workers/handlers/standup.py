"""The morning standup as a job: the worker queues one per day, once it's past the standup
hour, and the handler builds and sends it. The unique key means one per day, however many
workers are running or restarted."""

from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any

from app.features.jobs.interfaces import JobQueue
from app.features.standups.interfaces import StandupDelivery
from app.features.standups.render import to_text
from app.features.standups.service import StandupService

SEND_STANDUP = "standup.send"


class SendStandup:
    def __init__(self, standups: StandupService, delivery: StandupDelivery) -> None:
        self._standups = standups
        self._delivery = delivery

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        standup = await self._standups.for_day(date.fromisoformat(payload["day"]))
        text = to_text(standup)
        sent_to = await self._delivery.send(standup, text)
        return {"day": payload["day"], "headline": standup.headline, "sent_to": sent_to}

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        return None


def standup_schedule(queue: JobQueue, standups: StandupService) -> Callable[[], Awaitable[None]]:
    async def queue_todays_standup() -> None:
        day = standups.due_day()
        if day:
            await queue.enqueue(
                SEND_STANDUP, {"day": day.isoformat()}, unique_key=f"{SEND_STANDUP}:{day}"
            )

    return queue_todays_standup
