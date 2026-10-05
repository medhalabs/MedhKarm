"""Sending updates to a founder on the channels they chose, and working out which companies'
standups and weekly reports are due. Updates are opt-in: nothing goes out until the founder
saves their settings."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.features.notifications.exceptions import NotificationError
from app.features.notifications.interfaces import Notifier, SettingsRepository
from app.features.notifications.schemas import (
    Channel,
    CompanySettings,
    Delivery,
    NotificationSettings,
    Update,
)

TEST = Update(
    subject="MedhKarm: test message",
    text="This is a test from MedhKarm. Your daily standup and weekly report will arrive here.",
    short="This is a test from MedhKarm. Your daily standup and weekly report will arrive here.",
)
MONDAY = 0


class NotificationService:
    def __init__(
        self,
        settings: SettingsRepository,
        notifiers: list[Notifier] | None = None,
        timezone: str = "Asia/Kolkata",
    ) -> None:
        self._settings = settings
        self._notifiers = {n.channel: n for n in notifiers or []}
        self._zone = ZoneInfo(timezone)

    def channels(self) -> list[Channel]:
        """The channels this server can send on (their keys are set)."""
        return list(self._notifiers)

    async def get(self, company_id: str) -> CompanySettings:
        return await self._settings.get(company_id) or CompanySettings(company_id=company_id)

    async def save(self, company_id: str, settings: NotificationSettings) -> CompanySettings:
        return await self._settings.save(company_id, settings)

    async def deliver(self, company_id: str, update: Update) -> list[Delivery]:
        """Sends to every channel the founder set up; one failing doesn't stop the other."""
        settings = await self.get(company_id)
        targets = [
            (Channel.EMAIL, settings.email, update.text),
            (Channel.WHATSAPP, settings.whatsapp, update.short),
        ]
        results: list[Delivery] = []
        for channel, to, body in targets:
            if not to:
                continue
            notifier = self._notifiers.get(channel)
            if notifier is None:
                results.append(
                    Delivery(
                        channel=channel,
                        to=to,
                        ok=False,
                        error=f"{channel} isn't set up on the server",
                    )
                )
                continue
            try:
                await notifier.send(to, update.subject, body)
                results.append(Delivery(channel=channel, to=to, ok=True))
            except NotificationError as error:
                results.append(Delivery(channel=channel, to=to, ok=False, error=error.message))
        return results

    async def send_test(self, company_id: str) -> list[Delivery]:
        return await self.deliver(company_id, TEST)

    async def due_standups(self, now: datetime) -> list[tuple[str, date]]:
        """(company, day) for every company whose standup hour has passed today."""
        local = now.astimezone(self._zone)
        return [
            (s.company_id, local.date())
            for s in await self._settings.all()
            if s.standup_on and (s.email or s.whatsapp) and local.hour >= s.standup_hour
        ]

    async def due_weekly(self, now: datetime) -> list[tuple[str, date]]:
        """(company, Monday) on Mondays past each company's standup hour."""
        local = now.astimezone(self._zone)
        if local.weekday() != MONDAY:
            return []
        return [
            (s.company_id, local.date())
            for s in await self._settings.all()
            if s.weekly_on and (s.email or s.whatsapp) and local.hour >= s.standup_hour
        ]
