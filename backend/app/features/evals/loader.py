"""Reads eval tasks and their files from disk.

Layout under the evals root (default `backend/evals/`):

    repos/<repo>/...              starting projects shared by several tasks
    tasks/<id>/task.toml          the task definition
    tasks/<id>/checks/...         hidden acceptance tests, copied in after the team finishes
    tasks/<id>/solution/...       reference solution, used only by `validate`
"""

import tomllib
from pathlib import Path

from app.features.evals.exceptions import EvalTaskError
from app.features.evals.schemas import EvalTask

SKIP_PARTS = {"__pycache__", ".pytest_cache", "node_modules"}


def load_tasks(root: Path, only: list[str] | None = None) -> list[EvalTask]:
    tasks = [_load_task(root, path) for path in sorted((root / "tasks").glob("*/task.toml"))]
    if only:
        known = {task.id for task in tasks}
        missing = [task_id for task_id in only if task_id not in known]
        if missing:
            raise EvalTaskError(f"Unknown task ids: {', '.join(missing)}")
        tasks = [task for task in tasks if task.id in only]
    return tasks


def read_tree(directory: Path | None) -> dict[str, str]:
    """All text files under `directory`, keyed by path relative to it."""
    if directory is None or not directory.is_dir():
        return {}
    files: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if path.is_file() and not SKIP_PARTS.intersection(relative.parts):
            files[relative.as_posix()] = path.read_text(encoding="utf-8")
    return files


def _load_task(root: Path, toml_path: Path) -> EvalTask:
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    task_dir = toml_path.parent
    if data.get("id") != task_dir.name:
        raise EvalTaskError(f"{toml_path}: id must equal its folder name ({task_dir.name})")
    repo_dir = root / "repos" / data["repo"] if data.get("repo") else None
    if repo_dir is not None and not repo_dir.is_dir():
        raise EvalTaskError(f"{toml_path}: repo {data['repo']!r} not found in {root / 'repos'}")
    return EvalTask(**data, task_dir=task_dir, repo_dir=repo_dir)
