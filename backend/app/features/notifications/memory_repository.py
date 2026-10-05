"""SettingsRepository in memory, for tests."""

from datetime import UTC, datetime

from app.features.notifications.schemas import CompanySettings, NotificationSettings


class InMemorySettingsRepository:
    def __init__(self) -> None:
        self.settings: dict[str, CompanySettings] = {}

    async def get(self, company_id: str) -> CompanySettings | None:
        return self.settings.get(company_id)

    async def save(self, company_id: str, settings: NotificationSettings) -> CompanySettings:
        saved = CompanySettings(
            company_id=company_id, updated_at=datetime.now(UTC), **settings.model_dump()
        )
        self.settings[company_id] = saved
        return saved

    async def all(self) -> list[CompanySettings]:
        return list(self.settings.values())
