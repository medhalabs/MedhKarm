"""Files a run produced for the founder (the demo video of QA's browser test), kept in Postgres
and served with byte ranges, which browsers need to play and skip through a video."""

import re

from app.features.artifacts.exceptions import (
    ArtifactNotFoundError,
    ArtifactTooLargeError,
    RangeNotSatisfiableError,
)
from app.features.artifacts.interfaces import ArtifactRepository
from app.features.artifacts.schemas import Artifact, Content

MAX_BYTES = 8 * 1024 * 1024  # a short browser-test video is well under this
RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


class ArtifactService:
    def __init__(self, artifacts: ArtifactRepository, max_bytes: int = MAX_BYTES) -> None:
        self._artifacts = artifacts
        self._max_bytes = max_bytes

    async def save(
        self, run_id: str, kind: str, name: str, content_type: str, data: bytes
    ) -> Artifact:
        if len(data) > self._max_bytes:
            raise ArtifactTooLargeError(
                f"{name} is {len(data)} bytes; the limit is {self._max_bytes}"
            )
        return await self._artifacts.add(run_id, kind, name, content_type, data)

    async def list(self, run_id: str, kind: str | None = None) -> list[Artifact]:
        return await self._artifacts.for_run(run_id, kind)

    async def content(self, run_id: str, artifact_id: int) -> Content:
        found = await self._artifacts.content(run_id, artifact_id)
        if found is None:
            raise ArtifactNotFoundError(f"No file {artifact_id} for run {run_id}")
        return found


def byte_range(header: str | None, size: int) -> tuple[int, int] | None:
    """The (first, last) bytes a `Range` header asks for; None: no range, send it all.
    Raises RangeNotSatisfiableError (416) when the range lies beyond the file."""
    if not header:
        return None
    match = RANGE.match(header.strip())
    if not match or size == 0:
        return None
    first, last = match.groups()
    if first == "" and last == "":
        return None
    if first == "":  # the last N bytes
        start = max(size - int(last), 0)
        return start, size - 1
    start = int(first)
    end = min(int(last), size - 1) if last else size - 1
    if start >= size or end < start:
        raise RangeNotSatisfiableError(f"The file has {size} bytes")
    return start, end
