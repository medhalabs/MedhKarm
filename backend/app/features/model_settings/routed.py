"""An LLMProvider that picks the model and key per call, for whichever company's work is running
(`app.core.tenant`). The team is built once per worker; each call then uses that founder's own
choice and key, or ours."""

from app.core.tenant import current_company
from app.features.model_settings.interfaces import ModelResolver, ProviderFactory
from app.features.models.interfaces import LLMProvider
from app.features.models.schemas import LLMResponse, Message, ModelConfig, ToolSpec
from app.features.models.service import provider_for


class CompanyRoutedProvider:
    def __init__(
        self,
        resolver: ModelResolver,
        role: str,
        fallback: str | None = None,
        providers: ProviderFactory = provider_for,
    ) -> None:
        self._resolver = resolver
        self._role = role
        self._fallback = fallback
        self._providers = providers
        self._built: dict[tuple[str, str | None, str | None], LLMProvider] = {}
        self._last: dict[str | None, str] = {}  # company -> the model it last used
        self._own_key: dict[str | None, bool] = {}

    @property
    def model_name(self) -> str:
        """The model this company's last call used (for the activity log and metering)."""
        return self._last.get(current_company.get()) or self._fallback or "default"

    @property
    def own_key(self) -> bool:
        return self._own_key.get(current_company.get(), False)

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> LLMResponse:
        company = current_company.get()
        config, own_key = await self._resolver.config_with_ownership(
            company, self._role, self._fallback
        )
        self._last[company] = config.model
        self._own_key[company] = own_key
        return await self._provider(config).complete(messages, tools)

    def _provider(self, config: ModelConfig) -> LLMProvider:
        key = (config.model, config.api_base, config.api_key)
        if key not in self._built:
            self._built[key] = self._providers(config)
        return self._built[key]
