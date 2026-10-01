from app.features.developer_engine.engines.workspace_snapshot import changed_files, snapshot
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider


def test_lists_new_and_modified_files_only() -> None:
    before = {"keep.py": "aaa", "edit.py": "bbb", "gone.py": "ccc"}
    after = {"keep.py": "aaa", "edit.py": "zzz", "new.py": "ddd"}

    assert changed_files(before, after) == ["edit.py", "new.py"]


async def test_snapshot_hashes_files_and_skips_hidden_ones() -> None:
    sandbox = await InMemorySandboxProvider().create()
    await sandbox.write_file("app.py", "x = 1")
    await sandbox.write_file("src/util.py", "y = 2")
    await sandbox.write_file(".eval_checks/test_hidden.py", "secret")

    first = await snapshot(sandbox)
    await sandbox.write_file("app.py", "x = 2")
    second = await snapshot(sandbox)

    assert sorted(first) == ["app.py", "src/util.py"]
    assert changed_files(first, second) == ["app.py"]
