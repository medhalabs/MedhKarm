"""Planner node: turns the founder's request into a short plan the developer follows."""

from typing import Any

from app.features.models.interfaces import LLMProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState

PLANNER_PROMPT = """You are a technical lead. Write a short numbered plan (at most 5 steps)
for a developer to complete the request below. Name the files to create and what the tests
must check. Plain text only, no code."""


def make_plan_node(llm: LLMProvider, instructions: str = PLANNER_PROMPT) -> BuildNode:
    """`instructions` normally come from the CTO role in the team template."""

    async def plan(state: BuildState) -> dict[str, Any]:
        response = await llm.complete(
            [
                {"role": "system", "content": instructions.strip()},
                {"role": "user", "content": state["request"]},
            ]
        )
        return {"plan": (response.content or "").strip()}

    return plan
