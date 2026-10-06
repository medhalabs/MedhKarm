"""Share links: the owner turns one on and off; the public sees only a whitelisted view."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_error_handlers
from app.features.artifacts.memory_repository import InMemoryArtifactRepository
from app.features.artifacts.service import ArtifactService
from app.features.auth.tests.helpers import OTHER_COMPANY, sign_in
from app.features.events.schemas import Actor, Event, EventType
from app.features.runs.dependencies import get_run_service
from app.features.runs.exceptions import RunNotFoundError
from app.features.runs.schemas import Run, RunStatus
from app.features.shares.dependencies import get_share_service, public_views
from app.features.shares.exceptions import ShareNotFoundError
from app.features.shares.memory_repository import InMemoryShareRepository
from app.features.shares.router import owner, public
from app.features.shares.schemas import PublicMember
from app.features.shares.service import ShareService, live_url, public_events, stats, title_of

T0 = datetime(2026, 10, 7, 10, 0, tzinfo=UTC)
SECRET = "SECRET-CLIENT-NAME"
REQUEST = f"# A coffee shop app\nFor {SECRET}, payments with key sk-live-123 please"


def run(status: RunStatus = RunStatus.RELEASED) -> Run:
    return Run(
        id="r1",
        company_id="c1",
        request=REQUEST,
        test_command="",
        status=status,
        created_at=T0,
        updated_at=T0,
    )


class Runs:
    async def owned(self, run_id: str, company_id: str) -> Run:
        if (run_id, company_id) != ("r1", "c1"):
            raise RunNotFoundError(f"No run {run_id}")
        return run()

    async def get(self, run_id: str) -> Run:
        return run()


class Events:
    def __init__(self, events: list[Event]) -> None:
        self.events = events

    async def list_for_run(self, run_id: str, after_id: int = 0, limit: int = 500) -> list[Event]:
        return self.events


class Roster:
    def members(self) -> list[PublicMember]:
        return [PublicMember(role="cto", title="CTO", name="Kabir")]


def event(
    id_: int,
    type_: EventType,
    summary: str,
    data: dict[str, Any] | None = None,
    actor: Actor = Actor.CTO,
    minutes: int = 0,
) -> Event:
    return Event(
        id=id_,
        run_id="r1",
        actor=actor,
        type=type_,
        summary=summary,
        data=data or {},
        tokens=500,
        occurred_at=T0 + timedelta(minutes=minutes),
    )


LOG = [
    event(1, EventType.RUN_STARTED, f"Asked for: {REQUEST}", actor=Actor.FOUNDER),
    event(2, EventType.CODEBASE_MAPPED, "Read the project", {"map": f"{SECRET} files"}),
    event(
        3,
        EventType.PLAN_CREATED,
        "Split the work into 1 task for Isha",
        {
            "plan": "secret plan",
            "tasks": [{"id": "t1", "title": "Menu page", "owner": "Isha", "notes": SECRET}],
        },
    ),
    event(
        4,
        EventType.TASK_ASSIGNED,
        "Assigned “Menu page” to Isha",
        {"task_id": "t1", "member": "Isha", "title": "Menu page"},
    ),
    event(5, EventType.TOOL_USED, f"Wrote {SECRET}.py", actor=Actor.DEVELOPER),
    event(6, EventType.MODEL_USED, "Thought about the next step", actor=Actor.DEVELOPER),
    event(
        7,
        EventType.WORK_FINISHED,
        "Isha: built the menu page",
        {"task_id": "t1", "member": "Isha", "files_changed": [f"{SECRET}.py"]},
        Actor.DEVELOPER,
        2,
    ),
    event(8, EventType.MESSAGE_POSTED, f"You wrote: {SECRET}", actor=Actor.FOUNDER),
    event(
        9,
        EventType.CHECK_FINISHED,
        "Checks passed (tests)",
        {"passed": True, "output": f"{SECRET} output"},
        Actor.QA,
        3,
    ),
    event(
        10,
        EventType.SECURITY_FINISHED,
        "No security problems found",
        {"blocking": 0, "warnings": 0},
        Actor.SECURITY,
        4,
    ),
    event(
        11,
        EventType.DEPLOY_FINISHED,
        "Preview ready: https://p.vercel.app",
        {"url": "https://p.vercel.app"},
        Actor.DEVOPS,
        5,
    ),
    event(
        12,
        EventType.APPROVAL_REQUESTED,
        f"Waiting for your approval: {SECRET}",
        {"gate": {"summary": SECRET}},
    ),
    event(
        13,
        EventType.APPROVAL_DECIDED,
        f"Approved the release: {SECRET}",
        {"approved": True, "feedback": SECRET},
        Actor.FOUNDER,
        6,
    ),
    event(
        14,
        EventType.CHANGES_DELIVERED,
        "Opened a pull request: https://github.com/me/private-repo/pull/1",
        {"pull_request_url": "https://github.com/me/private-repo/pull/1"},
        Actor.DEVOPS,
        7,
    ),
    event(15, EventType.RUN_FINISHED, "Released", {"status": "released"}, Actor.SYSTEM, 8),
]


def make(
    events: list[Event] | None = None,
) -> tuple[ShareService, InMemoryShareRepository, InMemoryArtifactRepository]:
    shares, artifacts = InMemoryShareRepository(), InMemoryArtifactRepository()
    tokens = iter(f"token-{n}" for n in range(1, 10))
    service = ShareService(
        shares,
        Runs(),
        Events(LOG if events is None else events),
        ArtifactService(artifacts),
        Roster(),
        lambda: next(tokens),
    )
    return service, shares, artifacts


def test_the_title_is_the_first_line_and_nothing_more_of_the_request() -> None:
    assert title_of(run()) == "A coffee shop app"
    assert len(title_of(run().model_copy(update={"request": "x" * 400}))) <= 120


def test_only_the_whitelisted_steps_are_shown_and_nothing_private_in_them() -> None:
    shown = public_events(LOG, "tok", "A coffee shop app")

    assert [e.id for e in shown] == [1, 3, 4, 7, 9, 10, 11, 12, 13, 15]
    everything = " ".join(e.model_dump_json() for e in shown)
    for private in (SECRET, "sk-live", "private-repo", "secret plan", "r1"):
        assert private not in everything
    assert shown[0].summary == "Asked for: A coffee shop app"
    assert shown[0].run_id == "tok"  # the token stands in for the run's id
    assert [e.summary for e in shown if e.type == "approval.decided"] == [
        "The founder approved the release"
    ]
    plan = next(e for e in shown if e.type == "plan.created")
    assert plan.data == {"tasks": [{"id": "t1", "title": "Menu page", "owner": "Isha"}]}
    assert all(e.tokens == 0 for e in shown)


def test_a_rejection_is_shown_without_the_founders_words() -> None:
    log = [
        event(
            1,
            EventType.APPROVAL_DECIDED,
            f"Did not approve: {SECRET}",
            {"approved": False, "feedback": SECRET},
        )
    ]
    [shown] = public_events(log, "tok", "x")
    assert shown.summary == "The release was not approved" and SECRET not in shown.model_dump_json()


def test_facts_and_the_live_address() -> None:
    result = stats(LOG)
    assert (result.tasks, result.minutes, result.checks_passed) == (1, 8, True)
    assert result.security_clean and not result.docs_updated
    assert live_url(LOG) == "https://p.vercel.app"
    assert (
        live_url([event(1, EventType.DEPLOY_FINISHED, "Live at http://x", {"url": "http://x"})])
        == ""
    )
    assert live_url([]) == ""


async def test_the_owner_turns_the_link_on_off_and_only_for_their_own_run() -> None:
    service, shares, _ = make()
    first = await service.create("c1", "r1")
    assert first.token == "token-1"
    assert (await service.create("c1", "r1")).token == "token-1"  # the same link
    assert (await service.get("c1", "r1")) is not None

    with pytest.raises(RunNotFoundError):
        await service.create("c2", "r1")
    with pytest.raises(RunNotFoundError):
        await service.revoke("c2", "r1")

    await service.revoke("c1", "r1")
    assert await service.get("c1", "r1") is None and shares.shares == {}
    with pytest.raises(ShareNotFoundError):
        await service.public("token-1")  # the old link is dead
    assert (await service.create("c1", "r1")).token == "token-2"  # a new link, a new token


async def test_the_public_view_counts_views_and_knows_about_the_demo() -> None:
    service, shares, artifacts = make()
    share = await service.create("c1", "r1")

    page = await service.public(share.token)
    assert (page.title, page.status, page.has_demo) == ("A coffee shop app", "released", False)
    assert page.team[0].name == "Kabir" and page.live_url == "https://p.vercel.app"
    assert (await shares.by_token(share.token)).views == 1  # type: ignore[union-attr]
    with pytest.raises(ShareNotFoundError):
        await service.demo(share.token)

    await ArtifactService(artifacts).save("r1", "demo", "v.webm", "video/webm", b"video-bytes")
    assert (await service.public(share.token)).has_demo
    assert (await service.demo(share.token)).data == b"video-bytes"


def apps(who: object = None) -> tuple[TestClient, TestClient]:
    """The same service as a signed-in founder, and as a stranger with no token at all."""
    service, _, artifacts = make()
    asyncio.run(
        ArtifactService(artifacts).save("r1", "demo", "v.webm", "video/webm", bytes(range(50)))
    )

    def build(signed_in: bool) -> TestClient:
        app = FastAPI()
        register_error_handlers(app)
        app.include_router(owner)
        app.include_router(public)
        app.dependency_overrides[get_share_service] = lambda: service
        app.dependency_overrides[get_run_service] = lambda: Runs()
        if signed_in:
            sign_in(app, who) if who else sign_in(app)  # type: ignore[arg-type]
        return TestClient(app)

    return build(True), build(False)


def test_over_http_the_public_needs_no_sign_in_and_the_owner_does() -> None:
    api, stranger = apps()
    link = api.post("/runs/r1/share").json()
    assert api.get("/runs/r1/share").json()["token"] == link["token"]

    page = stranger.get(f"/public/shares/{link['token']}")
    assert page.status_code == 200 and page.json()["title"] == "A coffee shop app"
    part = stranger.get(f"/public/shares/{link['token']}/demo", headers={"Range": "bytes=0-9"})
    assert part.status_code == 206 and part.content == bytes(range(10))
    assert stranger.post("/runs/r1/share").status_code == 401  # making a link needs sign-in
    assert stranger.delete("/runs/r1/share").status_code == 401

    assert api.delete("/runs/r1/share").status_code == 204
    gone = stranger.get(f"/public/shares/{link['token']}")
    assert gone.json()["error"]["code"] == "share_not_found"


def test_another_company_cannot_share_or_stop_your_run() -> None:
    api, _ = apps(OTHER_COMPANY)
    assert api.post("/runs/r1/share").status_code == 404
    assert api.delete("/runs/r1/share").status_code == 404


def test_public_views_are_rate_limited_per_address() -> None:
    public_views._hits.clear()
    api, _ = apps()
    token = api.post("/runs/r1/share").json()["token"]
    codes = [api.get(f"/public/shares/{token}").status_code for _ in range(62)]
    assert codes[:60] == [200] * 60 and codes[60:] == [429, 429]
    public_views._hits.clear()
