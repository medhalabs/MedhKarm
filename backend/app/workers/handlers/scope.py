"""Runs a job as the company whose work it is, so every model call inside uses that founder's
own models and keys (app/core/tenant.py, features/model_settings)."""

from collections.abc import Awaitable, Callable
from typing import Any

from app.core.tenant import company_scope
from app.features.jobs.interfaces import JobHandler

CompanyOf = Callable[[dict[str, Any]], Awaitable[str | None]]


class CompanyScoped:
    def __init__(self, inner: JobHandler, company_of: CompanyOf) -> None:
        self._inner = inner
        self._company_of = company_of

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        with company_scope(await self._company_of(payload)):
            return await self._inner.run(payload)

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        with company_scope(await self._company_of(payload)):
            await self._inner.give_up(payload, error)
