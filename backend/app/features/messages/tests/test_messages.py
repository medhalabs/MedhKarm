"""Messages: only on your own runs and projects; agents reply in role; the founder's messages
reach the team's briefs and the PM's plan."""

from typing import Any

import pytest

from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.jobs.stores.memory_queue import InMemoryJobQueue
from app.features.messages.exceptions import ThreadNotFoundError
from app.features.messages.memory_repository import InMemoryMessageRepository
from app.features.messages.replier import AgentReplier, Persona
from app.features.messages.schemas import NewMessage, ThreadKind
from app.features.messages.service import REPLY_JOB, MessageService
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, TokenUsage


class Owner:
    async def owns(self, company_id: str, thread: ThreadKind, thread_id: str) -> bool:
        return company_id == "c1"


class Context:
    async def describe(self, kind: ThreadKind, thread_id: str) -> str:
        return "Run request: a feedback wall. Latest: Arjun is building the home page."


def setup() -> tuple[
    MessageService, InMemoryMessageRepository, InMemoryJobQueue, InMemoryEventStore
]:
    repo, jobs, events = InMemoryMessageRepository(), InMemoryJobQueue(), InMemoryEventStore()
    return MessageService(repo, Owner(), jobs, events), repo, jobs, events


async def test_posting_saves_queues_a_reply_and_logs_it_on_the_run() -> None:
    service, _, jobs, events = setup()

    message = await service.post(
        "c1", NewMessage(run_id="r1", to="cto", body="Use a green button, please")
    )

    assert (message.author, message.name, message.to) == ("founder", "You", "cto")
    assert [(j.kind, j.payload) for j in jobs.jobs] == [(REPLY_JOB, {"message_id": message.id})]
    assert events.events[-1].summary == "You wrote: Use a green button, please"
    assert await service.for_run("r1") == ["Use a green button, please"]
    with pytest.raises(ThreadNotFoundError):
        await service.post("c2", NewMessage(run_id="r1", body="hi"))
    with pytest.raises(ThreadNotFoundError):
        await service.thread("c2", ThreadKind.RUN, "r1")


def test_a_message_is_about_one_run_or_one_project() -> None:
    with pytest.raises(ValueError):
        NewMessage(body="hi")
    with pytest.raises(ValueError):
        NewMessage(run_id="r1", project_id="p1", body="hi")


async def test_the_agent_replies_in_role_once() -> None:
    service, repo, _, events = setup()
    message = await service.post("c1", NewMessage(run_id="r1", to="cto", body="How is it going?"))
    llm = ScriptedLLMProvider(
        [LLMResponse(content="Arjun is on the home page now.", usage=TokenUsage(prompt_tokens=50))]
    )
    replier = AgentReplier(
        repo,
        lambda role: llm,
        {"cto": Persona("cto", "Kabir", "CTO"), "pm": Persona("pm", "Mira", "Product Manager")},
        Context(),
        events,
    )

    reply = await replier.reply(message.id)
    again = await replier.reply(message.id)  # a retried job doesn't answer twice

    assert reply is not None and again is not None and again.id == reply.id
    assert (reply.author, reply.name, reply.to) == ("cto", "Kabir", "founder")
    prompt: Any = llm.calls[0]
    assert "You are Kabir, the CTO" in prompt[0]["content"]
    assert "Arjun is building the home page" in prompt[1]["content"]
    assert events.events[-1].summary == "Kabir: Arjun is on the home page now."
    assert await service.for_run("r1") == ["How is it going?"]  # replies aren't instructions
