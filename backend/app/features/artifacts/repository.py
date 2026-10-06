"""ArtifactRepository on Postgres. The bytes are loaded only when a file is served."""

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import defer

from app.features.artifacts.models import ArtifactRow
from app.features.artifacts.schemas import Artifact, Content


class SqlArtifactRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def add(
        self, run_id: str, kind: str, name: str, content_type: str, data: bytes
    ) -> Artifact:
        statement = (
            insert(ArtifactRow)
            .values(
                run_id=run_id,
                kind=kind,
                name=name,
                content_type=content_type,
                size=len(data),
                data=data,
            )
            .returning(ArtifactRow.id, ArtifactRow.created_at)
        )
        async with self._sessions() as session, session.begin():
            artifact_id, created_at = (await session.execute(statement)).one()
        return Artifact(
            id=artifact_id,
            run_id=run_id,
            kind=kind,
            name=name,
            content_type=content_type,
            size=len(data),
            created_at=created_at,
        )

    async def for_run(self, run_id: str, kind: str | None = None) -> list[Artifact]:
        statement = (
            select(ArtifactRow).options(defer(ArtifactRow.data)).where(ArtifactRow.run_id == run_id)
        )  # the bytes stay in the database until a file is played
        if kind:
            statement = statement.where(ArtifactRow.kind == kind)
        async with self._sessions() as session:
            rows = (await session.scalars(statement.order_by(ArtifactRow.id.desc()))).all()
            return [_to_artifact(r) for r in rows]

    async def content(self, run_id: str, artifact_id: int) -> Content | None:
        statement = select(ArtifactRow).where(
            ArtifactRow.run_id == run_id, ArtifactRow.id == artifact_id
        )
        async with self._sessions() as session:
            row = (await session.scalars(statement)).first()
            if row is None:
                return None
            return Content(artifact=_to_artifact(row), data=bytes(row.data))


def _to_artifact(row: ArtifactRow) -> Artifact:
    return Artifact(
        id=row.id,
        run_id=row.run_id,
        kind=row.kind,
        name=row.name,
        content_type=row.content_type,
        size=row.size,
        created_at=row.created_at,
    )
