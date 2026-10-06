"""BlueprintRepository in memory, for tests."""

from datetime import UTC, datetime

from app.features.blueprints.schemas import Blueprint, BlueprintStatus, Comment, Doc
from app.features.runs.schemas import StartRun


class InMemoryBlueprintRepository:
    def __init__(self) -> None:
        self.rows: dict[str, Blueprint] = {}

    async def create(
        self, blueprint_id: str, company_id: str, title: str, brief: StartRun
    ) -> Blueprint:
        now = datetime.now(UTC)
        self.rows[blueprint_id] = Blueprint(
            id=blueprint_id,
            company_id=company_id,
            title=title,
            brief=brief,
            status=BlueprintStatus.WRITING,
            created_at=now,
            updated_at=now,
        )
        return self.rows[blueprint_id]

    async def get(self, blueprint_id: str) -> Blueprint | None:
        return self.rows.get(blueprint_id)

    async def for_company(self, company_id: str, limit: int = 50) -> list[Blueprint]:
        mine = [b for b in self.rows.values() if b.company_id == company_id]
        return sorted(mine, key=lambda b: b.created_at, reverse=True)[:limit]

    async def for_run(self, run_id: str) -> Blueprint | None:
        return next((b for b in self.rows.values() if b.run_id == run_id), None)

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
    ) -> Blueprint:
        changes = {
            k: v
            for k, v in {
                "status": status,
                "docs": docs,
                "comments": comments,
                "progress": progress,
                "error": error,
                "run_id": run_id,
                "revision": revision,
                "updated_at": datetime.now(UTC),
            }.items()
            if v is not None
        }
        self.rows[blueprint_id] = self.rows[blueprint_id].model_copy(update=changes)
        return self.rows[blueprint_id]

    async def transition(
        self, blueprint_id: str, expected: BlueprintStatus, new: BlueprintStatus
    ) -> bool:
        if self.rows[blueprint_id].status != expected:
            return False
        await self.update(blueprint_id, status=new)
        return True
