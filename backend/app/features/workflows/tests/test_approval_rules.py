"""The release gate follows the team's approval rules."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.approvals.schemas import Action, ApprovalPolicy, ApprovalRule, Condition
from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.schemas import EventType
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.nodes.approval import approval_facts
from app.features.workflows.schemas import RunOutcome
from app.features.workflows.service import WorkflowService


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def script(path: str) -> list[LLMResponse]:
    return [
        tool("submit_plan", summary="s", developers=1, tasks=[{"title": "Do it"}]),
        tool("write_file", path=path, content="x"),
        tool("finish", summary="done"),
        tool("submit_review", decision="approve", feedback=""),
    ]


async def run(path: str, policy: ApprovalPolicy) -> tuple[RunOutcome, InMemoryEventStore]:
    llm, events = ScriptedLLMProvider(script(path)), InMemoryEventStore()
    sandboxes = InMemorySandboxProvider(lambda c, f: CommandResult(exit_code=0, output="ok"))
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        sandboxes,
        InMemorySaver(),
        events=events,
        approval_policy=policy,
    )
    return await WorkflowService(graph, events).start("r", "Build it", "pytest"), events


SMALL_ONES_GO = ApprovalPolicy(
    rules=[
        ApprovalRule(
            id="sensitive",
            action=Action.ASK,
            reason="It changes package.json.",
            when=[Condition(fact="files_changed", op="matches_any", value=["package.json"])],
        ),
        ApprovalRule(
            id="small",
            action=Action.APPROVE,
            reason="Small and tested.",
            when=[Condition(fact="files_count", op="lte", value=3)],
        ),
    ]
)


async def test_rules_can_release_without_asking() -> None:
    outcome, events = await run("calc.py", SMALL_ONES_GO)

    assert not outcome.waiting_for_approval
    assert outcome.state["status"] == "released"
    decided = [e for e in events.events if e.type == EventType.APPROVAL_DECIDED]
    assert [e.summary for e in decided] == ["Approved the release by your rules: Small and tested."]
    assert decided[0].data["rules"] == ["small"]


async def test_a_matching_ask_rule_pauses_and_says_why() -> None:
    outcome, events = await run("package.json", SMALL_ONES_GO)

    assert outcome.waiting_for_approval
    assert outcome.gate is not None
    assert outcome.gate["reasons"] == ["It changes package.json."]
    assert outcome.gate["rules"] == ["sensitive"]
    assert events.events[-1].summary == (
        "Waiting for your approval to release: It changes package.json."
    )


async def test_rules_can_stop_a_release() -> None:
    stop = ApprovalPolicy(
        rules=[ApprovalRule(id="freeze", action=Action.REJECT, reason="Release freeze.")]
    )

    outcome, _ = await run("calc.py", stop)

    assert outcome.state["status"] == "rejected"
    assert outcome.state["feedback"] == "Release freeze."


async def test_without_rules_every_release_asks() -> None:
    outcome, _ = await run("calc.py", ApprovalPolicy())

    assert outcome.waiting_for_approval
    assert outcome.gate is not None and outcome.gate["rules"] == []


def test_facts_count_cto_and_developer_tokens() -> None:
    facts = approval_facts(
        {
            "dev_result": {"files_changed": ["a.py"], "total_tokens": 100},
            "cto_tokens_total": 40,
            "tasks": [{"status": "done"}, {"status": "done_with_issues"}],
            "verified": True,
        }
    )

    assert facts == {
        "files_changed": ["a.py"],
        "files_count": 1,
        "tokens": 140,
        "tasks_count": 2,
        "tasks_with_issues": 1,
        "tests_passed": True,
        "security_warnings": 0,
    }
