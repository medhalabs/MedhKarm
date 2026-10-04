"""QA's checks beyond the tests: which ones a project gets, what blocks, and the fix round."""

import json
from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.events.schemas import EventType
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.repos.schemas import RepoSource
from app.features.repos.service import RepoService
from app.features.repos.tests.fakes import FakeHost, project_shell
from app.features.sandbox.interfaces import Sandbox
from app.features.sandbox.providers.memory_provider import InMemorySandbox, InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.workflows.checkers.quality import QualityChecker, detect_checks
from app.features.workflows.checkers.test_command import TestCommandChecker
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.schemas import RunOutcome
from app.features.workflows.service import WorkflowService

Handler = Callable[[str, dict[str, str]], CommandResult]


def tool(name: str, **arguments: Any) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def sandbox_with(files: dict[str, str], handler: Handler | None = None) -> InMemorySandbox:
    sandbox = InMemorySandbox("s", handler or (lambda c, f: CommandResult(exit_code=0, output="")))
    sandbox.files.update(files)
    return sandbox


def package(**scripts: str) -> str:
    return json.dumps({"scripts": scripts, "devDependencies": {"typescript": "5"}})


async def test_a_node_project_gets_its_own_type_check_lint_and_build() -> None:
    sandbox = sandbox_with(
        {"package.json": package(typecheck="tsc", lint="eslint .", build="next build", test="x")}
    )

    checks = await detect_checks(sandbox)

    assert [c.name for c in checks] == ["types", "lint", "build"]
    assert checks[0].command == "[ -d node_modules ] || npm install --no-audit --no-fund; " + (
        "npm run typecheck"
    )


async def test_typescript_without_a_script_is_type_checked_with_tsc() -> None:
    sandbox = sandbox_with({"package.json": package(), "tsconfig.json": "{}", "pnpm-lock.yaml": ""})

    [check] = await detect_checks(sandbox)

    assert check.name == "types" and check.command.endswith("npx --no-install tsc --noEmit")
    assert "pnpm install --frozen-lockfile" in check.command


async def test_python_gets_a_syntax_check_and_its_configured_linters() -> None:
    sandbox = sandbox_with(
        {
            "pyproject.toml": "[tool.ruff]\nline-length = 100\n[tool.mypy]\nstrict = true\n",
            "app.py": "x = 1",
            "notes.md": "",
        }
    )

    checks = await detect_checks(sandbox, ["app.py", "notes.md", "gone.py"])

    assert [c.name for c in checks] == ["syntax", "ruff", "mypy"]
    assert checks[0].command.endswith(" app.py")


async def test_a_project_that_configures_nothing_gets_only_its_tests() -> None:
    assert await detect_checks(sandbox_with({"index.html": "<p>hi</p>"})) == []


def failing(*words: str) -> Handler:
    """Commands containing any of `words` fail (exit 1); `missing` ones exit 127."""

    def run(command: str, files: dict[str, str]) -> CommandResult:
        if "missing" in words and "mypy" in command:
            return CommandResult(exit_code=127, output="mypy: command not found")
        bad = any(w in command for w in words if w != "missing")
        return CommandResult(exit_code=1 if bad else 0, output=f"out of {command}")

    return run


RUFF_PROJECT = {"pyproject.toml": "[tool.ruff]\n[tool.mypy]\n", "app.py": "x = 1"}


async def test_a_new_failure_blocks_but_old_failures_and_missing_tools_dont() -> None:
    checker = QualityChecker(TestCommandChecker())
    state: Any = {"test_command": "pytest", "dev_result": {"files_changed": ["app.py"]}}

    lint_fails = await checker.check(state, sandbox_with(RUFF_PROJECT, failing("ruff")))
    assert not lint_fails.passed
    assert "$ ruff check ." in lint_fails.output
    assert [(c.name, c.passed) for c in lint_fails.checks] == [
        ("tests", True),
        ("syntax", True),
        ("ruff", False),
        ("mypy", True),
    ]

    state["checks_baseline"] = {"ruff": False}  # it failed before the team started
    old = await checker.check(state, sandbox_with(RUFF_PROJECT, failing("ruff", "missing")))
    assert old.passed
    by_name = {c.name: c for c in old.checks}
    assert by_name["ruff"].already_failing and by_name["mypy"].skipped


async def test_failing_tests_fail_the_check() -> None:
    result = await QualityChecker(TestCommandChecker()).check(
        {"test_command": "pytest", "dev_result": {"files_changed": []}},
        sandbox_with({}, failing("pytest")),
    )

    assert not result.passed and result.checks[0].name == "tests"


# ---------- in the graph ----------


def build_and_review(*more: LLMResponse) -> list[LLMResponse]:
    return [
        tool("submit_plan", summary="s", developers=1, tasks=[{"title": "Write app.py"}]),
        tool("write_file", path="app.py", content="import os"),
        tool("write_file", path="pyproject.toml", content="[tool.ruff]\n"),
        tool("finish", summary="done"),
        tool("submit_review", decision="approve", feedback=""),
        *more,
    ]


FIX = [
    tool("write_file", path="app.py", content="x = 1"),
    tool("finish", summary="removed the unused import"),
    tool("submit_review", decision="approve", feedback=""),
]


def lint_passes_without_import_os(command: str, files: dict[str, str]) -> CommandResult:
    if command.startswith("ruff") and "import os" in files.get("app.py", ""):
        return CommandResult(exit_code=1, output="app.py:1:8: F401 `os` imported but unused")
    return CommandResult(exit_code=0, output="ok")


async def run(
    script: list[LLMResponse], handler: Handler, **start: Any
) -> tuple[RunOutcome, InMemoryEventStore]:
    llm, events = ScriptedLLMProvider(script), InMemoryEventStore()
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        InMemorySandboxProvider(handler),
        InMemorySaver(),
        events=events,
        developer_names=["Isha"],
        repos=RepoService(FakeHost()),
    )
    outcome = await WorkflowService(graph, events).start("r", "Build app.py", "pytest", **start)
    return outcome, events


def qa_summaries(events: InMemoryEventStore) -> list[str]:
    return [e.summary for e in events.events if e.actor == "qa"]


async def test_a_failed_check_goes_back_to_a_developer_once_then_reaches_the_gate() -> None:
    outcome, events = await run(build_and_review(*FIX), lint_passes_without_import_os)

    assert outcome.waiting_for_approval
    [_, fix] = outcome.state["tasks"]
    assert (fix["id"], fix["owner"], fix["status"]) == ("qa1", "Isha", "done")
    assert "F401" in fix["description"] and "`ruff check .`" in fix["description"]
    assert qa_summaries(events) == [
        "Checks failed: sent to Isha to fix",
        "Assigned “Make QA's checks pass” to Isha",
        "Checks passed (tests, syntax, ruff)",
    ]


async def test_checks_still_failing_after_the_fix_stop_the_release() -> None:
    still_broken = [
        tool("write_file", path="app.py", content="import os  # still"),
        tool("finish", summary="tried"),
        tool("submit_review", decision="approve", feedback=""),
    ]

    outcome, events = await run(build_and_review(*still_broken), lint_passes_without_import_os)

    assert not outcome.waiting_for_approval and outcome.state["status"] == "failed"
    assert qa_summaries(events)[-1] == "Stopped: the checks still fail"
    checks = [e for e in events.events if e.type == EventType.CHECK_FINISHED][-1]
    assert {c["name"]: c["passed"] for c in checks.data["checks"]}["ruff"] is False


class MypyHost(FakeHost):
    """Clones a project that configures mypy."""

    async def clone(self, source: RepoSource, sandbox: Sandbox) -> str:
        commit = await super().clone(source, sandbox)
        await sandbox.write_file("pyproject.toml", "[tool.mypy]\n")
        return commit


def mypy_always_fails(command: str, files: dict[str, str]) -> CommandResult:
    if command.startswith("mypy"):
        return CommandResult(exit_code=1, output="lib.py: error")
    return project_shell(command, files)


async def test_a_check_that_failed_before_the_team_started_does_not_block() -> None:
    """The founder's repo already fails its type-check: noted, not the team's to fix now."""
    script = [
        tool("submit_plan", summary="s", developers=1, tasks=[{"title": "Write app.py"}]),
        tool("write_file", path="app.py", content="x = 1"),
        tool("finish", summary="done"),
        tool("submit_review", decision="approve", feedback=""),
    ]
    llm, events = ScriptedLLMProvider(script), InMemoryEventStore()
    graph = build_app_graph(
        llm,
        ToolLoopEngine(llm),
        InMemorySandboxProvider(mypy_always_fails),
        InMemorySaver(),
        events=events,
        repos=RepoService(MypyHost()),
    )

    outcome = await WorkflowService(graph, events).start(
        "r", "Build app.py", "pytest", repo={"url": "https://github.com/a/b"}
    )

    assert outcome.state["checks_baseline"] == {"mypy": False}
    assert outcome.waiting_for_approval
    assert qa_summaries(events)[-1] == (
        "Checks passed (tests, syntax); already failing before this work: mypy"
    )
