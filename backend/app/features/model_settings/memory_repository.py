"""ModelSettingsRepository in memory, for tests."""

from app.features.model_settings.schemas import ModelChoices, Provider, StoredModels


class InMemoryModelSettingsRepository:
    def __init__(self) -> None:
        self.rows: dict[str, StoredModels] = {}

    async def get(self, company_id: str) -> StoredModels | None:
        return self.rows.get(company_id)

    async def save_choices(self, company_id: str, choices: ModelChoices) -> StoredModels:
        current = self.rows.get(company_id) or StoredModels(company_id=company_id)
        self.rows[company_id] = current.model_copy(update=choices.model_dump())
        return self.rows[company_id]

    async def set_key(
        self, company_id: str, provider: Provider, sealed: str | None, hint: str
    ) -> StoredModels:
        current = self.rows.get(company_id) or StoredModels(company_id=company_id)
        sealed_keys, hints = dict(current.sealed_keys), dict(current.hints)
        if sealed is None:
            sealed_keys.pop(provider, None)
            hints.pop(provider, None)
        else:
            sealed_keys[provider], hints[provider] = sealed, hint
        self.rows[company_id] = current.model_copy(
            update={"sealed_keys": sealed_keys, "hints": hints}
        )
        return self.rows[company_id]
