"""The PM's backlog as data: the `submit_backlog` tool and a lenient reading of the answer.

Like the CTO's plan (workflows/cto.py), small models call the tool but shape items their own
way, so the parser accepts the common variations and falls back to something safe: numbered
lines from the text, or one item for the whole goal.
"""

import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.features.models.schemas import LLMResponse, ToolSpec
from app.features.projects.schemas import ItemFields, Size

MAX_ITEMS = 12
MAX_QUESTIONS = 3

PM_PROMPT = """You are the product manager of a small software team. Turn the founder's goal
into a backlog: 3 to 12 small items, in the order to build them. Each item is a working,
testable slice the founder could try, not a technical layer. Give each a short title, what
and why in one to three sentences, two to four acceptance checks ("done when ..."), and a
size: S, M or L (split anything bigger). The first item is the smallest useful version. Every
item includes its own tests; never plan a separate testing item. If
something important is unclear, make a sensible assumption and list it as a question (at
most 3). Answer with submit_backlog."""


class Backlog(BaseModel):
    summary: str = ""
    questions: list[str] = Field(default_factory=list)
    items: list[ItemFields] = Field(min_length=1)


BACKLOG_TOOL: ToolSpec = {
    "type": "function",
    "function": {
        "name": "submit_backlog",
        "description": "Submit the backlog: items in build order, plus open questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "One or two sentences"},
                "questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Assumptions or questions for the founder (at most 3)",
                },
                "items": {
                    "type": "array",
                    "description": f"1 to {MAX_ITEMS} items, in the order to build them",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "acceptance": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Done when ...",
                            },
                            "size": {"type": "string", "enum": ["S", "M", "L"]},
                        },
                        "required": ["title", "description", "acceptance", "size"],
                    },
                },
            },
            "required": ["summary", "questions", "items"],
        },
    },
}

TITLE_KEYS = ("title", "name", "item", "story", "summary")
ACCEPTANCE_KEYS = ("acceptance", "acceptance_criteria", "criteria", "done_when", "checks")
SIZES = {"s": Size.S, "small": Size.S, "m": Size.M, "medium": Size.M, "l": Size.L, "large": Size.L}


def parse_backlog(response: LLMResponse, goal: str) -> Backlog:
    for call in response.tool_calls:
        if call.name == BACKLOG_TOOL["function"]["name"]:
            backlog = _validate(call.arguments)
            if backlog:
                return backlog
    text = response.content or ""
    found = re.search(r"\{.*\}", text, re.DOTALL)
    if found:
        try:
            backlog = _validate(json.loads(found.group(0)))
            if backlog:
                return backlog
        except json.JSONDecodeError:
            pass
    lines = [m.group(1).strip() for m in re.finditer(r"^\s*\d+[.)]\s+(.+)$", text, re.MULTILINE)]
    items = [_item({"title": line}) for line in lines[:MAX_ITEMS]]
    if any(items):
        return Backlog(items=[i for i in items if i])
    title = goal.strip().splitlines()[0][:117] if goal.strip() else "Build the project"
    return Backlog(items=[ItemFields(title=_fit(title), description=goal[:3000])])


def _validate(data: Any) -> Backlog | None:
    if not isinstance(data, dict):
        return None
    raw = data.get("items") or data.get("backlog") or data.get("stories")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = [line for line in raw.splitlines() if line.strip()]
    if not isinstance(raw, list):
        return None
    items = [i for i in (_item(r) for r in raw[:MAX_ITEMS]) if i]
    questions = data.get("questions") or data.get("assumptions") or []
    if isinstance(questions, str):
        questions = [q for q in questions.splitlines() if q.strip()]
    try:
        return Backlog(
            summary=str(data.get("summary", ""))[:500],
            questions=[str(q).strip()[:300] for q in questions if str(q).strip()][:MAX_QUESTIONS],
            items=items,
        )
    except ValidationError:
        return None


def _item(raw: Any) -> ItemFields | None:
    if isinstance(raw, str):
        raw = {"title": re.sub(r"^\s*(\d+[.)]|-|\*)\s*", "", raw)}
    if not isinstance(raw, dict):
        return None
    description = str(raw.get("description") or raw.get("details") or "").strip()
    title = next((str(raw[k]).strip() for k in TITLE_KEYS if str(raw.get(k) or "").strip()), "")
    title = title or (description.splitlines()[0] if description else "")
    title = re.sub(r"^(item|story|task)?\s*\d*\s*[:.\-\u2013\u2014]\s*", "", title, flags=re.I)
    if len(title.strip()) < 3:
        return None
    acceptance: Any = next((raw[k] for k in ACCEPTANCE_KEYS if raw.get(k)), [])
    if isinstance(acceptance, str):
        acceptance = [a for a in re.split(r"\n|;\s*", acceptance) if a.strip()]
    checks = [re.sub(r"^\s*[-*•]\s*", "", str(a)).strip()[:300] for a in acceptance]
    size = SIZES.get(str(raw.get("size", "M")).strip().lower(), Size.M)
    return ItemFields(
        title=_fit(title.strip()),
        description=description[:3000],
        acceptance=[c for c in checks if c][:10],
        size=size,
    )


def _fit(title: str) -> str:
    return title if len(title) <= 120 else title[:117].rstrip() + "..."
