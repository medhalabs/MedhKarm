"""Command-line entry point for the eval suite.

    uv run python -m app.workers.run_evals list
    uv run python -m app.workers.run_evals validate [--tasks id1,id2] [--parallel 4]
    uv run python -m app.workers.run_evals run [--engine builtin|openhands] [--model NAME]
        [--tasks id1,id2] [--parallel 2]

`validate` needs only Docker: it proves every task is fair and not already solved.
`run` sends each task through the real build workflow and saves a report to
`backend/evals/results/`.
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.features.evals.loader import load_tasks
from app.features.evals.report import save, summary_markdown, validation_markdown
from app.features.evals.runner import EvalRunner
from app.features.evals.schemas import EvalReport, TaskOutcome
from app.features.evals.validator import TaskValidator
from app.features.repos.code_graph import GraphifyCodeGraph
from app.features.repos.service import RepoService
from app.features.sandbox.providers.docker_provider import DockerSandboxProvider
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService
from app.workers.wiring import build_team_runtime, ensure_sandbox_image

BACKEND_DIR = Path(__file__).resolve().parents[2]
EVALS_DIR = BACKEND_DIR / "evals"

# The OpenHands agent-server image has Python and Node but not our test tools.
OPENHANDS_PREPARE = "pip install -q pytest fastapi httpx2 >/dev/null 2>&1"


def print_outcome(outcome: TaskOutcome) -> None:
    status = "ERROR" if outcome.errored else ("PASS" if outcome.passed else "FAIL")
    detail = outcome.error or (
        f"visible={'yes' if outcome.visible_passed else 'no'} "
        f"hidden={'yes' if outcome.hidden_passed else 'no'}"
    )
    print(
        f"{status} {outcome.task_id:32} {outcome.seconds:6.0f}s "
        f"{outcome.total_tokens:>8,} tokens  {detail}",
        flush=True,
    )


async def validate(settings: Settings, only: list[str] | None, parallel: int) -> int:
    ensure_sandbox_image(settings.eval_sandbox_image)
    tasks = load_tasks(EVALS_DIR, only)
    validator = TaskValidator(DockerSandboxProvider(settings.eval_sandbox_image))
    results = await validator.validate_all(tasks, parallel=parallel)
    print(validation_markdown(results))
    return 0 if all(r.ok for r in results) else 1


async def run(settings: Settings, only: list[str] | None, parallel: int) -> int:
    prepare = None
    if settings.developer_engine == "openhands":
        prepare = OPENHANDS_PREPARE
    else:
        ensure_sandbox_image(settings.eval_sandbox_image)
        settings = settings.model_copy(update={"sandbox_image": settings.eval_sandbox_image})

    tasks = load_tasks(EVALS_DIR, only)
    team = build_team_runtime(settings)
    sandboxes = team.sandboxes
    graph = build_app_graph(
        team.planner,
        team.engine,
        sandboxes,
        InMemorySaver(),
        planner_instructions=team.planner_instructions,
        review_instructions=team.review_instructions,
        developer_names=team.developer_names,
        max_developers=team.max_developers,
        approval_policy=team.approval_policy,
        repos=RepoService(graph=GraphifyCodeGraph() if settings.code_graph else None),
    )
    runner = EvalRunner(WorkflowService(graph), sandboxes, prepare_command=prepare)

    started = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(
        f"Running {len(tasks)} tasks · engine={settings.developer_engine} · "
        f"model={settings.default_model} · code_graph={settings.code_graph} · "
        f"parallel={parallel}\n",
        flush=True,
    )
    outcomes = await runner.run_all(tasks, parallel=parallel, on_outcome=print_outcome)

    report = EvalReport(
        started_at=started,
        engine=settings.developer_engine,
        model=settings.default_model,
        outcomes=outcomes,
        variant="code-graph" if settings.code_graph else "",
    )
    path = save(report, EVALS_DIR / "results")
    print("\n" + summary_markdown(report))
    print(f"Saved: {path.relative_to(BACKEND_DIR)} (+ .json)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Eval suite for the AI teams.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    for name in ("validate", "run"):
        sub = commands.add_parser(name)
        sub.add_argument("--tasks", help="Comma-separated task ids (default: all)")
        sub.add_argument("--parallel", type=int, default=4 if name == "validate" else 2)
        if name == "run":
            sub.add_argument("--engine", choices=["builtin", "openhands"])
            sub.add_argument("--model", help="LiteLLM model name; overrides DEFAULT_MODEL")
            sub.add_argument(
                "--code-graph", choices=["on", "off"], help="Overrides CODE_GRAPH (A/B runs)"
            )
    args = parser.parse_args()

    configure_logging("WARNING")
    settings = get_settings()
    if args.command == "list":
        for task in load_tasks(EVALS_DIR):
            print(f"{task.id:32} {task.kind:9} d{task.difficulty} {task.language:10} {task.title}")
        return

    only = [t.strip() for t in args.tasks.split(",")] if args.tasks else None
    if args.command == "validate":
        sys.exit(asyncio.run(validate(settings, only, args.parallel)))

    updates: dict[str, str | bool] = {}
    if args.engine:
        updates["developer_engine"] = args.engine
    if args.model:
        updates["default_model"] = args.model
    if args.code_graph:
        updates["code_graph"] = args.code_graph == "on"
    sys.exit(asyncio.run(run(settings.model_copy(update=updates), only, args.parallel)))


if __name__ == "__main__":
    main()
