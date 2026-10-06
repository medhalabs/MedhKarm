"""Priya's nudge as a job. Every tick the worker queues one per company that wants them and is
awake (once a day, by its unique key); the job looks at that company's inbox and only writes if
something has waited a day (features/inbox/nudge.py). Each goes to the founder's email and
WhatsApp, like the standup."""

from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from typing import Any

from app.features.inbox.nudge import nudge
from app.features.inbox.schemas import Inbox
from app.features.jobs.interfaces import JobQueue
from app.features.notifications.service import NotificationService
from app.features.standups.service import StandupService
from app.workers.handlers.standup import _check

NUDGE = "priya.nudge"
InboxOf = Callable[[str], Awaitable[Inbox]]


class SendNudge:
    def __init__(
        self,
        inbox: InboxOf,
        notifications: NotificationService,
        app_url: str = "",
        manager: str = "Priya",
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._inbox = inbox
        self._notifications = notifications
        self._link = f"{app_url}/admin/inbox" if app_url else ""
        self._manager = manager
        self._clock = clock

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        company = str(payload["company_id"])
        update = nudge(await self._inbox(company), self._clock(), self._link, self._manager)
        if update is None:  # nothing has waited a day: she stays quiet
            return {"company_id": company, "sent": []}
        results = await self._notifications.deliver(company, update)
        _check(results)
        return {"company_id": company, "sent": [r.model_dump(mode="json") for r in results]}

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        return None


def nudge_schedule(
    queue: JobQueue, standups: StandupService, notifications: NotificationService
) -> Callable[[], Awaitable[None]]:
    async def queue_due() -> None:
        day: date
        for company, day in await notifications.due_nudges(standups.now()):
            await queue.enqueue(
                NUDGE,
                {"company_id": company, "day": day.isoformat()},
                unique_key=f"{NUDGE}:{company}:{day}",
            )

    return queue_due
