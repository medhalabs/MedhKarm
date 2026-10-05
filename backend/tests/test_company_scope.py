import asyncio
from typing import Any

from app.core.tenant import current_company
from app.workers.handlers.scope import CompanyScoped


class Seen:
    def __init__(self) -> None:
        self.companies: list[str | None] = []

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        # Work started inside a job (LangGraph nodes, the cancel watcher) sees the company too.
        async def deep() -> str | None:
            return current_company.get()

        self.companies.append(await asyncio.ensure_future(deep()))
        return None

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        self.companies.append(current_company.get())


async def test_a_job_runs_as_its_company_and_only_inside() -> None:
    async def company_of(payload: dict[str, Any]) -> str | None:
        return {"r1": "company-a"}.get(payload["run_id"])

    inner = Seen()
    handler = CompanyScoped(inner, company_of)
    await handler.run({"run_id": "r1"})
    await handler.give_up({"run_id": "r1"}, "boom")
    await handler.run({"run_id": "unknown"})
    assert inner.companies == ["company-a", "company-a", None]
    assert current_company.get() is None
