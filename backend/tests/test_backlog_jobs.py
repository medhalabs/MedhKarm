"""The backlog's worker side: the PM's planning job, and the periodic step."""

from typing import Any

from app.features.jobs.service import JobRunner
from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.projects.memory_repository import InMemoryProjectRepository
from app.features.projects.planner import BacklogPlanner
from app.features.projects.schemas import NewProject, ProjectStatus
from app.features.projects.service import PLAN_JOB, ProjectService
from app.workers.handlers.backlog import PlanBacklog


def backlog() -> LLMResponse:
    items: list[dict[str, Any]] = [
        {"title": "Add a habit", "description": "", "acceptance": ["saved"], "size": "S"}
    ]
    return LLMResponse(
        tool_calls=[
            ToolCall(
                id="b",
                name="submit_backlog",
                arguments={"summary": "", "questions": [], "items": items},
            )
        ]
    )


async def test_creating_a_project_gets_a_plan_from_the_worker() -> None:
    repo, queue = InMemoryProjectRepository(), InMemoryJobQueue()
    projects = ProjectService(repo, queue)
    planner = BacklogPlanner(ScriptedLLMProvider([backlog()]), repo)
    worker = JobRunner(queue, {PLAN_JOB: PlanBacklog(planner, repo)}, "w1")

    created = await projects.create(NewProject(name="Habits", goal="Track daily habits"))
    await worker.run_once()

    project = await projects.get(created.id)
    assert project.status == ProjectStatus.PLAN_READY
    assert [i.title for i in project.items] == ["Add a habit"]


async def test_planning_that_keeps_failing_pauses_the_project_with_a_reason() -> None:
    repo, queue = InMemoryProjectRepository(), InMemoryJobQueue()
    projects = ProjectService(repo, queue)
    planner = BacklogPlanner(ScriptedLLMProvider([]), repo)  # every model call fails
    worker = JobRunner(queue, {PLAN_JOB: PlanBacklog(planner, repo)}, "w1")
    created = await projects.create(NewProject(name="Habits", goal="Track daily habits"))
    queue.jobs[0].max_attempts = 1

    await worker.run_once()

    project = await projects.get(created.id)
    assert project.status == ProjectStatus.PAUSED
    assert project.error.startswith("Mira couldn't plan the backlog")
