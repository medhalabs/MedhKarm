"""The intake: the CTO asks what's unclear, then hands over a brief the founder confirms."""

from typing import Any

from app.features.intake.schemas import About, Conversation, Turn
from app.features.intake.service import IntakeService, parse_brief
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall


def talk(*texts: str) -> Conversation:
    turns = [Turn(role="founder" if i % 2 == 0 else "agent", text=t) for i, t in enumerate(texts)]
    return Conversation(turns=turns)


def brief_call(**arguments: Any) -> LLMResponse:
    return LLMResponse(
        content="Great, here's the plan.",
        tool_calls=[ToolCall(id="b", name="submit_brief", arguments=arguments)],
    )


async def test_the_cto_asks_first_when_something_is_unclear() -> None:
    llm = ScriptedLLMProvider([LLMResponse(content="New project, or your existing repo?")])

    reply = await IntakeService(llm, "Kabir").turn(talk("A booking page for my yoga classes"))

    assert (reply.agent, reply.text, reply.brief) == (
        "Kabir",
        "New project, or your existing repo?",
        None,
    )
    sent: Any = llm.calls[0]
    assert "You are Kabir, the CTO" in sent[0]["content"]
    assert sent[1] == {"role": "user", "content": "A booking page for my yoga classes"}


async def test_the_brief_carries_the_answers_and_the_founders_choices() -> None:
    llm = ScriptedLLMProvider(
        [
            brief_call(
                request="A yoga booking page; students pay ₹499 per class with Stripe.",
                summary="New project: yoga bookings with Stripe payments.",
                create_repo=True,
                payments="Stripe",
                modules=["payments", "nonsense", 3],
                starter="yes",
            )
        ]
    )
    conversation = talk("A booking page for my yoga classes", "Payments?", "Yes, Stripe, ₹499")

    reply = await IntakeService(llm).turn(conversation)

    brief = reply.brief
    assert brief is not None and brief.request.endswith("with Stripe.")
    assert (brief.stack.payments, brief.stack.starter) == ("stripe", True)
    assert brief.stack.modules == ["payments", "nonsense"]
    assert brief.stack.frontend is None  # not chosen: the team picks
    sent: Any = llm.calls[0]
    assert [m["role"] for m in sent] == ["system", "user", "assistant", "user"]


async def test_a_sloppy_brief_still_carries_the_founders_words() -> None:
    llm = ScriptedLLMProvider([brief_call(summary="")])

    reply = await IntakeService(llm).turn(talk("Build a habit tracker, just start"))

    assert reply.brief is not None and reply.brief.request == "Build a habit tracker, just start"
    assert reply.text == "Great, here's the plan."


async def test_written_out_line_breaks_become_real_ones() -> None:
    llm = ScriptedLLMProvider([brief_call(request="Yoga bookings", summary="Line one./nLine two.")])

    reply = await IntakeService(llm).turn(talk("Yoga bookings", "Anything else?", "No"))

    assert reply.brief is not None and reply.brief.summary == "Line one.\nLine two."


async def test_mira_hands_over_a_project_to_plan() -> None:
    llm = ScriptedLLMProvider(
        [
            LLMResponse(
                content="Got it, here's the project.",
                tool_calls=[
                    ToolCall(
                        id="p",
                        name="submit_project",
                        arguments={
                            "name": "Yoga studio app",
                            "goal": "Students book classes and pay; I see bookings.",
                            "summary": "Bookings, Razorpay payments, an admin view.",
                            "payments": "razorpay",
                            "autopilot": True,
                            "daily_limit": 40,
                        },
                    )
                ],
            )
        ]
    )

    reply = await IntakeService(llm, "Mira").project_turn(
        talk("An app for my yoga studio", "Main features?", "Bookings and payments; plan it")
    )

    brief = reply.brief
    assert reply.agent == "Mira" and brief is not None
    assert (brief.name, brief.autopilot, brief.daily_limit) == ("Yoga studio app", True, 10)
    assert brief.stack.payments == "razorpay"
    sent: Any = llm.calls[0]
    assert "You are Mira, the product manager" in sent[0]["content"]


async def test_the_first_reply_asks_before_handing_over_a_brief() -> None:
    eager = LLMResponse(
        content="Here's the project.",
        tool_calls=[
            ToolCall(
                id="p",
                name="submit_project",
                arguments={"name": "Tuition app", "goal": "Parents see attendance and pay fees"},
            )
        ],
    )

    reply = await IntakeService(ScriptedLLMProvider([eager]), "Mira").project_turn(
        talk("An app for my tuition centre: parents see attendance and pay fees")
    )

    assert reply.brief is None
    assert "main things it must do first" in reply.text


async def test_a_full_spec_or_just_start_can_go_straight_to_a_brief() -> None:
    spec = "Build a landing page. " + "Details. " * 100
    for first in (spec, "A todo app, just start"):
        llm = ScriptedLLMProvider([brief_call(request=first, summary="ok")])
        reply = await IntakeService(llm).turn(talk(first))
        assert reply.brief is not None, first


async def test_a_change_to_a_live_project_is_about_that_project_and_says_how_big() -> None:
    call = brief_call(
        request="Add a tip option at checkout",
        summary="Tips of 10, 20 or 50 rupees",
        repo_url="https://github.com/someone/else",  # the model must not pick another project
        create_repo=True,
        scale="small",
    )
    llm = ScriptedLLMProvider([call])
    conversation = Conversation(
        turns=[Turn(role="founder", text="Add a tip option at checkout. Just do it.")],
        about=About(repo_url="https://github.com/me/coffee", name="Coffee shop orders"),
    )

    reply = await IntakeService(llm, "Kabir").turn(conversation)

    assert reply.brief is not None
    assert reply.brief.repo_url == "https://github.com/me/coffee"
    assert reply.brief.create_repo is False
    assert reply.brief.scale == "small"
    system: Any = llm.calls[0][0]["content"]
    assert "CHANGE" in system and "https://github.com/me/coffee (Coffee shop orders)" in system


def test_a_made_up_scale_is_ignored() -> None:
    call = brief_call(request="Do a thing", summary="s", scale="huge")
    brief = parse_brief(call, talk("Do a thing"))
    assert brief is not None and brief.scale is None


async def test_without_a_message_the_cto_still_says_what_he_thinks_of_a_changes_size() -> None:
    about = About(repo_url="https://github.com/me/coffee", name="Coffee")

    async def say(**arguments: Any) -> str:
        call = brief_call(request="Add a tip", summary="s", **arguments)
        call.content = ""
        conversation = Conversation(
            turns=[Turn(role="founder", text="Add a tip. Just do it.")], about=about
        )
        return (await IntakeService(ScriptedLLMProvider([call])).turn(conversation)).text

    assert "small change" in await say(scale="small")
    assert "bigger change" in await say(scale="big")
    assert "choose what happens next" in await say()
