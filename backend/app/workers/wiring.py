"""Chooses concrete implementations from settings and the team template. Entry points (CLI,
API, workers) call this; features only ever see interfaces (dependency inversion)."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from app.core.config import Settings
from app.core.database import session_factory
from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.events.stores.sql_store import SqlEventStore
from app.features.models.interfaces import LLMProvider
from app.features.models.service import build_provider, resolve_model_config
from app.features.sandbox.interfaces import SandboxProvider
from app.features.teams.loader import load_templates
from app.features.teams.schemas import RoleSpec, TeamTemplate
from app.features.teams.service import TeamService
from app.features.workflows.checkpointer import postgres_checkpointer
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService


@dataclass(frozen=True)
class TeamRuntime:
    """Everything a build run needs, built from one team template."""

    template: TeamTemplate
    planner: LLMProvider  # the CTO's model: plans and reviews
    planner_instructions: str
    review_instructions: str
    developer_names: list[str]
    max_developers: int
    engine: DeveloperEngine  # the developer
    sandboxes: SandboxProvider


def build_team_runtime(settings: Settings) -> TeamRuntime:
    template = TeamService(load_templates()).get_template(settings.team_template)
    cto, developer = template.role("cto"), template.role("developer")
    engine, sandboxes = build_engine(settings, developer)
    return TeamRuntime(
        template=template,
        planner=build_provider(settings, cto.model),
        planner_instructions=cto.instructions,
        review_instructions=cto.review_instructions,
        developer_names=developer.display_names,
        max_developers=developer.max_count,
        engine=engine,
        sandboxes=sandboxes,
    )


@asynccontextmanager
async def workflow_service(
    settings: Settings, team: TeamRuntime | None = None
) -> AsyncIterator[WorkflowService]:
    """A workflow service on Postgres (checkpoints and events), for one command or one job."""
    team = team or build_team_runtime(settings)
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


def build_engine(
    settings: Settings, role: RoleSpec | None = None
) -> tuple[DeveloperEngine, SandboxProvider]:
    """The developer engine and the sandbox it needs, shaped by the developer role (model,
    tools, instructions, step limit). Imports are local so the heavy OpenHands packages load
    only when that engine is chosen."""
    model = role.model if role else None
    if settings.developer_engine == "openhands":
        os.environ.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")
        from app.features.developer_engine.engines.openhands_engine import OpenHandsEngine
        from app.features.sandbox.providers.openhands_provider import OpenHandsSandboxProvider

        engine = OpenHandsEngine(
            resolve_model_config(settings, model), max_iterations=settings.openhands_max_iterations
        )
        return engine, OpenHandsSandboxProvider(settings.openhands_server_image)

    from app.features.developer_engine.engines.tool_loop_engine import (
        DEFAULT_TOOLS,
        SYSTEM_PROMPT,
        ToolLoopEngine,
    )
    from app.features.sandbox.providers.docker_provider import DockerSandboxProvider

    tools = list(role.tools) if role and role.tools else list(DEFAULT_TOOLS)
    if settings.builtin_apply_patch and "apply_patch" not in tools:
        tools.append("apply_patch")
    builtin = ToolLoopEngine(
        build_provider(settings, model),
        max_steps=(role.max_steps if role and role.max_steps else settings.builtin_max_steps),
        tools=tools,
        instructions=(role.instructions if role and role.instructions else SYSTEM_PROMPT),
    )
    return builtin, DockerSandboxProvider(settings.sandbox_image)
