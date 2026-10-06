from typing import Protocol

from app.features.artifacts.schemas import Artifact, Content


class ArtifactRepository(Protocol):
    async def add(
        self, run_id: str, kind: str, name: str, content_type: str, data: bytes
    ) -> Artifact: ...

    async def for_run(self, run_id: str, kind: str | None = None) -> list[Artifact]:
        """Newest first, without the bytes."""
        ...

    async def content(self, run_id: str, artifact_id: int) -> Content | None: ...
