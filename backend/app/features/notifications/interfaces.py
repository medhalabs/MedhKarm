from typing import Protocol

from app.features.notifications.schemas import Channel, CompanySettings, NotificationSettings


class Notifier(Protocol):
    """One channel's provider (Resend, SMTP, Meta WhatsApp). Raises NotificationError."""

    channel: Channel

    async def send(self, to: str, subject: str, text: str) -> None: ...


class SettingsRepository(Protocol):
    async def get(self, company_id: str) -> CompanySettings | None: ...

    async def save(self, company_id: str, settings: NotificationSettings) -> CompanySettings: ...

    async def all(self) -> list[CompanySettings]: ...
