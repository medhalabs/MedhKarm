from typing import Any, Protocol

from app.features.runs.schemas import Run, RunStatus


class RunRepository(Protocol):
    async def create(self, run_id: str, request: str, test_command: str) -> Run: ...

    async def get(self, run_id: str) -> Run | None: ...

    async def list(self, limit: int = 50) -> list[Run]:
        """Newest first."""
        ...

    async def set_status(
        self,
        run_id: str,
        status: RunStatus,
        gate: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None: ...

    async def transition(self, run_id: str, from_status: RunStatus, to_status: RunStatus) -> bool:
        """Change status only if it is still `from_status` (one approval wins a double click)."""
        ...
