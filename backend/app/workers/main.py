"""Background worker: runs queued jobs (build runs, the morning standup).

    uv run python -m app.workers.main

Run as many as you like; they share the Postgres job queue. Ctrl+C hands running jobs back to
the queue, and a worker that dies has its jobs picked up again once their lease runs out.
"""

import asyncio
import logging
import os
import signal
import socket
from contextlib import AbstractAsyncContextManager
from datetime import timedelta
from typing import Any

from app.core.config import get_settings
from app.core.database import session_factory
from app.core.logging import configure_logging
from app.features.blueprints.author import BlueprintAuthor
from app.features.blueprints.repository import SqlBlueprintRepository
from app.features.blueprints.service import REVISE_JOB, WRITE_JOB
from app.features.blueprints.writer import BlueprintWriter
from app.features.events.stores.sql_store import SqlEventStore
from app.features.jobs.interfaces import JobHandler
from app.features.jobs.service import JobRunner
from app.features.jobs.stores.sql_queue import SqlJobQueue
from app.features.messages.replier import AgentReplier
from app.features.messages.repository import SqlMessageRepository
from app.features.messages.service import REPLY_JOB, MessageService
from app.features.notifications.dependencies import get_notification_service
from app.features.projects.planner import BacklogPlanner
from app.features.projects.progress import BacklogProgress
from app.features.projects.repository import SqlProjectRepository
from app.features.projects.service import PLAN_JOB
from app.features.repos.github import GitHubRepoHost
from app.features.runs.exceptions import RunNotFoundError
from app.features.runs.repository import SqlRunRepository
from app.features.runs.service import CANCEL_JOB, RESUME_JOB, START_JOB, RunService
from app.features.standups.delivery.log_delivery import LogDelivery
from app.features.standups.dependencies import get_standup_service
from app.features.starters.service import StarterService
from app.features.workflows.service import WorkflowService
from app.workers.approved_plans import StackText
from app.workers.handlers.backlog import PlanBacklog, backlog_schedule
from app.workers.handlers.blueprint import ReviseBlueprint, WriteBlueprint
from app.workers.handlers.build import CancelBuild, ResumeBuild, StartBuild
from app.workers.handlers.evals import NIGHTLY_EVALS, NightlyEvals, nightly_evals_schedule
from app.workers.handlers.messages import MessageReply, TeamContext
from app.workers.handlers.scope import CompanyScoped
from app.workers.handlers.standup import (
    SEND_STANDUP,
    SEND_WEEKLY,
    SendStandup,
    SendWeekly,
    standup_schedule,
)
from app.workers.wiring import (
    build_team_runtime,
    ensure_sandbox_image,
    personas,
    role_model,
    workflow_service,
)

logger = logging.getLogger(__name__)


async def main() -> None:
    configure_logging()
    settings = get_settings()
    queue = SqlJobQueue(session_factory)
    events = SqlEventStore(session_factory)
    runs = RunService(SqlRunRepository(session_factory), queue, settings.build_max_attempts)
    if settings.developer_engine == "builtin":
        ensure_sandbox_image(settings.sandbox_image)
    team = build_team_runtime(settings)
    standups = get_standup_service()
    notifications = get_notification_service()
    projects = SqlProjectRepository(session_factory)
    progress = BacklogProgress(
        projects, runs, GitHubRepoHost(settings.github_token), settings.standup_timezone
    )
    messages = SqlMessageRepository(session_factory)
    planner = BacklogPlanner(
        team.pm, projects, events, team.pm_instructions, MessageService(messages)
    )
    replier = AgentReplier(
        messages,
        lambda role: role_model(settings, team, role),
        personas(team),
        TeamContext(runs, projects, events),
        events,
    )

    def workflow() -> AbstractAsyncContextManager[WorkflowService]:
        return workflow_service(settings, team)

    async def run_company(payload: dict[str, Any]) -> str | None:
        try:
            return (await runs.get(str(payload.get("run_id", "")))).company_id
        except RunNotFoundError:
            return None

    async def project_company(payload: dict[str, Any]) -> str | None:
        project = await projects.get_project(str(payload.get("project_id", "")))
        return project.company_id if project else None

    async def message_company(payload: dict[str, Any]) -> str | None:
        try:
            message = await messages.get(int(payload.get("message_id", 0)))
        except (TypeError, ValueError):
            return None
        return message.company_id if message else None

    blueprints = SqlBlueprintRepository(session_factory)
    lekha = team.template.role("docs")
    author = BlueprintAuthor(
        blueprints,
        BlueprintWriter(
            role_model(settings, team, "docs"), lekha.instructions, StackText(StarterService())
        ),
        lekha.display_names[0],
    )

    async def blueprint_company(payload: dict[str, Any]) -> str | None:
        found = await blueprints.get(str(payload.get("blueprint_id", "")))
        return found.company_id if found else None

    # Jobs that call models run as their company: its own models and keys (model_settings).
    handlers: dict[str, JobHandler] = {
        START_JOB: CompanyScoped(
            StartBuild(runs, workflow, team.sandboxes, events, progress), run_company
        ),
        RESUME_JOB: CompanyScoped(
            ResumeBuild(runs, workflow, team.sandboxes, events, progress), run_company
        ),
        CANCEL_JOB: CancelBuild(workflow, team.sandboxes, events, progress),
        PLAN_JOB: CompanyScoped(PlanBacklog(planner, projects), project_company),
        REPLY_JOB: CompanyScoped(MessageReply(replier), message_company),
        WRITE_JOB: CompanyScoped(WriteBlueprint(author), blueprint_company),
        REVISE_JOB: CompanyScoped(ReviseBlueprint(author), blueprint_company),
        NIGHTLY_EVALS: NightlyEvals(settings),
        SEND_STANDUP: SendStandup(standups, LogDelivery(), notifications, runs, settings.app_url),
        SEND_WEEKLY: SendWeekly(
            notifications, runs, events, settings.standup_timezone, settings.app_url
        ),
    }
    runner = JobRunner(
        queue,
        handlers,
        worker_id=f"{socket.gethostname()}-{os.getpid()}",
        lease=timedelta(seconds=settings.job_lease_seconds),
        retry_base=timedelta(seconds=settings.job_retry_seconds),
        concurrency=settings.worker_concurrency,
        poll_seconds=settings.worker_poll_seconds,
        periodic=[
            backlog_schedule(progress),
            nightly_evals_schedule(queue, settings),
            *(
                [standup_schedule(queue, standups, notifications)]
                if settings.standup_schedule
                else []
            ),
        ],
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    logger.info(
        "Worker %s started: %s jobs at once, %s engine, team %s",
        runner.worker_id,
        settings.worker_concurrency,
        settings.developer_engine,
        team.template.id,
    )
    await runner.run_forever(stop)
    logger.info("Worker %s stopped", runner.worker_id)


if __name__ == "__main__":
    asyncio.run(main())
