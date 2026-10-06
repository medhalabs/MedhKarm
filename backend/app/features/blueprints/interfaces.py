from typing import Protocol

from app.features.blueprints.schemas import Blueprint, BlueprintStatus, Comment, Doc
from app.features.runs.schemas import Run, StartRun


class BlueprintRepository(Protocol):
    async def create(
        self, blueprint_id: str, company_id: str, title: str, brief: StartRun
    ) -> Blueprint: ...

    async def get(self, blueprint_id: str) -> Blueprint | None: ...

    async def for_company(self, company_id: str, limit: int = 50) -> list[Blueprint]: ...

    async def for_run(self, run_id: str) -> Blueprint | None: ...

    async def update(
        self,
        blueprint_id: str,
        *,
        status: BlueprintStatus | None = None,
        docs: list[Doc] | None = None,
        comments: list[Comment] | None = None,
        progress: str | None = None,
        error: str | None = None,
        run_id: str | None = None,
        revision: int | None = None,
    ) -> Blueprint: ...

    async def transition(
        self, blueprint_id: str, expected: BlueprintStatus, new: BlueprintStatus
    ) -> bool:
        """Moves status only if it is still `expected`; False when someone got there first."""
        ...


class RunStarter(Protocol):
    """Starts the build once the founder approves (the runs service)."""

    async def start(self, body: StartRun, company_id: str | None = None) -> Run: ...
