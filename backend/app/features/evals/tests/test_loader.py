from pathlib import Path

import pytest

from app.features.evals.exceptions import EvalTaskError
from app.features.evals.loader import load_tasks, read_tree

TASK = """
id = "{id}"
title = "T"
kind = "feature"
difficulty = 1
language = "python"
test_command = "pytest"
check_command = "pytest .eval_checks"
request = "Do it"
{extra}
"""


def make_root(
    tmp_path: Path, task_id: str = "t1", extra: str = "", folder: str | None = None
) -> Path:
    task_dir = tmp_path / "tasks" / (folder or task_id)
    task_dir.mkdir(parents=True)
    (task_dir / "task.toml").write_text(TASK.format(id=task_id, extra=extra))
    return tmp_path


def test_loads_task_and_repo(tmp_path: Path) -> None:
    root = make_root(tmp_path, extra='repo = "shop"')
    (root / "repos" / "shop").mkdir(parents=True)

    [task] = load_tasks(root)

    assert task.id == "t1"
    assert task.repo_dir == root / "repos" / "shop"


def test_id_must_match_folder(tmp_path: Path) -> None:
    with pytest.raises(EvalTaskError):
        load_tasks(make_root(tmp_path, task_id="t1", folder="other"))


def test_missing_repo_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(EvalTaskError):
        load_tasks(make_root(tmp_path, extra='repo = "nope"'))


def test_filter_by_id_and_unknown_ids(tmp_path: Path) -> None:
    root = make_root(tmp_path)
    assert [t.id for t in load_tasks(root, ["t1"])] == ["t1"]
    with pytest.raises(EvalTaskError):
        load_tasks(root, ["missing"])


def test_read_tree_skips_caches(tmp_path: Path) -> None:
    (tmp_path / "pkg" / "__pycache__").mkdir(parents=True)
    (tmp_path / "pkg" / "a.py").write_text("x = 1")
    (tmp_path / "pkg" / "__pycache__" / "a.pyc").write_text("junk")

    assert read_tree(tmp_path) == {"pkg/a.py": "x = 1"}
    assert read_tree(None) == {}


def test_real_suite_has_twenty_valid_tasks() -> None:
    root = Path(__file__).resolve().parents[4] / "evals"
    tasks = load_tasks(root)
    assert len(tasks) == 20
    assert all(
        (t.task_dir / "checks").is_dir() and (t.task_dir / "solution").is_dir() for t in tasks
    )
