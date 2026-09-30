"""Command-line entry point for build runs (the Phase 0 stack check).

    uv run python -m app.workers.build_run start --request "..." --test-command "..."
    uv run python -m app.workers.build_run resume <run_id> --approve   (or --reject)
    uv run python -m app.workers.build_run status <run_id>

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

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.models.service import build_provider
from app.features.sandbox.providers.docker_provider import DockerSandboxProvider
from app.features.workflows.checkpointer import postgres_checkpointer
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.schemas import RunOutcome, StepUpdate
from app.features.workflows.service import WorkflowService


@asynccontextmanager
async def workflow_service() -> AsyncIterator[WorkflowService]:
    settings = get_settings()
    llm = build_provider(settings)
    sandboxes = DockerSandboxProvider(settings.sandbox_image)
    async with postgres_checkpointer(settings) as checkpointer:
        graph = build_app_graph(llm, ToolLoopEngine(llm), sandboxes, checkpointer)
        yield WorkflowService(graph)


def print_step(step: StepUpdate) -> None:
    data = step.data
    if step.node == "plan":
        print(f"\n[plan]\n{data.get('plan', '')}")
    elif step.node == "develop":
        dev = data.get("dev_result", {})
        print(
            f"\n[develop] success={dev.get('success')} steps={dev.get('steps')} "
            f"tokens={dev.get('total_tokens')}\n  summary: {dev.get('summary')}\n"
            f"  files: {', '.join(dev.get('files_changed', []))}"
        )
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
    resume = commands.add_parser("resume")
    resume.add_argument("run_id")
    decision = resume.add_mutually_exclusive_group(required=True)
    decision.add_argument("--approve", action="store_true")
    decision.add_argument("--reject", action="store_true")
    resume.add_argument("--feedback", default="")
    status = commands.add_parser("status")
    status.add_argument("run_id")
    args = parser.parse_args()

    configure_logging("WARNING")
    async with workflow_service() as service:
        if args.command == "start":
            run_id = uuid.uuid4().hex[:12]
            print(f"Run {run_id}: {args.request}")
            outcome = await service.start(run_id, args.request, args.test_command, print_step)
        elif args.command == "resume":
            outcome = await service.resume(args.run_id, args.approve, args.feedback, print_step)
        else:
            outcome = await service.get(args.run_id)
        print_outcome(outcome)


if __name__ == "__main__":
    asyncio.run(main())
