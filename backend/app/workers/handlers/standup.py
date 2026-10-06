"""The morning standup and the Monday report as jobs. Every tick the worker queues one per
company that's due (its own hour, in STANDUP_TIMEZONE); the unique key means once per day (or
week), however many workers run. Each goes to the founder's email and WhatsApp (notifications)
and to the worker's log."""

from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any, Protocol

from app.features.jobs.interfaces import JobQueue
from app.features.notifications.exceptions import NotificationError
from app.features.notifications.schemas import Delivery, Update
from app.features.notifications.service import NotificationService
from app.features.standups.interfaces import ActivityLog, RunLister, StandupDelivery
from app.features.standups.render import to_short, to_text
from app.features.standups.service import StandupService
from app.features.standups.weekly import build_weekly, weekly_short, weekly_text

SEND_STANDUP = "standup.send"
SEND_WEEKLY = "report.weekly"


class CompanyRuns(RunLister, Protocol):
    async def run_ids(self, company_id: str) -> set[str]: ...


def _check(results: list[Delivery]) -> None:
    """Retry the job when every channel failed (a provider outage), not when one did."""
    if results and not any(r.ok for r in results):
        raise NotificationError("; ".join(f"{r.channel}: {r.error}" for r in results))


class SendStandup:
    def __init__(
        self,
        standups: StandupService,
        delivery: StandupDelivery,
        notifications: NotificationService | None = None,
        runs: CompanyRuns | None = None,
        app_url: str = "",
        manager: str = "",
    ) -> None:
        self._standups = standups
        self._manager = manager  # who speaks: Priya, the office manager
        self._delivery = delivery
        self._notifications = notifications
        self._runs = runs
        self._link = f"{app_url}/admin/inbox" if app_url else ""

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        day = date.fromisoformat(payload["day"])
        company = payload.get("company_id")
        if not (company and self._notifications and self._runs):  # every run, to the log
            standup = await self._standups.for_day(day)
            sent_to = await self._delivery.send(standup, to_text(standup))
            return {"day": payload["day"], "headline": standup.headline, "sent_to": sent_to}
        settings = await self._notifications.get(company)
        standup = await self._standups.for_day(
            day, await self._runs.run_ids(company), settings.standup_hour
        )
        text = to_text(standup, self._manager)
        results = await self._notifications.deliver(
            company,
            Update(
                subject=f"Standup {day:%d %b}: {standup.headline}",
                text=text + (f"\n\nOpen your inbox: {self._link}" if self._link else ""),
                short=to_short(standup, self._link, self._manager),
            ),
        )
        await self._delivery.send(standup, text)
        _check(results)
        return {
            "day": payload["day"],
            "company_id": company,
            "sent": [r.model_dump(mode="json") for r in results],
        }

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        return None


class SendWeekly:
    def __init__(
        self,
        notifications: NotificationService,
        runs: CompanyRuns,
        log: ActivityLog,
        timezone: str,
        app_url: str = "",
    ) -> None:
        self._notifications = notifications
        self._runs = runs
        self._log = log
        self._timezone = timezone
        self._link = f"{app_url}/admin/inbox" if app_url else ""

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        company, day = str(payload["company_id"]), date.fromisoformat(payload["day"])
        report = await build_weekly(self._runs, self._log, company, day, self._timezone)
        results = await self._notifications.deliver(
            company,
            Update(
                subject=f"Your week with MedhKarm, up to {day:%d %b}",
                text=weekly_text(report, self._link),
                short=weekly_short(report, self._link),
            ),
        )
        _check(results)
        return {
            "day": payload["day"],
            "company_id": company,
            "sent": [r.model_dump(mode="json") for r in results],
        }

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        return None


def standup_schedule(
    queue: JobQueue,
    standups: StandupService,
    notifications: NotificationService | None = None,
) -> Callable[[], Awaitable[None]]:
    async def queue_due() -> None:
        if notifications is None:  # no founders' settings: one standup of everything, logged
            day = standups.due_day()
            if day:
                await queue.enqueue(
                    SEND_STANDUP, {"day": day.isoformat()}, unique_key=f"{SEND_STANDUP}:{day}"
                )
            return
        now = standups.now()
        for company, day in await notifications.due_standups(now):
            await queue.enqueue(
                SEND_STANDUP,
                {"company_id": company, "day": day.isoformat()},
                unique_key=f"{SEND_STANDUP}:{company}:{day}",
            )
        for company, day in await notifications.due_weekly(now):
            await queue.enqueue(
                SEND_WEEKLY,
                {"company_id": company, "day": day.isoformat()},
                unique_key=f"{SEND_WEEKLY}:{company}:{day}",
            )

    return queue_due
