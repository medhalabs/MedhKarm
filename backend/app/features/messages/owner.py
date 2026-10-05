"""ThreadOwner from the runs and projects services: a thread is the company's when its run or
project is."""

from typing import Any, Protocol

from app.core.errors import NotFoundError
from app.features.messages.schemas import ThreadKind


class OwnedLookup(Protocol):
    async def owned(self, record_id: str, company_id: str) -> Any: ...


class ServiceOwner:
    def __init__(self, runs: OwnedLookup, projects: OwnedLookup) -> None:
        self._lookups = {ThreadKind.RUN: runs, ThreadKind.PROJECT: projects}

    async def owns(self, company_id: str, thread: ThreadKind, thread_id: str) -> bool:
        try:
            await self._lookups[thread].owned(thread_id, company_id)
        except NotFoundError:
            return False
        return True
