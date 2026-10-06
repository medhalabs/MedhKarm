"""ShareRepository in memory, for tests."""

from datetime import UTC, datetime

from app.features.shares.schemas import Share


class InMemoryShareRepository:
    def __init__(self) -> None:
        self.shares: dict[str, Share] = {}

    async def create(self, token: str, run_id: str, company_id: str) -> Share:
        self.shares[token] = Share(token=token, run_id=run_id, created_at=datetime.now(UTC))
        return self.shares[token]

    async def for_run(self, run_id: str) -> Share | None:
        return next((s for s in self.shares.values() if s.run_id == run_id), None)

    async def by_token(self, token: str) -> Share | None:
        return self.shares.get(token)

    async def delete_for_run(self, run_id: str) -> None:
        self.shares = {t: s for t, s in self.shares.items() if s.run_id != run_id}

    async def count_view(self, token: str) -> None:
        share = self.shares[token]
        self.shares[token] = share.model_copy(update={"views": share.views + 1})
