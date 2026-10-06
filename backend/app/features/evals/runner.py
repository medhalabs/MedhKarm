"""Runs eval tasks through the real build workflow and scores them.

Per task, in a fresh sandbox:
1. copy in the starting project (and run the engine's prepare command, if any)
2. run the build graph: plan → develop → verify (the visible tests)
3. if it reaches the release gate, copy in the hidden checks and run them
4. reject at the gate, so the graph's finish step removes the sandbox

A task passes only if the visible tests AND the hidden checks pass. Model or sandbox failures
mark the task as errored instead: it's rerun, not counted against the team.
"""

import asyncio
import time
import uuid
from collections.abc import Callable

from app.features.evals.schemas import EvalTask, TaskOutcome
from app.features.evals.workspace import run_hidden_checks, seed_project
from app.features.models.exceptions import ModelCallError
from app.features.models.metering import metering
from app.features.sandbox.exceptions import SandboxError
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.service import WorkflowService

OnOutcome = Callable[[TaskOutcome], None]


class EvalRunner:
    def __init__(
        self,
        workflows: WorkflowService,
        sandboxes: SandboxProvider,
        prepare_command: str | None = None,
        task_timeout_seconds: float = 1200,
    ) -> None:
        self._workflows = workflows
        self._sandboxes = sandboxes
        self._prepare_command = prepare_command
        self._timeout = task_timeout_seconds

    async def run_all(
        self, tasks: list[EvalTask], parallel: int = 1, on_outcome: OnOutcome | None = None
    ) -> list[TaskOutcome]:
        limit = asyncio.Semaphore(parallel)

        async def one(task: EvalTask) -> TaskOutcome:
            async with limit:
                outcome = await self.run(task)
                if on_outcome:
                    on_outcome(outcome)
                return outcome

        return list(await asyncio.gather(*(one(task) for task in tasks)))

    async def run(self, task: EvalTask) -> TaskOutcome:
        started = time.monotonic()
        outcome = TaskOutcome(
            task_id=task.id,
            kind=task.kind,
            difficulty=task.difficulty,
            language=task.language,
            passed=False,
        )
        sandbox_id: str | None = None
        try:
            sandbox = await self._sandboxes.create()
            sandbox_id = sandbox.id
            if self._prepare_command:
                await sandbox.run(self._prepare_command, timeout_seconds=600)
            await seed_project(sandbox, task)
            with metering() as meter:  # counts every agent's model calls in this task
                try:
                    await asyncio.wait_for(
                        self._run_build(task, sandbox_id, outcome), self._timeout
                    )
                finally:
                    used = meter.total
                    if used.calls:
                        outcome.model_calls = used.calls
                        outcome.prompt_tokens = used.prompt_tokens
                        outcome.completion_tokens = used.completion_tokens
                        outcome.total_tokens = used.total_tokens
                        outcome.own_key = used.own_key
        except TimeoutError:
            outcome.error = f"Timed out after {self._timeout:.0f}s"
        except (ModelCallError, SandboxError) as exc:
            outcome.error = f"{type(exc).__name__}: {exc}"[:1000]
            outcome.errored = True
        except Exception as exc:  # one broken task must not stop the whole suite
            outcome.error = f"{type(exc).__name__}: {exc}"[:1000]
        finally:
            if sandbox_id:
                await self._sandboxes.destroy(sandbox_id)
        outcome.seconds = round(time.monotonic() - started, 1)
        outcome.passed = outcome.visible_passed and outcome.hidden_passed
        return outcome

    async def _run_build(self, task: EvalTask, sandbox_id: str, outcome: TaskOutcome) -> None:
        run_id = f"eval-{task.id}-{uuid.uuid4().hex[:8]}"
        result = await self._workflows.start(
            run_id, task.request.strip(), task.test_command, sandbox_id=sandbox_id
        )
        dev = result.state.get("dev_result", {})
        outcome.steps = int(dev.get("steps", 0))
        outcome.total_tokens = int(dev.get("total_tokens", 0))
        outcome.summary = str(dev.get("summary", ""))
        outcome.files_changed = list(dev.get("files_changed", []))
        outcome.visible_passed = bool(result.state.get("verified"))

        if result.waiting_for_approval:
            sandbox = await self._sandboxes.attach(sandbox_id)
            hidden = await run_hidden_checks(sandbox, task)
            outcome.hidden_passed = hidden.ok
            outcome.hidden_output = hidden.output[-2000:]
            await self._workflows.resume(run_id, approved=False, feedback="eval run")
