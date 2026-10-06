import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.features.waitlist.dependencies import get_waitlist_service, joins
from app.features.waitlist.memory_repository import InMemoryWaitlistRepository
from app.features.waitlist.router import router
from app.features.waitlist.schemas import JoinWaitlist
from app.features.waitlist.service import WaitlistService


def body(email: str = "Asha@Example.com", **more: str) -> JoinWaitlist:
    return JoinWaitlist(email=email, **more)


async def test_joining_saves_the_person_and_counts_them() -> None:
    repo = InMemoryWaitlistRepository()
    service = WaitlistService(repo)

    joined = await service.join(body(name=" Asha ", building="A tuition app", source="share"))

    assert joined.count == 1
    [entry] = await service.export()
    assert (entry.email, entry.name, entry.building, entry.source) == (
        "asha@example.com",  # tidied
        "Asha",
        "A tuition app",
        "share",
    )


async def test_the_same_email_twice_is_one_entry_and_the_answer_is_the_same() -> None:
    service = WaitlistService(InMemoryWaitlistRepository())
    await service.join(body())
    again = await service.join(body("asha@example.com"))
    assert again.ok and again.count == 1  # nothing tells a stranger whether an email is on it


async def test_a_bot_that_fills_the_hidden_field_gets_a_friendly_answer_and_nothing_is_saved() -> (
    None
):
    service = WaitlistService(InMemoryWaitlistRepository())
    answer = await service.join(body("bot@spam.com", website="http://spam.example"))
    assert answer.ok and answer.count == 0
    assert await service.export() == []


async def test_inviting_marks_the_person() -> None:
    service = WaitlistService(InMemoryWaitlistRepository())
    await service.join(body())
    assert await service.invite(" ASHA@example.com ") is True
    assert (await service.export())[0].invited_at is not None
    assert await service.invite("nobody@example.com") is False


def test_a_bad_email_is_refused() -> None:
    for bad in ("", "nobody", "a@b", "a b@c.com"):
        with pytest.raises(ValueError):
            body(bad)


def test_the_public_api_joins_counts_limits_and_never_lists_emails() -> None:
    joins._hits.clear()
    service = WaitlistService(InMemoryWaitlistRepository())
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_waitlist_service] = lambda: service
    api = TestClient(app)

    ok = api.post("/public/waitlist", json={"email": "a@example.com", "building": "x"})
    assert ok.status_code == 200 and ok.json() == {"ok": True, "count": 1}
    assert api.get("/public/waitlist/count").json() == {"count": 1}
    assert api.post("/public/waitlist", json={"email": "nope"}).status_code == 422
    assert api.get("/public/waitlist").status_code in (404, 405)  # no way to list the emails

    codes = [
        api.post("/public/waitlist", json={"email": f"p{n}@example.com"}).status_code
        for n in range(6)
    ]
    assert codes[-1] == 429  # five an hour from one address (one was used above)
    joins._hits.clear()
