"""The security engineer's step: clean work goes to the gate, blocking findings go back to a
developer once, and what's still there stops the release."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.schemas import EventType
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.interfaces import Sandbox
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.security.schemas import Finding, ScanResult, Severity
from app.features.security.service import SecurityReview
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.schemas import RunOutcome
from app.features.workflows.service import WorkflowService


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def build_and_review(*more: LLMResponse) -> list[LLMResponse]:
    return [
        tool("submit_plan", summary="s", developers=1, tasks=[{"title": "Write app.py"}]),
        tool("write_file", path="app.py", content="KEY = 1"),
        tool("finish", summary="done"),
        tool("submit_review", decision="approve", feedback=""),
        *more,
    ]


class Scripted:
    """A scanner that reports the given findings, one list per scan."""

    name = "scripted"

    def __init__(self, *rounds: list[Finding]) -> None:
        self.rounds = list(rounds)
        self.seen: list[list[str]] = []

    async def scan(self, sandbox: Sandbox, changed: list[str]) -> ScanResult:
        self.seen.append(changed)
        return ScanResult(findings=self.rounds.pop(0) if self.rounds else [])


SECRET = Finding(
    tool="secrets",
    rule="github-token",
    severity=Severity.CRITICAL,
    path="app.py",
    line=1,
    message="A GitHub token is written in the code.",
    fix="Remove it.",
)
WARNING = Finding(
    tool="semgrep",
    rule="py-weak-hash",
    severity=Severity.MEDIUM,
    path="app.py",
    line=3,
    message="MD5 is broken for security.",
)


async def run(
    script: list[LLMResponse], scanner: Scripted
) -> tuple[RunOutcome, InMemoryEventStore]:
    llm, events = ScriptedLLMProvider(script), InMemoryEventStore()
    sandboxes = InMemorySandboxProvider(lambda c, f: CommandResult(exit_code=0, output="ok"))
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        sandboxes,
        InMemorySaver(),
        events=events,
        developer_names=["Isha"],
        security=SecurityReview([scanner]),
    )
    return await WorkflowService(graph, events).start("r", "Build app.py", "pytest"), events


async def test_clean_work_goes_to_the_gate() -> None:
    scanner = Scripted([])
    outcome, events = await run(build_and_review(), scanner)

    assert outcome.waiting_for_approval
    assert scanner.seen == [["app.py"]]
    assert "No security problems found" in [e.summary for e in events.events]


async def test_blocking_findings_go_back_to_a_developer_once() -> None:
    scanner = Scripted([SECRET], [])
    fix = [
        tool("write_file", path="app.py", content="import os\nKEY = os.environ['KEY']"),
        tool("finish", summary="read it from the environment"),
        tool("submit_review", decision="approve", feedback=""),
    ]

    outcome, events = await run(build_and_review(*fix), scanner)

    assert outcome.waiting_for_approval
    [_, task] = outcome.state["tasks"]
    assert (task["id"], task["title"], task["owner"], task["status"]) == (
        "sec1",
        "Fix the security findings",
        "Isha",
        "done",
    )
    assert "GitHub token" in task["description"]
    summaries = [e.summary for e in events.events if e.actor == "security"]
    assert summaries == [
        "Found 1 security problem: sent to Isha to fix",
        "Assigned “Fix the security findings” to Isha",
        "No security problems found",
    ]


async def test_problems_still_there_stop_the_release_without_asking() -> None:
    scanner = Scripted([SECRET], [SECRET])
    fix = [
        tool("write_file", path="app.py", content="KEY = 2"),
        tool("finish", summary="tried"),
        tool("submit_review", decision="approve", feedback=""),
    ]

    outcome, events = await run(build_and_review(*fix), scanner)

    assert not outcome.waiting_for_approval
    assert outcome.state["status"] == "failed"
    last_scan = [e for e in events.events if e.type == EventType.SECURITY_FINISHED][-1]
    assert last_scan.summary == "Stopped the release: 1 security problem still there"


async def test_warnings_reach_the_founder_at_the_gate() -> None:
    outcome, _ = await run(build_and_review(), Scripted([WARNING]))

    assert outcome.waiting_for_approval and outcome.gate is not None
    assert outcome.gate["security"] == ["medium: app.py MD5 is broken for security."]
