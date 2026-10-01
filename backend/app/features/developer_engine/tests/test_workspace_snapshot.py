from app.features.developer_engine.engines.workspace_snapshot import changed_files, snapshot
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.sandbox.schemas import CommandResult


def test_lists_new_and_modified_files_only() -> None:
    before = {"keep.py": "aaa", "edit.py": "bbb", "gone.py": "ccc"}
    after = {"keep.py": "aaa", "edit.py": "zzz", "new.py": "ddd"}

    assert changed_files(before, after) == ["edit.py", "new.py"]


async def test_parses_sha1sum_output() -> None:
    def fake_hashes(command: str, files: dict[str, str]) -> CommandResult:
        return CommandResult(exit_code=0, output="abc123  app.py\ndef456  src/util.py\n")

    sandbox = await InMemorySandboxProvider(fake_hashes).create()

    assert await snapshot(sandbox) == {"app.py": "abc123", "src/util.py": "def456"}
