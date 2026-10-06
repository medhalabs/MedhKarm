"""Run files: stored with a size cap, served with byte ranges so a browser can play and skip
through a video, and only to the run's own company."""

import asyncio
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_error_handlers
from app.features.artifacts.dependencies import get_artifact_service
from app.features.artifacts.exceptions import ArtifactTooLargeError, RangeNotSatisfiableError
from app.features.artifacts.memory_repository import InMemoryArtifactRepository
from app.features.artifacts.router import router
from app.features.artifacts.service import ArtifactService, byte_range
from app.features.auth.tests.helpers import OTHER_COMPANY, sign_in
from app.features.runs.dependencies import get_run_service
from app.features.runs.exceptions import RunNotFoundError
from app.features.runs.schemas import Run, RunStatus

VIDEO = bytes(range(100))


class Runs:
    """Run r1 belongs to company c1."""

    async def owned(self, run_id: str, company_id: str) -> Run:
        if (run_id, company_id) != ("r1", "c1"):
            raise RunNotFoundError(f"No run {run_id}")
        now = datetime.now(UTC)
        return Run(
            id="r1",
            company_id="c1",
            request="x",
            test_command="",
            status=RunStatus.RUNNING,
            created_at=now,
            updated_at=now,
        )


def api(who: object = None) -> tuple[TestClient, ArtifactService]:
    service = ArtifactService(InMemoryArtifactRepository(), max_bytes=1000)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_artifact_service] = lambda: service
    app.dependency_overrides[get_run_service] = lambda: Runs()
    sign_in(app, who) if who else sign_in(app)  # type: ignore[arg-type]
    return TestClient(app), service


def test_ranges_are_read_the_way_browsers_ask() -> None:
    assert byte_range(None, 100) is None
    assert byte_range("bytes=0-", 100) == (0, 99)
    assert byte_range("bytes=10-19", 100) == (10, 19)
    assert byte_range("bytes=90-500", 100) == (90, 99)  # past the end: up to the end
    assert byte_range("bytes=-10", 100) == (90, 99)  # the last ten bytes
    assert byte_range("bytes=-500", 100) == (0, 99)
    assert byte_range("nonsense", 100) is None
    assert byte_range("bytes=0-5", 0) is None
    with pytest.raises(RangeNotSatisfiableError):
        byte_range("bytes=100-", 100)
    with pytest.raises(RangeNotSatisfiableError):
        byte_range("bytes=50-10", 100)


def test_a_video_is_listed_and_played_whole_or_in_parts() -> None:
    client, service = api()
    saved = asyncio.run(service.save("r1", "demo", "browser-test.webm", "video/webm", VIDEO))

    [listed] = client.get("/runs/r1/artifacts?kind=demo").json()
    assert (listed["id"], listed["name"], listed["size"]) == (saved.id, "browser-test.webm", 100)
    assert client.get("/runs/r1/artifacts?kind=other").json() == []

    whole = client.get(f"/runs/r1/artifacts/{saved.id}")
    assert whole.content == VIDEO and whole.headers["content-type"] == "video/webm"
    assert whole.headers["accept-ranges"] == "bytes"

    part = client.get(f"/runs/r1/artifacts/{saved.id}", headers={"Range": "bytes=10-19"})
    assert part.status_code == 206 and part.content == VIDEO[10:20]
    assert part.headers["content-range"] == "bytes 10-19/100"

    beyond = client.get(f"/runs/r1/artifacts/{saved.id}", headers={"Range": "bytes=500-"})
    assert beyond.status_code == 416


def test_a_file_that_doesnt_exist_or_isnt_yours_is_not_found() -> None:
    client, service = api()
    saved = asyncio.run(service.save("r1", "demo", "v.webm", "video/webm", VIDEO))
    assert client.get("/runs/r1/artifacts/999").json()["error"]["code"] == "artifact_not_found"

    other, _ = api(OTHER_COMPANY)
    other.app.dependency_overrides[get_artifact_service] = lambda: service  # type: ignore[attr-defined]
    assert other.get(f"/runs/r1/artifacts/{saved.id}").status_code == 404
    assert other.get("/runs/r1/artifacts").status_code == 404


def test_files_over_the_limit_are_refused() -> None:
    _, service = api()
    with pytest.raises(ArtifactTooLargeError):
        asyncio.run(service.save("r1", "demo", "big.webm", "video/webm", b"x" * 1001))
