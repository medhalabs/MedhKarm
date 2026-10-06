"""A run's files: list them, and play or download one (with byte ranges, for video)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response

from app.features.artifacts.dependencies import get_artifact_service
from app.features.artifacts.schemas import Artifact
from app.features.artifacts.service import ArtifactService, byte_range
from app.features.runs.dependencies import owned_run

router = APIRouter(
    prefix="/runs/{run_id}/artifacts", tags=["artifacts"], dependencies=[Depends(owned_run)]
)
Service = Annotated[ArtifactService, Depends(get_artifact_service)]


@router.get("", response_model=list[Artifact])
async def list_artifacts(run_id: str, service: Service, kind: str | None = None) -> list[Artifact]:
    return await service.list(run_id, kind)


@router.get("/{artifact_id}")
async def get_artifact(
    run_id: str,
    artifact_id: int,
    service: Service,
    range: Annotated[str | None, Header()] = None,
) -> Response:
    found = await service.content(run_id, artifact_id)
    size = len(found.data)
    headers = {"Accept-Ranges": "bytes", "Cache-Control": "private, max-age=3600"}
    wanted = byte_range(range, size)
    if wanted is not None:
        start, end = wanted
        return Response(
            found.data[start : end + 1],
            status_code=206,
            media_type=found.artifact.content_type,
            headers={**headers, "Content-Range": f"bytes {start}-{end}/{size}"},
        )
    return Response(found.data, media_type=found.artifact.content_type, headers=headers)
