"""The runs API on a feature-only app, with in-memory storage."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_error_handlers
from app.features.auth.tests.helpers import OTHER_COMPANY, sign_in
from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.features.runs.dependencies import get_run_service
from app.features.runs.memory_repository import InMemoryRunRepository
from app.features.runs.router import router
from app.features.runs.service import RunService


def test_start_list_get_and_approve() -> None:
    queue = InMemoryJobQueue()
    service = RunService(InMemoryRunRepository(), queue)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_run_service] = lambda: service
    sign_in(app)
    api = TestClient(app)

    started = api.post("/runs", json={"request": "Build a calculator", "test_command": "pytest"})
    run_id = started.json()["id"]

    assert started.status_code == 202
    assert started.json()["status"] == "queued"
    assert [r["id"] for r in api.get("/runs").json()] == [run_id]
    assert api.get(f"/runs/{run_id}").json()["request"] == "Build a calculator"
    assert api.get("/runs/missing").json()["error"]["code"] == "run_not_found"
    early = api.post(f"/runs/{run_id}/approval", json={"approved": True})
    assert early.status_code == 409
    assert early.json()["error"]["code"] == "run_not_waiting_for_approval"
    assert api.post("/runs", json={"request": ""}).status_code == 422
    bad_repo = {"request": "Add search", "repo": {"url": "https://example.com/x/y"}}
    assert api.post("/runs", json=bad_repo).status_code == 422
    assert len(queue.jobs) == 1

    repo = {"url": "https://github.com/a/notes", "branch": "dev"}
    on_repo = api.post("/runs", json={"request": "Add search", "repo": repo}).json()
    assert on_repo["repo"] == repo and on_repo["test_command"] == ""
    bad_name = {"request": "Build a timer", "new_repo_name": "my timer"}
    assert api.post("/runs", json=bad_name).status_code == 422


def test_runs_belong_to_the_founders_company() -> None:
    service = RunService(InMemoryRunRepository(), InMemoryJobQueue())
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_run_service] = lambda: service
    sign_in(app)
    mine = TestClient(app).post("/runs", json={"request": "Build a timer"}).json()

    sign_in(app, OTHER_COMPANY)
    other = TestClient(app)
    assert other.get("/runs").json() == []
    assert other.get(f"/runs/{mine['id']}").status_code == 404
    assert other.post(f"/runs/{mine['id']}/cancel").status_code == 404

    app.dependency_overrides.clear()
    app.dependency_overrides[get_run_service] = lambda: service
    assert TestClient(app).get("/runs").status_code == 401  # not signed in


def test_cancel_over_the_api() -> None:
    service = RunService(InMemoryRunRepository(), InMemoryJobQueue())
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_run_service] = lambda: service
    sign_in(app)
    api = TestClient(app)
    run = api.post("/runs", json={"request": "Build a timer"}).json()

    assert api.post(f"/runs/{run['id']}/cancel").json()["status"] == "cancelled"
    again = api.post(f"/runs/{run['id']}/cancel")
    assert (again.status_code, again.json()["error"]["code"]) == (409, "run_already_finished")
