"""Sending updates: the providers' requests, one failing channel not stopping the other, and
which companies are due."""

import json
from datetime import UTC, datetime

import httpx
import pytest

from app.features.notifications.exceptions import NotificationError
from app.features.notifications.memory_repository import InMemorySettingsRepository
from app.features.notifications.providers.meta_whatsapp import MetaWhatsApp, template_text
from app.features.notifications.providers.resend_email import ResendEmail
from app.features.notifications.schemas import Channel, NotificationSettings, Update
from app.features.notifications.service import NotificationService

UPDATE = Update(subject="Standup", text="Line one\nLine two", short="One line")


def mock(status: int, seen: list[httpx.Request]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json={"id": "x"})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_resend_sends_the_full_text() -> None:
    seen: list[httpx.Request] = []
    await ResendEmail("re_key", "MedhKarm <a@b.co>", mock(200, seen)).send("me@x.in", "Hi", "Body")

    body = json.loads(seen[0].content)
    assert seen[0].headers["Authorization"] == "Bearer re_key"
    assert (body["to"], body["subject"], body["text"]) == (["me@x.in"], "Hi", "Body")
    with pytest.raises(NotificationError):
        await ResendEmail("k", "a@b.co", mock(422, [])).send("me@x.in", "Hi", "Body")


async def test_whatsapp_uses_the_template_with_one_flat_variable() -> None:
    seen: list[httpx.Request] = []
    sender = MetaWhatsApp("token", "12345", "medhkarm_update", "en", mock(200, seen))

    await sender.send("+919876543210", "ignored", "Done 2\nBlocked 0")

    body = json.loads(seen[0].content)
    assert str(seen[0].url).endswith("/12345/messages")
    assert body["to"] == "919876543210" and body["template"]["name"] == "medhkarm_update"
    assert body["template"]["components"][0]["parameters"][0]["text"] == "Done 2 • Blocked 0"


def test_template_variables_follow_metas_rules() -> None:
    assert template_text("a\n\nb\tc     d") == "a • b • c   d"
    assert len(template_text("x" * 2000)) == 1000


class Fake:
    def __init__(self, channel: Channel, fail: bool = False) -> None:
        self.channel = channel
        self.fail = fail
        self.sent: list[tuple[str, str]] = []

    async def send(self, to: str, subject: str, text: str) -> None:
        if self.fail:
            raise NotificationError("provider down")
        self.sent.append((to, text))


async def test_each_channel_gets_its_shape_and_one_failure_doesnt_stop_the_other() -> None:
    email, whatsapp = Fake(Channel.EMAIL), Fake(Channel.WHATSAPP, fail=True)
    repo = InMemorySettingsRepository()
    service = NotificationService(repo, [email, whatsapp])
    await service.save("c1", NotificationSettings(email="Me@X.in", whatsapp="+91 98765 43210"))

    results = await service.deliver("c1", UPDATE)

    assert email.sent == [("me@x.in", "Line one\nLine two")]
    assert [(r.channel, r.ok, r.error) for r in results] == [
        (Channel.EMAIL, True, ""),
        (Channel.WHATSAPP, False, "provider down"),
    ]
    assert await service.deliver("nobody", UPDATE) == []  # opt-in: no settings, nothing sent


async def test_a_channel_without_server_keys_says_so() -> None:
    repo = InMemorySettingsRepository()
    service = NotificationService(repo, [])
    await repo.save("c1", NotificationSettings(whatsapp="+919876543210"))

    [result] = await service.deliver("c1", UPDATE)

    assert not result.ok and "isn't set up on the server" in result.error


def test_settings_check_email_and_phone() -> None:
    with pytest.raises(ValueError):
        NotificationSettings(email="nope")
    with pytest.raises(ValueError):
        NotificationSettings(whatsapp="98765 43210")  # no country code
    assert NotificationSettings(whatsapp="+91 (98765) 43210").whatsapp == "+919876543210"


async def test_whos_due_today_and_on_mondays() -> None:
    repo = InMemorySettingsRepository()
    service = NotificationService(repo, [], "Asia/Kolkata")
    await repo.save("early", NotificationSettings(email="a@b.co", standup_hour=8))
    await repo.save("late", NotificationSettings(email="c@d.co", standup_hour=18))
    await repo.save("off", NotificationSettings(email="e@f.co", standup_on=False, weekly_on=False))
    await repo.save("no-address", NotificationSettings())
    monday_10am_ist = datetime(2026, 10, 5, 4, 30, tzinfo=UTC)

    due = await service.due_standups(monday_10am_ist)
    weekly = await service.due_weekly(monday_10am_ist)
    tuesday = await service.due_weekly(datetime(2026, 10, 6, 4, 30, tzinfo=UTC))

    assert [c for c, _ in due] == ["early"]
    assert [c for c, _ in weekly] == ["early"] and tuesday == []
