"""Builds LLM providers from settings: the one place mapping a model name to a provider."""

from app.core.config import Settings
from app.features.models.interfaces import LLMProvider
from app.features.models.providers.litellm_provider import LiteLLMProvider
from app.features.models.schemas import ModelConfig


def resolve_model_config(settings: Settings, model: str | None = None) -> ModelConfig:
    """Model name + where to reach it. Shared by our providers and external agents (OpenHands)."""
    name = model or settings.default_model
    if name.startswith(("ollama/", "ollama_chat/")):
        key = settings.ollama_api_key.get_secret_value() if settings.ollama_api_key else None
        return ModelConfig(model=name, api_base=settings.ollama_api_base, api_key=key)
    # Other providers read their keys from the standard env vars (ANTHROPIC_API_KEY, ...).
    return ModelConfig(model=name)


def build_provider(settings: Settings, model: str | None = None) -> LLMProvider:
    return provider_for(resolve_model_config(settings, model))


def provider_for(config: ModelConfig, num_retries: int = 5) -> LLMProvider:
    """A provider for a model and endpoint already resolved (e.g. with a founder's own key)."""
    return LiteLLMProvider(
        config.model, api_base=config.api_base, api_key=config.api_key, num_retries=num_retries
    )
