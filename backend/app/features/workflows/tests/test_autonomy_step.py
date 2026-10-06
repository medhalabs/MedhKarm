"""The autonomy step: the founder's settings decide what the gate does, the verdict is fixed
before the gate, and "go live" can be switched off."""

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.approvals.schemas import ApprovalPolicy
from app.features.autonomy.policy import build_policy
from app.features.autonomy.schemas import AutonomySettings, Level
from app.features.deploys.schemas import DeployFile, Deployment
from app.features.deploys.service import DeployService
from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.teams.loader import load_templates
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.schemas import RunAutonomy
from app.features.workflows.service import WorkflowService

BASE = load_templates()["software"].approval


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def script(path: str) -> list[LLMResponse]:
    return [
        tool("submit_plan", summary="s", developers=1, tasks=[{"title": "Page"}]),
        tool("write_file", path=path, content="<h1>Tips</h1>"),
        tool("finish", summary="done"),
        tool("submit_review", decision="approve", feedback=""),
    ]


class Settings:
    """What the founder has set right now (can change while a release waits)."""

    def __init__(self, settings: AutonomySettings | None) -> None:
        self.settings = settings
        self.asked: list[str] = []

    async def for_run(self, run_id: str) -> RunAutonomy | None:
        self.asked.append(run_id)
        if self.settings is None:
            return None
        return RunAutonomy(policy=build_policy(BASE, self.settings), go_live=self.settings.go_live)


class Vercel:
    def __init__(self) -> None:
        self.calls: list[bool] = []

    async def deploy(
        self, name: str, files: list[DeployFile], production: bool, framework: str | None
    ) -> Deployment:
        self.calls.append(production)
        return Deployment(id="d", url="https://tips.vercel.app", state="READY", error="")


def service(
    path: str, settings: Settings | None, target: Vercel | None = None
) -> tuple[WorkflowService, InMemoryEventStore]:
    llm, events = ScriptedLLMProvider(script(path)), InMemoryEventStore()
    sandboxes = InMemorySandboxProvider(lambda c, f: CommandResult(exit_code=0, output="aGk="))
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        sandboxes,
        InMemorySaver(),
        events=events,
        approval_policy=BASE,
        autonomies=settings,
        deploys=DeployService(target) if target else None,
    )
    return WorkflowService(graph, events), events


async def test_a_company_that_set_nothing_is_asked_as_before() -> None:
    settings = Settings(None)
    flow, _ = service("index.html", settings)

    outcome = await flow.start("r1", "A tip page", "true")

    assert outcome.waiting_for_approval and settings.asked == ["r1"]
    assert outcome.state["go_live"] is True


async def test_release_on_its_own_when_the_founder_chose_that() -> None:
    flow, events = service("index.html", Settings(AutonomySettings(level=Level.CHECKS)))

    outcome = await flow.start("r1", "A tip page", "true")

    assert not outcome.waiting_for_approval and outcome.state["status"] == "released"
    summaries = [e.summary for e in events.events]
    assert any(t.startswith("Approved the release by your rules") for t in summaries)


async def test_a_risky_change_still_asks_even_on_release_on_its_own() -> None:
    flow, _ = service("package.json", Settings(AutonomySettings(level=Level.CHECKS)))

    outcome = await flow.start("r1", "A tip page", "true")

    assert outcome.waiting_for_approval
    assert outcome.gate is not None and outcome.gate["rules"] == ["sensitive_files"]


async def test_a_file_the_team_must_never_change_stops_the_release() -> None:
    settings = AutonomySettings(level=Level.CHECKS, never_touch=["pay/*"])
    flow, events = service("pay/razorpay.ts", Settings(settings))

    outcome = await flow.start("r1", "A tip page", "true")

    assert outcome.state["status"] == "rejected"
    assert outcome.state["feedback"] == "You told the team never to change pay/*."
    assert any("Stopped by your rules" in e.summary for e in events.events)


async def test_changing_the_settings_while_waiting_cannot_override_the_founders_decision() -> None:
    settings = Settings(AutonomySettings(level=Level.EVERY))
    flow, _ = service("index.html", settings)
    waiting = await flow.start("r1", "A tip page", "true")
    assert waiting.waiting_for_approval

    settings.settings = AutonomySettings(level=Level.CHECKS)  # changed while the release waits
    done = await flow.resume("r1", approved=False, feedback="Not yet")

    assert done.state["approved"] is False and done.state["status"] == "rejected"
    assert settings.asked == ["r1"]  # the settings were read once, before the gate


async def test_go_live_off_delivers_but_does_not_publish() -> None:
    target = Vercel()
    off = Settings(AutonomySettings(level=Level.CHECKS, go_live=False))
    flow, _ = service("index.html", off, target)
    outcome = await flow.start("r1", "A tip page", "true")
    assert outcome.state["status"] == "released"
    assert target.calls == [False]  # the preview only

    on_target = Vercel()
    on_flow, _ = service("index.html", Settings(AutonomySettings(level=Level.CHECKS)), on_target)
    await on_flow.start("r2", "A tip page", "true")
    assert on_target.calls == [False, True]  # preview, then production


def test_the_template_policy_is_what_the_default_falls_back_to() -> None:
    assert isinstance(BASE, ApprovalPolicy) and BASE.default.value == "ask"
