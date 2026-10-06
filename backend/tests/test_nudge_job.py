"""Priya's nudge job: queued once a day for those who want it, silent unless something waited."""

from datetime import UTC, datetime, timedelta

from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.inbox.schemas import Approval, Inbox
from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.features.notifications.memory_repository import InMemorySettingsRepository
from app.features.notifications.schemas import Channel, NotificationSettings
from app.features.notifications.service import NotificationService
from app.features.standups.service import StandupService
from app.workers.handlers.nudge import NUDGE, SendNudge, nudge_schedule

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)  # 17:30 in Asia/Kolkata


class WaitingInbox:
    def __init__(self, hours: float | None) -> None:
        self.hours = hours

    async def __call__(self, company: str) -> Inbox:
        if self.hours is None:
            return Inbox()
        return Inbox(
            approvals=[
                Approval(
                    run_id="r",
                    request="Chai stall",
                    waiting_since=NOW - timedelta(hours=self.hours),
                )
            ]
        )


class Sink:
    channel = Channel.EMAIL

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, text: str) -> None:
        self.sent.append((to, subject, text))


async def setup(**settings: object) -> tuple[NotificationService, Sink]:
    repo, sink = InMemorySettingsRepository(), Sink()
    await repo.save("c1", NotificationSettings(email="me@x.in", **settings))  # type: ignore[arg-type]
    return NotificationService(repo, [sink]), sink


async def test_priya_writes_when_something_has_waited_a_day() -> None:
    notifications, sink = await setup()
    job = SendNudge(WaitingInbox(30), notifications, "https://app.in", "Priya", clock=lambda: NOW)

    result = await job.run({"company_id": "c1", "day": "2026-10-07"})

    assert [s["ok"] for s in result["sent"]] == [True]  # type: ignore[index]
    [(to, subject, text)] = sink.sent
    assert to == "me@x.in" and subject == "Priya: 1 thing is waiting for you"
    assert "https://app.in/admin/inbox" in text


async def test_she_stays_quiet_when_nothing_has_waited() -> None:
    notifications, sink = await setup()
    for hours in (None, 5):
        job = SendNudge(WaitingInbox(hours), notifications, "", "Priya", clock=lambda: NOW)
        assert (await job.run({"company_id": "c1", "day": "2026-10-07"}))["sent"] == []
    assert sink.sent == []


async def test_one_nudge_a_day_for_those_who_want_them_in_waking_hours() -> None:
    queue = InMemoryJobQueue()
    standups = StandupService(InMemoryEventStore(), hour=9, clock=lambda: NOW)
    wants, _ = await setup(nudge_on=True, standup_hour=9)
    tick = nudge_schedule(queue, standups, wants)
    await tick()
    await tick()  # however often the worker ticks
    assert [j.kind for j in queue.jobs] == [NUDGE]

    declined, _ = await setup(nudge_on=False)
    other = InMemoryJobQueue()
    await nudge_schedule(other, standups, declined)()
    assert other.jobs == []  # switched off

    late = StandupService(InMemoryEventStore(), hour=9, clock=lambda: NOW + timedelta(hours=4))
    night = InMemoryJobQueue()
    await nudge_schedule(night, late, wants)()  # 21:30 local: she doesn't write at night
    assert night.jobs == []
