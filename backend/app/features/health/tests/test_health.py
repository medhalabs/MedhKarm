from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.features.health.router import router
from app.features.health.service import HealthService


def test_service_reports_ok_with_settings() -> None:
    settings = Settings(app_name="Test API", app_version="9.9.9", environment="test")

    result = HealthService(settings).get_status()

    assert result.status == "ok"
    assert result.service == "Test API"
    assert result.version == "9.9.9"
    assert result.environment == "test"


def test_health_endpoint_returns_ok() -> None:
    app = FastAPI()
    app.include_router(router)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
