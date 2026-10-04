"""Chooses concrete implementations from settings and the team template. Entry points (CLI,
API, workers) call this; features only ever see interfaces (dependency inversion)."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings
from app.core.database import session_factory
from app.features.approvals.schemas import ApprovalPolicy
from app.features.deploys.service import DeployService
from app.features.deploys.vercel import VercelDeployTarget
from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.events.stores.sql_store import SqlEventStore
from app.features.models.interfaces import LLMProvider
from app.features.models.service import build_provider, resolve_model_config
from app.features.repos.code_graph import GraphifyCodeGraph
from app.features.repos.github import GitHubRepoHost
from app.features.repos.service import RepoService
from app.features.sandbox.interfaces import SandboxProvider
from app.features.security.service import SecurityReview
from app.features.teams.loader import load_templates
from app.features.teams.schemas import RoleSpec, TeamTemplate
from app.features.teams.service import TeamService
from app.features.workflows.checkpointer import postgres_checkpointer
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService

logger = logging.getLogger(__name__)

SANDBOX_IMAGE_DIR = Path(__file__).resolve().parents[2] / "sandbox-image"
OWN_IMAGE_PREFIX = "medhkarm-sandbox:"


def ensure_sandbox_image(tag: str) -> None:
    """Build our sandbox image (backend/sandbox-image/) if it isn't there yet. Other images
    are pulled by Docker as usual. About a minute, once per machine."""
    if not tag.startswith(OWN_IMAGE_PREFIX):
        return
    import docker

    client = docker.from_env()
    try:
        client.images.get(tag)
    except docker.errors.ImageNotFound:
        logger.warning("Building sandbox image %s (one-time, about a minute)...", tag)
        client.images.build(path=str(SANDBOX_IMAGE_DIR), tag=tag, rm=True)


@dataclass(frozen=True)
class TeamRuntime:
    """Everything a build run needs, built from one team template."""

    template: TeamTemplate
    planner: LLMProvider  # the CTO's model: plans and reviews
    planner_instructions: str
    review_instructions: str
    developer_names: list[str]
    max_developers: int
    specialties: dict[str, str]  # developer name -> specialty
    specialty_instructions: dict[str, str]  # specialty -> instructions
    approval_policy: ApprovalPolicy  # what happens at the release gate
    pm: LLMProvider  # the PM's model: plans project backlogs
    pm_instructions: str
    security: SecurityReview | None  # the security engineer, if the team has an active one
    browser_tester: DeveloperEngine | None  # QA's engine for browser tests (built-in only)
    deploys: DeployService | None  # DevOps, when the team has one and VERCEL_TOKEN is set
    qa_name: str
    engine: DeveloperEngine  # the developer
    sandboxes: SandboxProvider


def build_team_runtime(settings: Settings) -> TeamRuntime:
    template = TeamService(load_templates()).get_template(settings.team_template)
    cto, developer, pm = template.role("cto"), template.role("developer"), template.role("pm")
    engine, sandboxes = build_engine(settings, developer)
    return TeamRuntime(
        template=template,
        planner=build_provider(settings, cto.model),
        planner_instructions=cto.instructions,
        review_instructions=cto.review_instructions,
        developer_names=developer.display_names,
        max_developers=developer.max_count,
        specialties=developer.specialty_of(),
        specialty_instructions={s.id: s.instructions for s in developer.specialties},
        approval_policy=template.approval,
        pm=build_provider(settings, pm.model),
        pm_instructions=pm.instructions,
        security=SecurityReview() if _active(template, "security") else None,
        browser_tester=_browser_tester(settings, template),
        deploys=(
            DeployService(VercelDeployTarget(settings.vercel_token, settings.vercel_team))
            if _active(template, "devops") and settings.vercel_token
            else None
        ),
        qa_name=template.role("qa").display_names[0],
        engine=engine,
        sandboxes=sandboxes,
    )


def _browser_tester(settings: Settings, template: TeamTemplate) -> DeveloperEngine | None:
    """QA's engine for browser tests: the built-in engine with QA's role (tools, instructions,
    steps). Not with OpenHands yet (see docs/10-gaps.md)."""
    if settings.developer_engine != "builtin":
        return None
    from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
    from app.features.events.schemas import Actor

    qa = template.role("qa")
    return ToolLoopEngine(
        build_provider(settings, qa.model),
        max_steps=qa.max_steps or settings.builtin_max_steps,
        tools=qa.tools,
        instructions=qa.instructions,
        actor=Actor.QA,
    )


def _active(template: TeamTemplate, role_id: str) -> bool:
    return any(r.id == role_id and r.active for r in template.roles)


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
            approval_policy=team.approval_policy,
            security=team.security,
            specialties=team.specialties,
            specialty_instructions=team.specialty_instructions,
            browser_tester=team.browser_tester,
            qa_name=team.qa_name,
            deploys=team.deploys,
            repos=RepoService(
                GitHubRepoHost(settings.github_token),
                GraphifyCodeGraph() if settings.code_graph else None,
            ),
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
    if settings.code_graph and "explain_symbol" not in tools:
        tools.append("explain_symbol")
    from app.features.integrations.service import tool_sources

    builtin = ToolLoopEngine(
        build_provider(settings, model),
        max_steps=(role.max_steps if role and role.max_steps else settings.builtin_max_steps),
        tools=tools,
        instructions=(role.instructions if role and role.instructions else SYSTEM_PROMPT),
        tool_sources=tool_sources(role.mcp) if role else [],
        existing_project_max_steps=role.existing_project_max_steps if role else None,
    )
    return builtin, DockerSandboxProvider(settings.sandbox_image)
