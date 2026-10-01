"""Checks that every task is fair and not already solved, without calling any model.

For each task, in a fresh sandbox:
1. starting project only → the hidden checks must FAIL (otherwise the task is free)
2. + reference solution → the visible tests and the hidden checks must PASS
"""

import asyncio

from app.features.evals.schemas import EvalTask, ValidationOutcome
from app.features.evals.workspace import apply_solution, run_hidden_checks, seed_project
from app.features.sandbox.interfaces import SandboxProvider


class TaskValidator:
    def __init__(self, sandboxes: SandboxProvider, prepare_command: str | None = None) -> None:
        self._sandboxes = sandboxes
        self._prepare_command = prepare_command

    async def validate_all(
        self, tasks: list[EvalTask], parallel: int = 4
    ) -> list[ValidationOutcome]:
        limit = asyncio.Semaphore(parallel)

        async def one(task: EvalTask) -> ValidationOutcome:
            async with limit:
                return await self.validate(task)

        return list(await asyncio.gather(*(one(task) for task in tasks)))

    async def validate(self, task: EvalTask) -> ValidationOutcome:
        sandbox = await self._sandboxes.create()
        try:
            if self._prepare_command:
                await sandbox.run(self._prepare_command, timeout_seconds=600)
            await seed_project(sandbox, task)
            before = await run_hidden_checks(sandbox, task)

            await apply_solution(sandbox, task)
            visible = await sandbox.run(task.test_command, timeout_seconds=300)
            after = await run_hidden_checks(sandbox, task)

            detail = ""
            if before.ok:
                detail += "hidden checks already pass on the starting project. "
            if not visible.ok:
                detail += f"solution fails visible tests: {visible.output[-600:]} "
            if not after.ok:
                detail += f"solution fails hidden checks: {after.output[-600:]}"
            return ValidationOutcome(
                task_id=task.id,
                fixture_fails_checks=not before.ok,
                solution_passes=visible.ok and after.ok,
                detail=detail.strip(),
            )
        finally:
            await self._sandboxes.destroy(sandbox.id)
