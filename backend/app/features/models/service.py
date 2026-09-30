"""Builds LLM providers from settings: the one place mapping a model name to a provider."""

from app.core.config import Settings
from app.features.models.interfaces import LLMProvider
from app.features.models.providers.litellm_provider import LiteLLMProvider


def build_provider(settings: Settings, model: str | None = None) -> LLMProvider:
    name = model or settings.default_model
    if name.startswith(("ollama/", "ollama_chat/")):
        key = settings.ollama_api_key.get_secret_value() if settings.ollama_api_key else None
        return LiteLLMProvider(name, api_base=settings.ollama_api_base, api_key=key)
    # Other providers read their keys from the standard env vars (ANTHROPIC_API_KEY, ...).
    return LiteLLMProvider(name)
