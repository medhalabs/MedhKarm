"""The CTO's decisions as data: a plan (tasks + team size) and a review verdict.

The CTO answers by calling a tool (`submit_plan`, `submit_review`), which gives structured
output on any model that can call tools. If a model ignores the tool, parsing falls back to
something safe: one task covering the whole request, or approving the work.
"""

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from app.features.models.schemas import LLMResponse, ToolSpec

MAX_TASKS = 5


class PlannedTask(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = ""
    specialty: str = "any"  # e.g. "frontend", "backend": who should build it


class CtoPlan(BaseModel):
    summary: str = ""
    developers: int = 1
    tasks: list[PlannedTask] = Field(min_length=1)


class ReviewDecision(BaseModel):
    decision: Literal["approve", "revise"]
    feedback: str = ""


PLAN_TOOL: ToolSpec = {
    "type": "function",
    "function": {
        "name": "submit_plan",
        "description": "Submit the plan: summary, number of developers, and tasks in order.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "One or two sentences for the founder",
                },
                "developers": {"type": "integer", "description": "How many developers to use"},
                "tasks": {
                    "type": "array",
                    "description": f"1 to {MAX_TASKS} small tasks, in the order to build them",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Short, e.g. 'Add the expense form'",
                            },
                            "description": {
                                "type": "string",
                                "description": "Files to change and what the tests must check",
                            },
                            "specialty": {
                                "type": "string",
                                "description": "Who should build it: frontend, backend or any",
                            },
                        },
                        "required": ["title", "description"],
                    },
                },
            },
            "required": ["summary", "developers", "tasks"],
        },
    },
}

REVIEW_TOOL: ToolSpec = {
    "type": "function",
    "function": {
        "name": "submit_review",
        "description": "Approve the task, or send it back with specific changes to make.",
        "parameters": {
            "type": "object",
            "properties": {
                "decision": {"type": "string", "enum": ["approve", "revise"]},
                "feedback": {"type": "string", "description": "What to change, if revising"},
            },
            "required": ["decision", "feedback"],
        },
    },
}


def parse_plan(response: LLMResponse, request: str) -> CtoPlan:
    """The plan from the CTO's answer: the tool call, else JSON in the text, else numbered
    lines, else one task for the whole request."""
    for call in response.tool_calls:
        if call.name == PLAN_TOOL["function"]["name"]:
            plan = _validate_plan(call.arguments)
            if plan:
                return plan
    text = response.content or ""
    found = re.search(r"\{.*\}", text, re.DOTALL)
    if found:
        try:
            plan = _validate_plan(json.loads(found.group(0)))
            if plan:
                return plan
        except json.JSONDecodeError:
            pass
    steps = [m.group(1).strip() for m in re.finditer(r"^\s*\d+[.)]\s+(.+)$", text, re.MULTILINE)]
    if steps:
        return CtoPlan(
            summary=text.strip()[:300],
            tasks=[PlannedTask(title=s[:120]) for s in steps[:MAX_TASKS]],
        )
    return CtoPlan(
        summary=text.strip()[:300],
        tasks=[PlannedTask(title="Build the request", description=request)],
    )


def parse_review(response: LLMResponse) -> ReviewDecision:
    """The CTO's verdict: the tool call, else approve (never block the run on a format slip;
    QA's final check still runs)."""
    for call in response.tool_calls:
        if call.name == REVIEW_TOOL["function"]["name"]:
            try:
                return ReviewDecision.model_validate(call.arguments)
            except ValidationError:
                break
    return ReviewDecision(decision="approve", feedback="")


def assign(
    plan: CtoPlan,
    developer_names: list[str],
    max_developers: int,
    specialties: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Tasks with ids and owners: round-robin over the developers the CTO chose to use. With
    `specialties` (name -> specialty), a task goes to a matching specialist when one fits
    within `max_developers`, else to the team as usual."""
    team_size = max(1, min(plan.developers, max_developers, len(plan.tasks), len(developer_names)))
    team = developer_names[:team_size]
    allowed = developer_names[: max(1, min(max_developers, len(developer_names)))]
    turns: dict[str, int] = {}
    tasks = []
    for i, task in enumerate(plan.tasks[:MAX_TASKS]):
        owner = team[i % team_size]
        wanted = task.specialty
        if specialties and wanted != "any":
            fits = [n for n in allowed if specialties.get(n) == wanted]
            if fits:
                owner = fits[turns.get(wanted, 0) % len(fits)]
                turns[wanted] = turns.get(wanted, 0) + 1
        tasks.append(
            {
                "id": f"t{i + 1}",
                "title": _without_name(task.title, developer_names),
                "description": task.description,
                "specialty": (specialties or {}).get(owner, "any"),
                "owner": owner,
                "status": "todo",
                "attempts": 0,
                "feedback": "",
                "summary": "",
                "files_changed": [],
                "success": False,
            }
        )
    return tasks


def _without_name(title: str, names: list[str]) -> str:
    """Drop a leading "Isha: " the model sometimes puts in titles; owners are shown separately."""
    for name in names:
        if title.lower().startswith(name.lower() + ":"):
            return title[len(name) + 1 :].strip() or title
    return title


def _validate_plan(data: Any) -> CtoPlan | None:
    """Small models call the tool but shape tasks their own way (`name` instead of `title`,
    extra `files`/`tests`/`developer` keys, plain strings). Normalise before validating."""
    if not isinstance(data, dict):
        return None
    raw_tasks = data.get("tasks")
    if isinstance(raw_tasks, str):
        try:
            raw_tasks = json.loads(raw_tasks)
        except json.JSONDecodeError:
            raw_tasks = [line for line in raw_tasks.splitlines() if line.strip()]
    if not isinstance(raw_tasks, list):
        return None
    tasks = [task for task in (_normalise_task(t) for t in raw_tasks) if task]
    try:
        developers = int(data.get("developers", 1))
    except (TypeError, ValueError):
        developers = 1
    try:
        return CtoPlan(summary=str(data.get("summary", "")), developers=developers, tasks=tasks)
    except ValidationError:
        return None


TITLE_KEYS = ("title", "name", "task", "summary")
SPECIALTY_KEYS = ("specialty", "speciality", "area", "role", "skill")
# A task titled like page work is frontend work, whatever the plan says
UI_WORDS = re.compile(r"\b(ui|page|pages|form|screen|component|layout|styling|frontend)\b", re.I)
API_WORDS = re.compile(r"\b(api|route|endpoint|database|migration|schema|server)\b", re.I)
SKIP_KEYS = {*TITLE_KEYS, *SPECIALTY_KEYS, "description", "developer", "owner", "assignee", "id"}


def _normalise_task(raw: Any) -> PlannedTask | None:
    if isinstance(raw, str):
        text = re.sub(r"^\s*(\d+[.)]|-|\*)\s*", "", raw).strip()
        return PlannedTask(title=text[:120], description=text) if text else None
    if not isinstance(raw, dict):
        return None
    description = str(raw.get("description", "")).strip()
    title = next((str(raw[k]).strip() for k in TITLE_KEYS if str(raw.get(k, "")).strip()), "")
    if not title:
        title = description.splitlines()[0] if description else ""
    title = re.sub(r"^tasks?\s*\d*\s*[:.\-\u2013\u2014]\s*", "", title, flags=re.IGNORECASE)[:120]
    # Fold other useful detail (files, tests, ...) into the description.
    extras = []
    for key, value in raw.items():
        if key in SKIP_KEYS or value in (None, "", []):
            continue
        shown = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
        extras.append(f"{key.capitalize()}: {shown}")
    full = "\n".join([description, *extras]).strip()
    specialty = next(
        (str(raw[k]).strip().lower() for k in SPECIALTY_KEYS if str(raw.get(k, "")).strip()),
        "any",
    )
    if UI_WORDS.search(title) and not API_WORDS.search(title):
        specialty = "frontend"  # small models tag page work "backend" (live run, Oct 5, 2026)
    return PlannedTask(title=title, description=full, specialty=specialty) if title else None
