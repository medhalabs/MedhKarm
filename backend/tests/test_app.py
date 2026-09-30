"""Whole-app tests: the assembled app starts and every feature router is registered."""

from fastapi.testclient import TestClient

from app.main import app


def test_app_serves_health() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200


def test_openapi_schema_is_generated() -> None:
    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 200
    assert "/health" in response.json()["paths"]
