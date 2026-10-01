"""RunRepository in memory, for tests."""

from datetime import UTC, datetime
from typing import Any

from app.features.repos.schemas import RepoSource
from app.features.runs.schemas import Run, RunStatus


class InMemoryRunRepository:
    def __init__(self) -> None:
        self.runs: dict[str, Run] = {}

    async def create(
        self, run_id: str, request: str, test_command: str, repo: RepoSource | None = None
    ) -> Run:
        now = datetime.now(UTC)
        run = Run(
            id=run_id,
            request=request,
            test_command=test_command,
            repo=repo,
            status=RunStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )
        self.runs[run_id] = run
        return run.model_copy()

    async def get(self, run_id: str) -> Run | None:
        run = self.runs.get(run_id)
        return run.model_copy() if run else None

    async def list(self, limit: int = 50) -> list[Run]:
        newest = sorted(self.runs.values(), key=lambda r: r.created_at, reverse=True)
        return [r.model_copy() for r in newest[:limit]]

    async def set_status(
        self,
        run_id: str,
        status: RunStatus,
        gate: dict[str, Any] | None = None,
        error: str | None = None,
        delivery: dict[str, Any] | None = None,
    ) -> None:
        run = self.runs[run_id]
        run.status, run.gate, run.error = status, gate, error
        if delivery is not None:
            run.delivery = delivery
        run.updated_at = datetime.now(UTC)

    async def transition(self, run_id: str, from_status: RunStatus, to_status: RunStatus) -> bool:
        run = self.runs.get(run_id)
        if not run or run.status != from_status:
            return False
        run.status, run.updated_at = to_status, datetime.now(UTC)
        return True
