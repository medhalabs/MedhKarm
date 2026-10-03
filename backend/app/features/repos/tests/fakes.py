"""Test helpers: a sandbox that answers the mapper's shell commands from its files, and a
repository host that "clones" a small Python project."""

import re
import shlex

from app.features.repos.mapper import GREP_PATTERN
from app.features.repos.schemas import Delivery, DeliveryStatus, RepoSource
from app.features.sandbox.interfaces import Sandbox
from app.features.sandbox.providers.memory_provider import InMemorySandbox
from app.features.sandbox.schemas import CommandResult


def project_shell(command: str, files: dict[str, str]) -> CommandResult:
    """`git ls-files` (when there's a .git folder), `grep -HnE` and `git rev-parse` over
    in-memory files; anything else succeeds silently."""
    if command.startswith("[ -d .git ]"):
        tracked = [f for f in sorted(files) if not f.startswith(".git/")]
        if not any(f.startswith(".git/") for f in files):
            return CommandResult(exit_code=1, output="")
        return CommandResult(exit_code=0, output="\n".join(tracked))
    if command.startswith("grep -HnE"):
        parts = shlex.split(command)
        paths = parts[parts.index("--") + 1 :]
        pattern = re.compile(GREP_PATTERN)
        hits = [
            f"{path}:{n}:{line}"
            for path in paths
            for n, line in enumerate(files.get(path, "").splitlines(), 1)
            if pattern.search(line)
        ]
        return CommandResult(exit_code=0 if hits else 1, output="\n".join(hits))
    if command == "git rev-parse HEAD":
        ok = ".git/HEAD" in files
        return CommandResult(exit_code=0 if ok else 128, output="abc123\n" if ok else "fatal")
    return CommandResult(exit_code=0, output="")


def sandbox_with(files: dict[str, str]) -> InMemorySandbox:
    sandbox = InMemorySandbox("sb-1", project_shell)
    sandbox.files.update(files)
    return sandbox


class FakeHost:
    def __init__(self) -> None:
        self.clones = 0
        self.delivered: list[tuple[str, str, str]] = []
        self.published: list[tuple[str, str]] = []

    async def clone(self, source: RepoSource, sandbox: Sandbox) -> str:
        self.clones += 1
        assert isinstance(sandbox, InMemorySandbox)
        sandbox.files.update(
            {
                ".git/HEAD": "ref: refs/heads/dev",
                "requirements.txt": "fastapi\n",
                "app.py": "def create(): ...\n",
                "tests/test_app.py": "def test_create(): ...\n",
            }
        )
        return "abc123"

    async def deliver(
        self, source: RepoSource, sandbox: Sandbox, branch: str, title: str, body: str
    ) -> Delivery:
        self.delivered.append((branch, title, body))
        return Delivery(status=DeliveryStatus.OPENED, branch=branch, pull_request_url="u")

    async def publish(self, sandbox: Sandbox, name: str, description: str) -> Delivery:
        self.published.append((name, description))
        return Delivery(
            status=DeliveryStatus.CREATED, branch="main", repo_url=f"https://github.com/me/{name}"
        )
