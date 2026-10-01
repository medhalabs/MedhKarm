from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.workflows.cto import CtoPlan, PlannedTask, assign, parse_plan, parse_review
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService

NAMES = ["Isha", "Arjun", "Ravi"]


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def plan_call(*titles: str, developers: int = 1) -> LLMResponse:
    tasks = [{"title": t, "description": f"do {t}"} for t in titles]
    return tool("submit_plan", summary="Plan", developers=developers, tasks=tasks)


# ---- parsing and assignment ----


def test_plan_from_tool_call() -> None:
    plan = parse_plan(plan_call("Form", "List", developers=2), "req")

    assert [t.title for t in plan.tasks] == ["Form", "List"]
    assert plan.developers == 2


def test_plan_from_json_in_text() -> None:
    text = 'Here: {"summary": "s", "developers": 1, "tasks": [{"title": "A", "description": ""}]}'

    assert [t.title for t in parse_plan(LLMResponse(content=text), "req").tasks] == ["A"]


def test_plan_from_numbered_lines() -> None:
    plan = parse_plan(LLMResponse(content="Plan:\n1. Add form\n2) Add list\nThanks"), "req")

    assert [t.title for t in plan.tasks] == ["Add form", "Add list"]


def test_plan_falls_back_to_one_task_for_the_whole_request() -> None:
    plan = parse_plan(LLMResponse(content="I think it's fine."), "Build an expense app")

    assert len(plan.tasks) == 1
    assert plan.tasks[0].description == "Build an expense app"


def test_assign_round_robin_within_limits() -> None:
    plan = CtoPlan(developers=5, tasks=[PlannedTask(title=f"T{i}") for i in range(4)])

    tasks = assign(plan, NAMES, max_developers=2)

    assert [(t["id"], t["owner"]) for t in tasks] == [
        ("t1", "Isha"),
        ("t2", "Arjun"),
        ("t3", "Isha"),
        ("t4", "Arjun"),
    ]


def test_one_task_uses_one_developer_and_tasks_are_capped() -> None:
    assert {
        t["owner"] for t in assign(CtoPlan(developers=3, tasks=[PlannedTask(title="T")]), NAMES, 3)
    } == {"Isha"}
    many = CtoPlan(tasks=[PlannedTask(title=f"T{i}") for i in range(9)])
    assert len(assign(many, NAMES, 3)) == 5


def test_review_parsing_defaults_to_approve() -> None:
    assert (
        parse_review(tool("submit_review", decision="revise", feedback="Add a test")).feedback
        == "Add a test"
    )
    assert parse_review(LLMResponse(content="Looks fine")).decision == "approve"
    assert parse_review(tool("submit_review", decision="maybe", feedback="")).decision == "approve"


# ---- the review loop in the graph ----


def judge(command: str, files: dict[str, str]) -> CommandResult:
    return CommandResult(exit_code=0 if "a.py" in files else 1, output="tests")


async def run(script: list[LLMResponse]) -> dict[str, Any]:
    llm = ScriptedLLMProvider(script)
    sandboxes = InMemorySandboxProvider(judge)
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        sandboxes,
        InMemorySaver(),
        developer_names=NAMES,
        max_developers=3,
    )
    outcome = await WorkflowService(graph).start("r", "Build it", "pytest")
    return outcome.state


async def test_two_tasks_two_developers_each_approved() -> None:
    state = await run(
        [
            plan_call("Write a.py", "Write b.py", developers=2),
            tool("write_file", path="a.py", content="1"),
            tool("finish", summary="a done"),
            tool("submit_review", decision="approve", feedback=""),
            tool("write_file", path="b.py", content="2"),
            tool("finish", summary="b done"),
            tool("submit_review", decision="approve", feedback=""),
        ]
    )

    assert [(t["owner"], t["status"]) for t in state["tasks"]] == [
        ("Isha", "done"),
        ("Arjun", "done"),
    ]
    assert state["verified"] is True


async def test_cto_sends_work_back_with_feedback_then_approves() -> None:
    llm_script = [
        plan_call("Write a.py"),
        tool("write_file", path="a.py", content="1"),
        tool("finish", summary="first try"),
        tool("submit_review", decision="revise", feedback="Add a docstring"),
        tool("write_file", path="a.py", content='"""Doc."""\n1'),
        tool("finish", summary="second try"),
        tool("submit_review", decision="approve", feedback=""),
    ]
    llm = ScriptedLLMProvider(llm_script)
    sandboxes = InMemorySandboxProvider(judge)
    graph = build_app_graph(llm, ToolLoopEngine(llm), sandboxes, InMemorySaver())

    state = (await WorkflowService(graph).start("r", "Build it", "pytest")).state

    [task] = state["tasks"]
    assert (task["status"], task["attempts"]) == ("done", 2)
    # the developer's second brief carried the CTO's feedback
    second_brief = next(m for m in llm.calls[4] if m["role"] == "user")["content"]
    assert "Add a docstring" in second_brief


async def test_revisions_are_capped() -> None:
    state = await run(
        [
            plan_call("Write a.py"),
            tool("write_file", path="a.py", content="1"),
            tool("finish", summary="try 1"),
            tool("submit_review", decision="revise", feedback="Again"),
            tool("finish", summary="try 2"),
            tool("submit_review", decision="revise", feedback="Again"),
        ]
    )

    [task] = state["tasks"]
    assert (task["status"], task["attempts"]) == ("done_with_issues", 2)
    assert state["verified"] is True  # QA still checks: the code does pass


def test_plan_shapes_small_models_actually_send() -> None:
    """Real gpt-oss:20b outputs: `name` instead of `title`, extra keys, no title at all."""
    response = tool(
        "submit_plan",
        summary="s",
        developers="2",
        tasks=[
            {"name": "Task 1: Base class", "files": ["expenses.py"], "tests": "add rejects <= 0"},
            {"description": "Monthly totals by category\nUse a dict", "developer": "Arjun"},
            "3. CSV export",
        ],
    )

    plan = parse_plan(response, "req")

    assert [t.title for t in plan.tasks] == [
        "Base class",
        "Monthly totals by category",
        "CSV export",
    ]
    assert "Files: expenses.py" in plan.tasks[0].description
    assert "Tests: add rejects <= 0" in plan.tasks[0].description
    assert plan.developers == 2
