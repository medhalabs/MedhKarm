"""CTO planning node: splits the founder's request into tasks and assigns them to developers."""

from typing import Any

from app.features.models.interfaces import LLMProvider
from app.features.workflows.cto import PLAN_TOOL, assign, parse_plan
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState

PLANNER_PROMPT = """You are the CTO of a small software team. Split the request into 1 to 5
small tasks, in the order to build them, and decide how many developers to use. Each task
names the files to create or change and what its tests must check. Answer with submit_plan."""


def make_plan_node(
    llm: LLMProvider,
    instructions: str = PLANNER_PROMPT,
    developer_names: list[str] | None = None,
    max_developers: int = 1,
) -> BuildNode:
    """`instructions`, `developer_names` and `max_developers` normally come from the team
    template (CTO and developer roles)."""
    names = developer_names or ["Developer"]

    async def plan(state: BuildState) -> dict[str, Any]:
        team = (
            f"You can use up to {min(max_developers, len(names))} developers: {', '.join(names)}."
        )
        response = await llm.complete(
            [
                {"role": "system", "content": instructions.strip()},
                {"role": "user", "content": f"{state['request']}\n\n{team}"},
            ],
            [PLAN_TOOL],
        )
        cto_plan = parse_plan(response, state["request"])
        tasks = assign(cto_plan, names, max_developers)
        lines = [f"{i + 1}. {t['title']} ({t['owner']})" for i, t in enumerate(tasks)]
        return {
            "plan": "\n".join([cto_plan.summary, *lines]).strip(),
            "tasks": tasks,
            "current_task": 0,
            "cto_tokens": response.usage.total_tokens,
            "cto_tokens_total": response.usage.total_tokens,
        }

    return plan
