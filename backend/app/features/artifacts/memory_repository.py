"""ArtifactRepository in memory, for tests."""

from datetime import UTC, datetime

from app.features.artifacts.schemas import Artifact, Content


class InMemoryArtifactRepository:
    def __init__(self) -> None:
        self.items: list[Content] = []

    async def add(
        self, run_id: str, kind: str, name: str, content_type: str, data: bytes
    ) -> Artifact:
        artifact = Artifact(
            id=len(self.items) + 1,
            run_id=run_id,
            kind=kind,
            name=name,
            content_type=content_type,
            size=len(data),
            created_at=datetime.now(UTC),
        )
        self.items.append(Content(artifact=artifact, data=data))
        return artifact

    async def for_run(self, run_id: str, kind: str | None = None) -> list[Artifact]:
        found = [
            c.artifact
            for c in self.items
            if c.artifact.run_id == run_id and (kind is None or c.artifact.kind == kind)
        ]
        return list(reversed(found))

    async def content(self, run_id: str, artifact_id: int) -> Content | None:
        return next(
            (c for c in self.items if c.artifact.run_id == run_id and c.artifact.id == artifact_id),
            None,
        )
