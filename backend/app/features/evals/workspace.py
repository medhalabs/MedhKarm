"""Puts eval files into a sandbox and runs the hidden checks."""

import shlex

from app.features.evals.loader import read_tree
from app.features.evals.schemas import EvalTask
from app.features.sandbox.interfaces import Sandbox
from app.features.sandbox.schemas import CommandResult

CHECKS_DIR = ".eval_checks"  # hidden from the team: list_files skips dot-folders


async def upload(sandbox: Sandbox, files: dict[str, str], prefix: str = "") -> None:
    for path, content in files.items():
        await sandbox.write_file(f"{prefix}{path}", content)


async def seed_project(sandbox: Sandbox, task: EvalTask) -> None:
    """Copy the task's starting project (if any) into the workspace."""
    await upload(sandbox, read_tree(task.repo_dir))


async def run_hidden_checks(sandbox: Sandbox, task: EvalTask) -> CommandResult:
    await upload(sandbox, read_tree(task.task_dir / "checks"), prefix=f"{CHECKS_DIR}/")
    return await sandbox.run(task.check_command, timeout_seconds=300)


async def apply_solution(sandbox: Sandbox, task: EvalTask) -> None:
    for path in task.solution_delete:
        await sandbox.run(f"rm -rf {shlex.quote(path)}")
    await upload(sandbox, read_tree(task.task_dir / "solution"))
