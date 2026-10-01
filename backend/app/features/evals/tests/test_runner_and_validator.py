"""Runner and validator with fakes: scripted model, in-memory sandbox, in-memory checkpoints."""

from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver

from app.features.developer_engine.engines.tool_loop_engine import ToolLoopEngine
from app.features.evals.runner import EvalRunner
from app.features.evals.schemas import EvalTask
from app.features.evals.validator import TaskValidator
from app.features.models.exceptions import ModelCallError
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, ToolCall
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult
from app.features.workflows.graphs.build_app import build_app_graph
from app.features.workflows.service import WorkflowService


def make_task(tmp_path: Path) -> EvalTask:
    """Starting project has app.py; visible tests need fixed.py; hidden checks need done.txt."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text("x = 1")
    task_dir = tmp_path / "task"
    (task_dir / "checks").mkdir(parents=True)
    (task_dir / "checks" / "check.txt").write_text("hidden")
    (task_dir / "solution").mkdir()
    (task_dir / "solution" / "fixed.py").write_text("ok")
    (task_dir / "solution" / "done.txt").write_text("ok")
    return EvalTask(
        id="t1",
        title="T",
        kind="bug",
        difficulty=1,
        language="python",
        request="Fix it",
        test_command="visible",
        check_command="hidden",
        task_dir=task_dir,
        repo_dir=repo,
    )


def judge(command: str, files: dict[str, str]) -> CommandResult:
    if command == "visible":
        return CommandResult(exit_code=0 if "fixed.py" in files else 1, output="visible run")
    if command == "hidden":
        ok = "done.txt" in files and ".eval_checks/check.txt" in files
        return CommandResult(exit_code=0 if ok else 1, output="hidden run")
    return CommandResult(exit_code=0, output="")


def call(name: str, **arguments: str) -> LLMResponse:
    return LLMResponse(tool_calls=[ToolCall(id=f"id_{name}", name=name, arguments=arguments)])


def make_runner(script: list[LLMResponse]) -> tuple[EvalRunner, InMemorySandboxProvider]:
    llm = ScriptedLLMProvider(script)
    sandboxes = InMemorySandboxProvider(judge)
    graph = build_app_graph(llm, ToolLoopEngine(llm), sandboxes, InMemorySaver())
    return EvalRunner(WorkflowService(graph), sandboxes), sandboxes


async def test_pass_needs_visible_and_hidden(tmp_path: Path) -> None:
    runner, sandboxes = make_runner(
        [
            LLMResponse(content="plan"),
            call("write_file", path="fixed.py", content="ok"),
            call("write_file", path="done.txt", content="ok"),
            call("finish", summary="Fixed"),
            call("submit_review", decision="approve", feedback=""),
        ]
    )

    outcome = await runner.run(make_task(tmp_path))

    assert outcome.passed and outcome.visible_passed and outcome.hidden_passed
    assert outcome.summary == "Fixed"
    assert sandboxes.sandboxes == {}  # cleaned up


async def test_visible_pass_but_hidden_fail(tmp_path: Path) -> None:
    runner, _ = make_runner(
        [
            LLMResponse(content="plan"),
            call("write_file", path="fixed.py", content="ok"),
            call("finish", summary="Fixed"),
            call("submit_review", decision="approve", feedback=""),
        ]
    )

    outcome = await runner.run(make_task(tmp_path))

    assert outcome.visible_passed and not outcome.hidden_passed and not outcome.passed


async def test_visible_fail_skips_hidden(tmp_path: Path) -> None:
    runner, sandboxes = make_runner(
        [
            LLMResponse(content="plan"),
            call("finish", summary="Nothing"),
            call("finish", summary="Again"),
        ]
    )

    outcome = await runner.run(make_task(tmp_path))

    assert not outcome.visible_passed and not outcome.hidden_passed
    assert sandboxes.sandboxes == {}


async def test_errors_are_recorded_not_raised(tmp_path: Path) -> None:
    runner, sandboxes = make_runner([])  # the scripted model has nothing to say

    outcome = await runner.run(make_task(tmp_path))

    assert not outcome.passed
    assert outcome.error and "ran out of responses" in outcome.error
    assert sandboxes.sandboxes == {}


async def test_validator_accepts_fair_task(tmp_path: Path) -> None:
    [result] = await TaskValidator(InMemorySandboxProvider(judge)).validate_all(
        [make_task(tmp_path)]
    )

    assert result.ok


async def test_validator_flags_task_already_solved(tmp_path: Path) -> None:
    task = make_task(tmp_path)
    (task.repo_dir / "done.txt").write_text("already here")  # type: ignore[operator]

    [result] = await TaskValidator(InMemorySandboxProvider(judge)).validate_all([task])

    assert not result.fixture_fails_checks
    assert not result.ok


async def test_model_outage_is_errored_not_failed(tmp_path: Path) -> None:
    class DownProvider(ScriptedLLMProvider):
        async def complete(self, messages, tools=None):  # type: ignore[no-untyped-def]
            raise ModelCallError("down")

    llm = DownProvider([])
    sandboxes = InMemorySandboxProvider(judge)
    graph = build_app_graph(llm, ToolLoopEngine(llm), sandboxes, InMemorySaver())

    outcome = await EvalRunner(WorkflowService(graph), sandboxes).run(make_task(tmp_path))

    assert outcome.errored and not outcome.passed
    assert sandboxes.sandboxes == {}
