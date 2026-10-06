from app.core.errors import ConflictError


class NoProjectSettingsError(ConflictError):
    """Only a project can go back to the company's settings."""

    code = "autonomy_scope_invalid"
