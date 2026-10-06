"""One turn of an intake conversation. Kabir (CTO) turns a request into a run's brief; Mira
(PM) turns a product idea into a project to plan. Each asks what's unclear, then hands over a
brief the founder confirms. The conversation lives in the browser; each turn sends it whole."""

import re
from typing import Any

from pydantic import ValidationError

from app.features.intake.prompt import (
    BRIEF_TOOL,
    CHANGE_PROMPT,
    FIRST_QUESTIONS,
    INTAKE_PROMPT,
    PROJECT_PROMPT,
    PROJECT_TOOL,
)
from app.features.intake.schemas import (
    Brief,
    Conversation,
    ProjectBrief,
    ProjectReply,
    Reply,
)
from app.features.models.interfaces import LLMProvider
from app.features.models.schemas import LLMResponse, ToolSpec
from app.features.starters.schemas import FIELDS, StackChoice

STARTERS = {"yes": True, "no": False}


class IntakeService:
    def __init__(self, llm: LLMProvider, agent: str = "Kabir") -> None:
        self._llm = llm
        self._agent = agent

    async def turn(self, conversation: Conversation) -> Reply:
        """The CTO's side: a run's brief."""
        about = conversation.about
        prompt = INTAKE_PROMPT + (
            CHANGE_PROMPT.format(
                repo_url=about.repo_url, name=f" ({about.name})" if about.name else ""
            )
            if about
            else ""
        )
        response = await self._ask(prompt, BRIEF_TOOL, conversation)
        brief = parse_brief(response, conversation)
        if brief and about:  # a change to this project, whatever the model wrote
            brief.repo_url, brief.create_repo = about.repo_url, False
        if brief and too_soon(conversation):
            return Reply(agent=self._agent, text=_questions(response, "cto"), brief=None)
        text = (response.content or "").strip() or _fallback(brief)
        return Reply(agent=self._agent, text=text, brief=brief)

    async def project_turn(self, conversation: Conversation) -> ProjectReply:
        """The PM's side: a project for her to plan."""
        response = await self._ask(PROJECT_PROMPT, PROJECT_TOOL, conversation)
        brief = parse_project(response, conversation)
        if brief and too_soon(conversation):
            return ProjectReply(agent=self._agent, text=_questions(response, "pm"), brief=None)
        text = (response.content or "").strip() or (
            "Here's the project. Check it, and I'll plan the backlog."
            if brief
            else "Tell me a little more about what you'd like to build?"
        )
        return ProjectReply(agent=self._agent, text=text, brief=brief)

    async def _ask(self, prompt: str, tool: ToolSpec, conversation: Conversation) -> LLMResponse:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": prompt.format(name=self._agent)}
        ]
        for t in conversation.turns:
            messages.append(
                {"role": "user" if t.role == "founder" else "assistant", "content": t.text}
            )
        return await self._llm.complete(messages, [tool])


FULL_SPEC = 700  # characters: a pasted spec may already answer everything
GO_AHEAD = re.compile(
    r"\b(just (start|go|build|do it|plan)|start now|go ahead|no questions)\b", re.I
)


def too_soon(conversation: Conversation) -> bool:
    """A brief on the founder's first message, when they gave a short request and didn't say to
    just go: the agent should ask first (small models skip it)."""
    founder = [t.text for t in conversation.turns if t.role == "founder"]
    if len(founder) != 1:
        return False
    return len(founder[0]) < FULL_SPEC and not GO_AHEAD.search(founder[0])


def _fallback(brief: Brief | None) -> str:
    """What the CTO says when the model sent a brief without a message."""
    if brief is None:
        return "Could you tell me a little more about what you need?"
    if brief.scale == "small":
        return "This looks like a small change, so I'd build it straight away. Check it below."
    if brief.scale == "big":
        return "This is a bigger change, so I'd plan it first. Check the brief below."
    return "Here's the brief. Check it, then choose what happens next, or tell me what to change."


def _questions(response: LLMResponse, role: str) -> str:
    """The agent's own questions if it wrote any, otherwise the standard ones."""
    text = (response.content or "").strip()
    return text if "?" in text else FIRST_QUESTIONS[role]


def parse_brief(response: LLMResponse, conversation: Conversation) -> Brief | None:
    """The brief from a submit_brief call, read leniently (small models name things their own
    way); None when the agent is still asking."""
    raw = _call(response, "submit_brief")
    if raw is None:
        return None
    founder = _founder(conversation)
    try:
        return Brief(
            request=_text(raw.get("request")) or founder,
            summary=_lines(_text(raw.get("summary")) or ""),
            repo_url=_text(raw.get("repo_url")),
            branch=_text(raw.get("branch")),
            create_repo=bool(raw.get("create_repo", not raw.get("repo_url"))),
            new_repo_name=_text(raw.get("new_repo_name")),
            stack=_stack(raw),
            test_command=_text(raw.get("test_command")),
            scale=raw.get("scale") if raw.get("scale") in ("small", "big") else None,
        )
    except ValidationError:
        return Brief(request=founder[:50_000])


def parse_project(response: LLMResponse, conversation: Conversation) -> ProjectBrief | None:
    """The project from a submit_project call, read leniently."""
    raw = _call(response, "submit_project")
    if raw is None:
        return None
    goal = _text(raw.get("goal")) or _founder(conversation)
    name = (_text(raw.get("name")) or goal.split("\n")[0])[:80]
    try:
        limit = min(max(int(raw.get("daily_limit") or 2), 1), 10)
    except (TypeError, ValueError):
        limit = 2
    try:
        return ProjectBrief(
            name=name if len(name) >= 2 else "New project",
            goal=goal if len(goal) >= 10 else f"{goal} (as described by the founder)",
            summary=_lines(_text(raw.get("summary")) or ""),
            repo_url=_text(raw.get("repo_url")),
            stack=_stack(raw),
            autopilot=bool(raw.get("autopilot", False)),
            daily_limit=limit,
        )
    except ValidationError:
        return None


def _call(response: LLMResponse, name: str) -> dict[str, Any] | None:
    call = next((c for c in response.tool_calls if c.name == name), None)
    return call.arguments if call else None


def _founder(conversation: Conversation) -> str:
    return "\n\n".join(t.text for t in conversation.turns if t.role == "founder")


def _stack(raw: dict[str, Any]) -> StackChoice:
    """The founder's stack choices from a tool call: only what they named."""
    stack = {f: _text(raw.get(f)) for f in FIELDS if _text(raw.get(f))}
    modules = raw.get("modules")
    try:
        return StackChoice(
            **stack,
            modules=[m for m in modules if isinstance(m, str)]
            if isinstance(modules, list)
            else None,
            starter=STARTERS.get(str(raw.get("starter", "auto")).lower()),
            notes=_text(raw.get("notes")) or "",
        )
    except ValidationError:
        return StackChoice()


def _text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _lines(text: str) -> str:
    """Small models sometimes write line breaks as the characters "/n" or "\\n"."""
    return text.replace("\\n", "\n").replace("/n", "\n")
