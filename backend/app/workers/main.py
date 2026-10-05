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

from app.core.config import get_settings
from app.core.database import session_factory
from app.core.logging import configure_logging
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
from app.features.runs.repository import SqlRunRepository
from app.features.runs.service import CANCEL_JOB, RESUME_JOB, START_JOB, RunService
from app.features.standups.delivery.log_delivery import LogDelivery
from app.features.standups.dependencies import get_standup_service
from app.features.workflows.service import WorkflowService
from app.workers.handlers.backlog import PlanBacklog, backlog_schedule
from app.workers.handlers.build import CancelBuild, ResumeBuild, StartBuild
from app.workers.handlers.evals import NIGHTLY_EVALS, NightlyEvals, nightly_evals_schedule
from app.workers.handlers.messages import MessageReply, TeamContext
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

    handlers: dict[str, JobHandler] = {
        START_JOB: StartBuild(runs, workflow, team.sandboxes, events, progress),
        RESUME_JOB: ResumeBuild(runs, workflow, team.sandboxes, events, progress),
        CANCEL_JOB: CancelBuild(workflow, team.sandboxes, events, progress),
        PLAN_JOB: PlanBacklog(planner, projects),
        REPLY_JOB: MessageReply(replier),
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
