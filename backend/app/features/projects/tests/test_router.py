"""The projects API on a feature-only app, with in-memory storage and fake runs."""

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_error_handlers
from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.features.projects.dependencies import get_backlog_progress, get_project_service
from app.features.projects.memory_repository import InMemoryProjectRepository
from app.features.projects.progress import BacklogProgress
from app.features.projects.router import router
from app.features.projects.schemas import ItemFields, ItemStatus, ProjectStatus
from app.features.projects.service import ProjectService
from app.features.projects.tests.helpers import FakeRuns


def test_create_plan_approve_edit_and_start() -> None:
    repo, runs = InMemoryProjectRepository(), FakeRuns()
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_project_service] = lambda: ProjectService(repo, InMemoryJobQueue())
    app.dependency_overrides[get_backlog_progress] = lambda: BacklogProgress(repo, runs)
    api = TestClient(app)

    created = api.post("/projects", json={"name": "Habits", "goal": "Track daily habits"})
    project_id = created.json()["id"]
    assert created.status_code == 202 and created.json()["status"] == "planning"

    # what the PM's job would do
    asyncio.run(
        repo.replace_open_items(project_id, [ItemFields(title="Add a habit")], ItemStatus.PROPOSED)
    )
    asyncio.run(repo.update_project(project_id, {"status": ProjectStatus.PLAN_READY}))

    assert api.post(f"/projects/{project_id}/next").json()["error"]["code"] == "backlog_conflict"
    approved = api.post(f"/projects/{project_id}/plan/approve").json()
    item_id = approved["items"][0]["id"]
    assert approved["status"] == "active"

    api.patch(f"/projects/{project_id}/items/{item_id}", json={"acceptance": ["saved"]})
    started = api.post(f"/projects/{project_id}/next")
    assert started.status_code == 202 and started.json()["status"] == "in_progress"
    assert runs.started[0].request.startswith("Add a habit")
    assert api.get("/projects").json()[0]["id"] == project_id
    assert api.get("/projects/nope").json()["error"]["code"] == "project_not_found"
