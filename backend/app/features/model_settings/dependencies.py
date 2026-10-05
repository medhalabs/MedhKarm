import logging
import os
from functools import cache, partial

from app.core.config import Settings, get_settings
from app.core.database import session_factory
from app.features.model_settings.catalog import SERVER_KEY_ENV
from app.features.model_settings.repository import SqlModelSettingsRepository
from app.features.model_settings.schemas import Provider
from app.features.model_settings.service import ModelSettingsService
from app.features.models.service import provider_for, resolve_model_config
from app.shared.secret_box import SecretBox

logger = logging.getLogger(__name__)
DEV_SECRET = "medhkarm-development-only-keys-secret"


def server_providers(settings: Settings) -> set[Provider]:
    """The providers we can run on our own keys."""
    found = {p for p, env in SERVER_KEY_ENV.items() if os.environ.get(env)}
    if settings.ollama_api_key:
        found.add(Provider.OLLAMA)
    return found


def secret_box(settings: Settings) -> SecretBox:
    secret = settings.secrets_key or settings.auth_secret
    if secret is not None:
        return SecretBox(secret.get_secret_value())
    if settings.environment == "development":
        logger.warning("SECRETS_KEY isn't set: founders' keys use the development secret")
        return SecretBox(DEV_SECRET)
    raise RuntimeError("Set SECRETS_KEY (a long random string) outside development")


def model_settings_service(settings: Settings) -> ModelSettingsService:
    return ModelSettingsService(
        SqlModelSettingsRepository(session_factory),
        secret_box(settings),
        partial(resolve_model_config, settings),
        server_providers(settings),
        provider_for,
        settings.ollama_api_base,
    )


@cache
def get_model_settings_service() -> ModelSettingsService:
    return model_settings_service(get_settings())
