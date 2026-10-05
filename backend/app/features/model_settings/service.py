"""Each founder's models and keys: what they chose, the keys they added (sealed), and, for
every model call, which model, endpoint and key to use.

Resolving a call: the role's own choice, else the company's team model, else the template's
model for that role (`fallback`), else the server default. Then the key: the company's own for
that provider, else ours when the company is on managed keys. On their own keys only, a model
without one of their keys doesn't run (`MissingKeyError`).
"""

import re
import time
from collections.abc import Callable

from app.features.model_settings.catalog import CHECK_MODEL, SUGGESTED
from app.features.model_settings.exceptions import MissingKeyError, ModelSettingsError
from app.features.model_settings.interfaces import ModelSettingsRepository, ProviderFactory
from app.features.model_settings.schemas import (
    PREFIX,
    CompanyModels,
    KeyCheck,
    KeyMode,
    ModelChoices,
    ModelOption,
    NewKey,
    Provider,
    SavedKey,
    StoredModels,
    provider_of,
)
from app.features.models.exceptions import ModelCallError
from app.features.models.schemas import ModelConfig
from app.shared.secret_box import SecretBox

ServerConfig = Callable[[str | None], ModelConfig]  # our own endpoint and key for a model
CACHE_SECONDS = 30.0  # workers see a founder's change within this long
CHECK_PROMPT = [{"role": "user", "content": "Reply with the single word OK."}]


class ModelSettingsService:
    def __init__(
        self,
        repository: ModelSettingsRepository,
        box: SecretBox,
        server: ServerConfig,
        server_providers: set[Provider],
        providers: ProviderFactory,
        ollama_base: str = "https://ollama.com",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._repository = repository
        self._box = box
        self._server = server
        self._server_providers = server_providers
        self._providers = providers
        self._ollama_base = ollama_base
        self._clock = clock
        self._cache: dict[str, tuple[float, StoredModels | None]] = {}

    # The founder's settings

    async def get(self, company_id: str) -> CompanyModels:
        return _view(await self._stored(company_id, fresh=True), company_id)

    def options(self) -> list[ModelOption]:
        return [
            ModelOption(provider=p, models=models, server_key=p in self._server_providers)
            for p, models in SUGGESTED.items()
        ]

    async def save(self, company_id: str, choices: ModelChoices) -> CompanyModels:
        stored = await self._stored(company_id, fresh=True)
        own = set(stored.sealed_keys) if stored else set()
        for model in sorted(choices.models()):
            self._check_runnable(model, choices, own)
        saved = await self._repository.save_choices(company_id, choices)
        self._cache.pop(company_id, None)
        return _view(saved, company_id)

    async def add_key(self, company_id: str, new: NewKey) -> CompanyModels:
        key = new.key.strip()
        saved = await self._repository.set_key(
            company_id, new.provider, self._box.seal(key), f"…{key[-4:]}"
        )
        self._cache.pop(company_id, None)
        return _view(saved, company_id)

    async def remove_key(self, company_id: str, provider: Provider) -> CompanyModels:
        saved = await self._repository.set_key(company_id, provider, None, "")
        self._cache.pop(company_id, None)
        return _view(saved, company_id)

    async def check(self, company_id: str, provider: Provider) -> KeyCheck:
        """One tiny call with the founder's key: does it work? Uses their chosen model of that
        provider, else the cheapest we know."""
        stored = await self._stored(company_id, fresh=True)
        chosen = [m for m in (stored.models() if stored else set()) if provider_of(m) == provider]
        model = sorted(chosen)[0] if chosen else CHECK_MODEL[provider]
        try:
            config = self._own_config(stored, model, provider)
            if config is None:
                return KeyCheck(
                    provider=provider, model=model, ok=False, error=f"Add your {provider} key first"
                )
            await self._providers(config, num_retries=0).complete(CHECK_PROMPT)
        except (ModelCallError, MissingKeyError) as error:
            return KeyCheck(provider=provider, model=model, ok=False, error=reason(error.message))
        return KeyCheck(provider=provider, model=model, ok=True)

    # Every model call

    async def config(self, company_id: str | None, role: str, fallback: str | None) -> ModelConfig:
        stored = await self._stored(company_id) if company_id else None
        if stored is None:
            return self._server(fallback)
        model = stored.role_models.get(role) or stored.default_model or fallback
        if model is None:
            model = self._server(None).model
        provider = provider_of(model)
        if provider is None:  # a template's own model name (e.g. bare "gpt-oss:20b")
            return self._managed(stored, model)
        own = self._own_config(stored, model, provider)
        if own is not None:
            return own
        return self._managed(stored, model, provider)

    def _own_config(
        self, stored: StoredModels | None, model: str, provider: Provider
    ) -> ModelConfig | None:
        sealed = stored.sealed_keys.get(provider) if stored else None
        key = self._box.open(sealed) if sealed else None
        if sealed and key is None:
            raise MissingKeyError(
                f"Your {provider} key can't be read any more (the server's key changed): "
                "add it again in Settings → Models"
            )
        if provider == Provider.LOCAL:
            if not stored or not stored.local_url:
                raise MissingKeyError("Local models need your connector's URL: Settings → Models")
            name = PREFIX[Provider.OLLAMA] + model.removeprefix(PREFIX[Provider.LOCAL])
            return ModelConfig(model=name, api_base=stored.local_url, api_key=key)
        if key is None:
            return None
        base = self._ollama_base if provider == Provider.OLLAMA else None
        return ModelConfig(model=model, api_base=base, api_key=key)

    def _managed(
        self, stored: StoredModels, model: str, provider: Provider | None = None
    ) -> ModelConfig:
        if stored.mode == KeyMode.OWN:
            raise MissingKeyError(
                f"You're on your own keys and there's no {provider or 'provider'} key for "
                f"{model}: add one, or choose another model, in Settings → Models"
            )
        return self._server(model)

    def _check_runnable(self, model: str, choices: ModelChoices, own: set[Provider]) -> None:
        provider = provider_of(model)
        if provider == Provider.LOCAL:
            if not choices.local_url:
                raise ModelSettingsError(f"{model} needs your connector's URL")
            return
        if provider in own:
            return
        if choices.mode == KeyMode.OWN:
            raise ModelSettingsError(f"Add your {provider} key before choosing {model}")
        if provider not in self._server_providers:
            raise ModelSettingsError(
                f"We don't run {provider} models on our keys: add your {provider} key first"
            )

    async def _stored(self, company_id: str, fresh: bool = False) -> StoredModels | None:
        now = self._clock()
        cached = self._cache.get(company_id)
        if not fresh and cached and now - cached[0] < CACHE_SECONDS:
            return cached[1]
        stored = await self._repository.get(company_id)
        self._cache[company_id] = (now, stored)
        return stored


def reason(error: str) -> str:
    """The provider's own words ("Invalid API Key") instead of LiteLLM's whole error."""
    found = re.search(r'"message"\s*:\s*"([^"]+)"', error)
    return (found.group(1) if found else error.strip())[:300]


def _view(stored: StoredModels | None, company_id: str) -> CompanyModels:
    if stored is None:
        return CompanyModels(company_id=company_id)
    return CompanyModels(
        company_id=company_id,
        mode=stored.mode,
        default_model=stored.default_model,
        role_models=stored.role_models,
        local_url=stored.local_url,
        keys=[SavedKey(provider=p, hint=stored.hints.get(p, "")) for p in stored.sealed_keys],
        updated_at=stored.updated_at,
    )
