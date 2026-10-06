from app.core.database import session_factory
from app.features.artifacts.repository import SqlArtifactRepository
from app.features.artifacts.service import ArtifactService


def get_artifact_service() -> ArtifactService:
    return ArtifactService(SqlArtifactRepository(session_factory))
