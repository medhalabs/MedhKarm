import pytest

from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.features.projects.exceptions import BacklogConflictError, ProjectNotFoundError
from app.features.projects.memory_repository import InMemoryProjectRepository
from app.features.projects.schemas import (
    ItemFields,
    ItemStatus,
    ItemUpdate,
    NewProject,
    ProjectStatus,
)
from app.features.projects.service import PLAN_JOB, ProjectService


def service() -> tuple[ProjectService, InMemoryProjectRepository, InMemoryJobQueue]:
    repo, queue = InMemoryProjectRepository(), InMemoryJobQueue()
    return ProjectService(repo, queue), repo, queue


async def planned(svc: ProjectService, repo: InMemoryProjectRepository) -> str:
    project = await svc.create(NewProject(name="Habits", goal="Track daily habits"))
    await repo.replace_open_items(
        project.id,
        [ItemFields(title="First item"), ItemFields(title="Second item")],
        ItemStatus.PROPOSED,
    )
    await repo.update_project(project.id, {"status": ProjectStatus.PLAN_READY})
    return project.id


async def test_creating_a_project_asks_the_pm_to_plan() -> None:
    svc, _, queue = service()

    project = await svc.create(NewProject(name="Habits", goal="Track daily habits", autopilot=True))

    assert project.status == ProjectStatus.PLANNING and project.autopilot
    assert [(j.kind, j.payload) for j in queue.jobs] == [(PLAN_JOB, {"project_id": project.id})]


async def test_approving_the_plan_makes_items_to_do() -> None:
    svc, repo, _ = service()
    project_id = await planned(svc, repo)

    project = await svc.approve_plan(project_id)

    assert project.status == ProjectStatus.ACTIVE
    assert [i.status for i in project.items] == ["todo", "todo"]
    with pytest.raises(BacklogConflictError):
        await svc.approve_plan(project_id)


async def test_editing_moving_and_deleting_items() -> None:
    svc, repo, _ = service()
    project_id = await planned(svc, repo)
    first, second = (await svc.get(project_id)).items

    await svc.update_item(project_id, second.id, ItemUpdate(title="Now first", position=1))
    added = await svc.add_item(project_id, ItemFields(title="Third item", size="S"))
    await svc.delete_item(project_id, first.id)

    items = (await svc.get(project_id)).items
    assert [(i.position, i.title) for i in items] == [(1, "Now first"), (2, "Third item")]
    assert added.status == ItemStatus.PROPOSED  # the plan isn't approved yet


async def test_started_work_cant_be_edited_or_deleted_but_blocked_can_be_retried() -> None:
    svc, repo, _ = service()
    project_id = await planned(svc, repo)
    await svc.approve_plan(project_id)
    item = (await svc.get(project_id)).items[0]
    await repo.update_item(item.id, {"status": ItemStatus.IN_PROGRESS})

    with pytest.raises(BacklogConflictError):
        await svc.update_item(project_id, item.id, ItemUpdate(title="Changed"))
    with pytest.raises(BacklogConflictError):
        await svc.delete_item(project_id, item.id)

    await repo.update_item(item.id, {"status": ItemStatus.BLOCKED, "note": "failed"})
    retried = await svc.retry_item(project_id, item.id)
    assert (retried.status, retried.note) == (ItemStatus.TODO, "")
    assert (await svc.skip_item(project_id, item.id)).status == ItemStatus.SKIPPED


async def test_pause_resume_and_unknown_projects() -> None:
    svc, repo, _ = service()
    project_id = await planned(svc, repo)
    await svc.approve_plan(project_id)

    assert (await svc.pause(project_id)).status == ProjectStatus.PAUSED
    assert (await svc.resume(project_id)).status == ProjectStatus.ACTIVE
    with pytest.raises(ProjectNotFoundError):
        await svc.get("nope")
