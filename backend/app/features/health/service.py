"""Health check rules. No HTTP here; the router calls this."""

from app.core.config import Settings
from app.features.health.schemas import HealthResponse


class HealthService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_status(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=self._settings.app_name,
            version=self._settings.app_version,
            environment=self._settings.environment,
        )
