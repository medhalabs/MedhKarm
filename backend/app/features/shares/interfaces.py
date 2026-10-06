from typing import Protocol

from app.features.artifacts.schemas import Artifact, Content
from app.features.events.schemas import Event
from app.features.runs.schemas import Run
from app.features.shares.schemas import PublicMember, Share


class ShareRepository(Protocol):
    async def create(self, token: str, run_id: str, company_id: str) -> Share: ...

    async def for_run(self, run_id: str) -> Share | None: ...

    async def by_token(self, token: str) -> Share | None: ...

    async def delete_for_run(self, run_id: str) -> None: ...

    async def count_view(self, token: str) -> None: ...


class RunReader(Protocol):
    async def owned(self, run_id: str, company_id: str) -> Run: ...

    async def get(self, run_id: str) -> Run: ...


class EventReader(Protocol):
    async def list_for_run(
        self, run_id: str, after_id: int = 0, limit: int = 500
    ) -> list[Event]: ...


class DemoReader(Protocol):
    async def list(self, run_id: str, kind: str | None = None) -> list[Artifact]: ...

    async def content(self, run_id: str, artifact_id: int) -> Content: ...


class Roster(Protocol):
    def members(self) -> list[PublicMember]: ...
