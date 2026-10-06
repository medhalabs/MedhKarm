from typing import Protocol

from app.features.model_settings.schemas import ModelChoices, Provider, StoredModels
from app.features.models.interfaces import LLMProvider
from app.features.models.schemas import ModelConfig


class ModelSettingsRepository(Protocol):
    async def get(self, company_id: str) -> StoredModels | None: ...

    async def save_choices(self, company_id: str, choices: ModelChoices) -> StoredModels: ...

    async def set_key(
        self, company_id: str, provider: Provider, sealed: str | None, hint: str
    ) -> StoredModels:
        """Adds or replaces a key; `sealed=None` removes it."""
        ...


class ModelResolver(Protocol):
    """A model call's model, endpoint and key for a company and role (None: no company, e.g.
    evals, which run on our keys)."""

    async def config(
        self, company_id: str | None, role: str, fallback: str | None
    ) -> ModelConfig: ...

    async def config_with_ownership(
        self, company_id: str | None, role: str, fallback: str | None
    ) -> tuple[ModelConfig, bool]: ...


class ProviderFactory(Protocol):
    def __call__(self, config: ModelConfig, num_retries: int = 5) -> LLMProvider: ...
