from app.core.errors import AppError


class ModelSettingsError(AppError):
    """A choice that can't run: a model with no key to run it."""

    status_code = 400
    code = "model_settings_invalid"


class MissingKeyError(AppError):
    """A model call for a company on its own keys, with no key for that model's provider."""

    status_code = 400
    code = "model_key_missing"
