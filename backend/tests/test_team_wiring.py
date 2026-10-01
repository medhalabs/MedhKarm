"""The team template's vocabulary matches what the platform implements, and its settings
actually reach the agents."""

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.developer_engine.engines.tools import TOOL_SPECS
from app.features.developer_engine.schemas import DevTask
from app.features.events.schemas import Actor
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.teams.catalog import KNOWN_TOOLS
from app.features.teams.loader import load_templates


def test_known_tools_are_exactly_the_engine_tools() -> None:
    assert {spec["function"]["name"] for spec in TOOL_SPECS} == KNOWN_TOOLS


def test_every_role_can_appear_in_the_activity_log() -> None:
    actors = {actor.value for actor in Actor}
    for template in load_templates().values():
        assert {role.id for role in template.roles} <= actors, template.id


async def test_developer_gets_the_role_instructions_and_only_its_tools() -> None:
    role = load_templates()["software"].role("developer")
    seen: list[tuple[str, list[str]]] = []

    class Spy(ScriptedLLMProvider):
        async def complete(self, messages, tools=None):  # type: ignore[no-untyped-def]
            seen.append((messages[0]["content"], [t["function"]["name"] for t in tools or []]))
            return await super().complete(messages, tools)

    finish = LLMResponse(tool_calls=[ToolCall(id="f", name="finish", arguments={"summary": "x"})])
    engine = ToolLoopEngine(Spy([finish]), tools=role.tools, instructions=role.instructions)
    sandbox = await InMemorySandboxProvider().create()

    await engine.run_task(DevTask(description="x", test_command="true"), sandbox)

    prompt, tools = seen[0]
    assert prompt == role.instructions.strip()
    assert sorted(tools) == sorted(role.tools)
    assert "apply_patch" not in tools


def test_approval_facts_match_the_catalog() -> None:
    from app.features.teams.catalog import WORKFLOW_FACTS
    from app.features.workflows.nodes.approval import approval_facts

    assert set(approval_facts({})) == WORKFLOW_FACTS["build_app"]
