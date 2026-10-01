"""Command-line entry point for build runs (the Phase 0 stack check).

    uv run python -m app.workers.build_run start --request "..." --test-command "..."
        [--engine builtin|openhands]
    uv run python -m app.workers.build_run resume <run_id> --approve   (or --reject)
    uv run python -m app.workers.build_run status <run_id>
    uv run python -m app.workers.build_run events <run_id>     (the run's activity log)

Each command is a separate process: `resume` proves a paused run survives a restart,
because everything it needs is in the Postgres checkpoint and the sandbox id.
This is the only place concrete classes are chosen (dependency inversion).
"""

import argparse
import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.core.config import Settings, get_settings
from app.core.database import session_factory
from app.core.logging import configure_logging
from app.features.events.service import EventService
from app.features.events.stores.sql_store import SqlEventStore
from app.features.workflows.checkpointer import postgres_checkpointer
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.schemas import RunOutcome, StepUpdate
from app.features.workflows.service import WorkflowService
from app.workers.wiring import build_team_runtime


@asynccontextmanager
async def workflow_service(settings: Settings) -> AsyncIterator[WorkflowService]:
    team = build_team_runtime(settings)
    events = SqlEventStore(session_factory)
    async with postgres_checkpointer(settings) as checkpointer:
        graph = build_app_graph(
            team.planner,
            team.engine,
            team.sandboxes,
            checkpointer,
            events=events,
            planner_instructions=team.planner_instructions,
            review_instructions=team.review_instructions,
            developer_names=team.developer_names,
            max_developers=team.max_developers,
        )
        yield WorkflowService(graph, events)


async def print_events(run_id: str) -> None:
    service = EventService(SqlEventStore(session_factory))
    for event in await service.list_for_run(run_id):
        tokens = f"  [{event.tokens:,} tokens]" if event.tokens else ""
        when = f"{event.occurred_at:%H:%M:%S}"
        print(f"{when}  {event.actor:<9} {event.type:<19} {event.summary}{tokens}")
    totals = await service.totals_for_run(run_id)
    print(f"\n{totals.events} events · {totals.tokens:,} tokens")


def print_step(step: StepUpdate) -> None:
    data = step.data
    if step.node == "plan":
        print(f"\n[plan]\n{data.get('plan', '')}")
    elif step.node == "develop":
        tasks: list[dict[str, Any]] = data.get("tasks", [])
        task: dict[str, Any] = next((t for t in tasks if t.get("status") == "review"), {})
        print(
            f'\n[develop] {task.get("owner")} on "{task.get("title")}" '
            f"(attempt {task.get('attempts')}): tests passed={task.get('success')}\n"
            f"  summary: {task.get('summary')}\n  files: {', '.join(task.get('files_changed', []))}"
        )
    elif step.node == "review":
        review = data.get("last_review", {})
        verdict = "approved" if review.get("decision") == "approve" else "sent back"
        print(f'\n[review] Kabir {verdict} "{review.get("title")}"')
        if review.get("decision") != "approve":
            print("  " + str(review.get("feedback", ""))[:300].replace("\n", "\n  "))
    elif step.node == "verify":
        print(f"\n[verify] tests passed={data.get('verified')}")
        print("  " + str(data.get("verify_output", "")).strip().replace("\n", "\n  "))
    elif step.node == "approval":
        print(f"\n[approval] approved={data.get('approved')}")
    elif step.node == "finish":
        print(f"\n[finish] status={data.get('status')}")


def print_outcome(outcome: RunOutcome) -> None:
    if outcome.waiting_for_approval:
        print(f"\nPAUSED at the release gate. Run id: {outcome.run_id}")
        print(json.dumps(outcome.gate, indent=2)[:1500])
        print(
            "\nResume later with:\n"
            f"  uv run python -m app.workers.build_run resume {outcome.run_id} --approve"
        )
    else:
        print(f"\nDONE. Run {outcome.run_id} status={outcome.state.get('status')}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Start, resume or inspect a build run.")
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--request", required=True)
    start.add_argument("--test-command", required=True)
    start.add_argument(
        "--engine", choices=["builtin", "openhands"], help="Overrides DEVELOPER_ENGINE"
    )
    resume = commands.add_parser("resume")
    resume.add_argument("run_id")
    decision = resume.add_mutually_exclusive_group(required=True)
    decision.add_argument("--approve", action="store_true")
    decision.add_argument("--reject", action="store_true")
    resume.add_argument("--feedback", default="")
    status = commands.add_parser("status")
    status.add_argument("run_id")
    events = commands.add_parser("events")
    events.add_argument("run_id")
    args = parser.parse_args()

    configure_logging("WARNING")
    if args.command == "events":
        await print_events(args.run_id)
        return
    settings = get_settings()
    if getattr(args, "engine", None):
        settings = settings.model_copy(update={"developer_engine": args.engine})
    async with workflow_service(settings) as service:
        if args.command == "start":
            run_id = uuid.uuid4().hex[:12]
            print(f"Run {run_id} ({settings.developer_engine} engine): {args.request}")
            outcome = await service.start(run_id, args.request, args.test_command, print_step)
        elif args.command == "resume":
            outcome = await service.resume(args.run_id, args.approve, args.feedback, print_step)
        else:
            outcome = await service.get(args.run_id)
        print_outcome(outcome)


if __name__ == "__main__":
    asyncio.run(main())
