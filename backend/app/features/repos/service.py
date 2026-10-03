"""Working on a founder's existing project: check it out, map it, install it, and hand the
finished work back as a pull request. The build workflow calls this; it never sees GitHub."""

from pydantic import BaseModel

from app.features.repos.interfaces import CodeGraph, RepoHost
from app.features.repos.mapper import map_codebase
from app.features.repos.schemas import (
    CodebaseMap,
    Delivery,
    DeliveryStatus,
    RepoSource,
    repo_name_for,
)
from app.features.sandbox.interfaces import Sandbox

SETUP_TIMEOUT = 600


class Checkout(BaseModel):
    """The project as the team found it."""

    commit: str = ""  # empty when there was no repository (a new project)
    map: CodebaseMap
    setup_ok: bool = True
    setup_output: str = ""


class RepoService:
    def __init__(self, host: RepoHost | None = None, graph: CodeGraph | None = None) -> None:
        self._host = host
        self._graph = graph

    async def checkout(self, sandbox: Sandbox, source: RepoSource | None) -> Checkout:
        """Clone `source` (unless already cloned: safe to repeat after a crash), map the
        workspace and install its dependencies. Without a source, only maps what's there."""
        commit = ""
        if source:
            if self._host is None:
                raise RuntimeError("No repository host configured")
            existing = await sandbox.run("git rev-parse HEAD")
            commit = (
                existing.output.strip() if existing.ok else await self._host.clone(source, sandbox)
            )
        codebase = await map_codebase(sandbox)
        if self._graph and not codebase.empty:
            codebase.graph = await self._graph.describe(sandbox)
        if not (source and codebase.setup_command):  # evals' projects come ready to run
            return Checkout(commit=commit, map=codebase)
        setup = await sandbox.run(codebase.setup_command, timeout_seconds=SETUP_TIMEOUT)
        return Checkout(
            commit=commit, map=codebase, setup_ok=setup.ok, setup_output=setup.output[-2000:]
        )

    async def deliver(
        self, sandbox: Sandbox, source: RepoSource, run_id: str, request: str, summary: str
    ) -> Delivery:
        if self._host is None:
            return Delivery(status=DeliveryStatus.SKIPPED, reason="No repository host configured")
        title = request.strip().splitlines()[0][:70] or f"MedhKarm run {run_id}"
        body = (
            f"{summary.strip()}\n\n**Asked for:**\n\n> "
            + request.strip().replace("\n", "\n> ")
            + f"\n\nBuilt and tested by the MedhKarm software team (run `{run_id}`); "
            "approved by you at the release gate."
        )
        return await self._host.deliver(source, sandbox, f"medhkarm/{run_id}", title, body)

    async def publish(
        self, sandbox: Sandbox, run_id: str, request: str, name: str | None = None
    ) -> Delivery:
        """A new project's released work goes to a new private repository."""
        if self._host is None:
            return Delivery(status=DeliveryStatus.SKIPPED, reason="No repository host configured")
        description = request.strip().splitlines()[0][:200] if request.strip() else ""
        return await self._host.publish(
            sandbox, name or repo_name_for(request, run_id), description
        )
