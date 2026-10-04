from typing import Any, Protocol

from app.features.repos.schemas import NewRepo, RepoSource
from app.features.runs.schemas import Run, RunStatus
from app.features.starters.schemas import StackChoice


class RunRepository(Protocol):
    async def create(
        self,
        run_id: str,
        request: str,
        test_command: str,
        repo: RepoSource | None = None,
        new_repo: NewRepo | None = None,
        stack: StackChoice | None = None,
        company_id: str | None = None,
    ) -> Run: ...

    async def get(self, run_id: str) -> Run | None: ...

    async def list(self, limit: int = 50, company_id: str | None = None) -> list[Run]:
        """Newest first; only the company's runs when `company_id` is given."""
        ...

    async def ids_for(self, company_id: str) -> set[str]: ...

    async def adopt_unowned(self, company_id: str) -> int:
        """Gives runs without a company to this one; how many."""
        ...

    async def set_status(
        self,
        run_id: str,
        status: RunStatus,
        gate: dict[str, Any] | None = None,
        error: str | None = None,
        delivery: dict[str, Any] | None = None,
        deployment: dict[str, Any] | None = None,
    ) -> None:
        """`delivery` is kept when not given."""
        ...

    async def transition(self, run_id: str, from_status: RunStatus, to_status: RunStatus) -> bool:
        """Change status only if it is still `from_status` (one approval wins a double click)."""
        ...
