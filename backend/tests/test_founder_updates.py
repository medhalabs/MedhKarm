"""The morning standup and the Monday report reach each founder: their own runs only, on
their channels, once a day."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.jobs.service import JobRunner
from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.features.notifications.memory_repository import InMemorySettingsRepository
from app.features.notifications.schemas import Channel, NotificationSettings
from app.features.notifications.service import NotificationService
from app.features.runs.memory_repository import InMemoryRunRepository
from app.features.runs.schemas import RunStatus, StartRun
from app.features.runs.service import RunService
from app.features.standups.schemas import Standup
from app.features.standups.service import StandupService
from app.workers.handlers.standup import (
    SEND_STANDUP,
    SendStandup,
    SendWeekly,
    standup_schedule,
)


class Inbox:
    def __init__(self, channel: Channel) -> None:
        self.channel = channel
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, text: str) -> None:
        self.sent.append((to, subject, text))


class Log:
    async def send(self, standup: Standup, text: str) -> str:
        return "log"


async def test_each_founder_gets_their_own_standup_and_weekly_report() -> None:
    events, queue = InMemoryEventStore(), InMemoryJobQueue()
    # Noon today: inside the window that ends at 23:00, whatever time the test runs
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    events.now = datetime.combine(today, time(12), ZoneInfo("Asia/Kolkata"))
    runs = RunService(InMemoryRunRepository(), queue)
    mine = await runs.start(StartRun(request="Build the chai stall orders library"), "c1")
    theirs = await runs.start(StartRun(request="Someone else's secret project"), "c2")
    for run in (mine, theirs):
        recorder = RunRecorder(events, run.id)
        await recorder.record(Actor.FOUNDER, EventType.RUN_STARTED, "Asked for it")
        await recorder.record(
            Actor.SYSTEM, EventType.RUN_FINISHED, "Released", {"status": "released"}, tokens=1200
        )
        await runs.set_status(run.id, RunStatus.RELEASED)
    email, whatsapp = Inbox(Channel.EMAIL), Inbox(Channel.WHATSAPP)
    settings = InMemorySettingsRepository()
    await settings.save(
        "c1", NotificationSettings(email="me@x.in", whatsapp="+919876543210", standup_hour=0)
    )
    notifications = NotificationService(settings, [email, whatsapp])
    standups = StandupService(events, hour=0)
    worker = JobRunner(
        queue,
        {SEND_STANDUP: SendStandup(standups, Log(), notifications, runs, "https://app.in")},
        "w1",
    )
    tick = standup_schedule(queue, standups, notifications)

    await tick()
    await tick()  # once a day, however often the worker ticks
    # The content covers the 24 hours up to the founder's hour: a late hour covers just now
    await settings.save(
        "c1", NotificationSettings(email="me@x.in", whatsapp="+919876543210", standup_hour=23)
    )
    while await worker.run_once():
        pass

    assert [j.kind for j in queue.jobs].count(SEND_STANDUP) == 1
    [(to, subject, standup_mail)] = email.sent
    assert to == "me@x.in" and subject.startswith("Standup")
    assert "1,200 tokens" in standup_mail  # this company's run only (both would be 2,400)
    assert "secret project" not in standup_mail
    assert "https://app.in/admin/inbox" in standup_mail
    assert "\n" not in whatsapp.sent[0][2]  # one line for WhatsApp

    next_monday = (standups.today() + timedelta(days=7)).isoformat()
    weekly = SendWeekly(notifications, runs, events, "Asia/Kolkata", "https://app.in")
    await weekly.run({"company_id": "c1", "day": next_monday})

    assert email.sent[-1][1].startswith("Your week")
    assert "1 released" in whatsapp.sent[-1][2]
    assert "secret project" not in email.sent[-1][2]
