import json

import httpx
import pytest
from pydantic import SecretStr

from app.features.repos.exceptions import RepoError
from app.features.repos.github import GitHubRepoHost
from app.features.repos.schemas import DeliveryStatus, RepoSource
from app.features.sandbox.providers.memory_provider import InMemorySandbox
from app.features.sandbox.schemas import CommandResult

SOURCE = RepoSource(url="https://github.com/medhalabs/shop")
TOKEN = "ghp_secret123"


class Git:
    """Answers git commands like a checkout with uncommitted work."""

    def __init__(self, changed: str = " M cart.js", branch: str = "main", fail: str = ""):
        self.changed, self.branch, self.fail = changed, branch, fail

    def __call__(self, command: str, files: dict[str, str]) -> CommandResult:
        if self.fail and self.fail in command:
            return CommandResult(exit_code=128, output=f"fatal: denied for {TOKEN}")
        if "status --porcelain" in command:
            return CommandResult(exit_code=0, output=self.changed)
        if "--abbrev-ref" in command:
            return CommandResult(exit_code=0, output=self.branch)
        if "rev-parse HEAD" in command:
            return CommandResult(exit_code=0, output="deadbeef\n")
        return CommandResult(exit_code=0, output="")


def github(handler: httpx.MockTransport, token: str | None = TOKEN) -> GitHubRepoHost:
    return GitHubRepoHost(SecretStr(token) if token else None, httpx.AsyncClient(transport=handler))


def pulls_api(seen: list[httpx.Request], create_status: int = 201) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "GET" and request.url.path == "/repos/medhalabs/shop":
            return httpx.Response(200, json={"default_branch": "main"})
        if request.method == "POST":
            if create_status != 201:
                return httpx.Response(create_status, json={"message": "exists"})
            return httpx.Response(
                201, json={"html_url": "https://github.com/medhalabs/shop/pull/7"}
            )
        return httpx.Response(200, json=[{"html_url": "https://github.com/medhalabs/shop/pull/3"}])

    return httpx.MockTransport(handle)


async def test_clone_passes_the_token_as_a_one_off_header() -> None:
    sandbox = InMemorySandbox("sb", Git())

    commit = await github(pulls_api([])).clone(SOURCE, sandbox)

    clone = sandbox.commands[0]
    assert commit == "deadbeef"
    assert "clone" in clone and "http.extraHeader=" in clone and TOKEN not in clone  # base64
    assert not any("git config" in c or "remote set-url" in c for c in sandbox.commands)
    assert any(".git/info/exclude" in c and "node_modules/" in c for c in sandbox.commands)


async def test_clone_errors_never_show_the_token() -> None:
    sandbox = InMemorySandbox("sb", Git(fail="clone"))
    with pytest.raises(RepoError) as error:
        await github(pulls_api([])).clone(SOURCE, sandbox)
    assert TOKEN not in str(error.value) and "***" in str(error.value)


async def test_delivers_a_branch_and_opens_a_pull_request_to_the_default_branch() -> None:
    seen: list[httpx.Request] = []
    sandbox = InMemorySandbox("sb", Git())

    delivery = await github(pulls_api(seen)).deliver(
        SOURCE, sandbox, "medhkarm/run1", "Add GST", "Body"
    )

    assert delivery.status == DeliveryStatus.OPENED
    assert delivery.pull_request_url == "https://github.com/medhalabs/shop/pull/7"
    assert (delivery.branch, delivery.commit) == ("medhkarm/run1", "deadbeef")
    assert any("checkout -q -B medhkarm/run1" in c and "commit" in c for c in sandbox.commands)
    assert any("push" in c and "HEAD:refs/heads/medhkarm/run1" in c for c in sandbox.commands)
    post = next(r for r in seen if r.method == "POST")
    assert json.loads(post.content) == {
        "title": "Add GST",
        "head": "medhkarm/run1",
        "base": "main",
        "body": "Body",
    }
    assert post.headers["authorization"] == f"Bearer {TOKEN}"


async def test_a_retry_after_the_commit_reuses_the_open_pull_request() -> None:
    sandbox = InMemorySandbox("sb", Git(changed="", branch="medhkarm/run1"))

    delivery = await github(pulls_api([], create_status=422)).deliver(
        SOURCE, sandbox, "medhkarm/run1", "Add GST", "Body"
    )

    assert delivery.pull_request_url == "https://github.com/medhalabs/shop/pull/3"
    assert not any(" commit " in c for c in sandbox.commands)  # already committed


async def test_nothing_changed_means_no_pull_request() -> None:
    sandbox = InMemorySandbox("sb", Git(changed=""))
    delivery = await github(pulls_api([])).deliver(SOURCE, sandbox, "medhkarm/r", "t", "b")
    assert delivery.status == DeliveryStatus.NO_CHANGES
    assert not any("push" in c for c in sandbox.commands)


async def test_without_a_token_delivery_is_skipped_with_a_reason() -> None:
    sandbox = InMemorySandbox("sb", Git())
    delivery = await github(pulls_api([]), token=None).deliver(SOURCE, sandbox, "b", "t", "b")
    assert delivery.status == DeliveryStatus.SKIPPED and "GITHUB_TOKEN" in delivery.reason
    assert sandbox.commands == []


async def test_failed_push_is_an_error_without_the_token() -> None:
    sandbox = InMemorySandbox("sb", Git(fail="push"))
    with pytest.raises(RepoError) as error:
        await github(pulls_api([])).deliver(SOURCE, sandbox, "medhkarm/r", "t", "b")
    assert TOKEN not in str(error.value)


def create_api(seen: list[httpx.Request], create_status: int = 201) -> httpx.MockTransport:
    repo = {
        "html_url": "https://github.com/me/roman-3f9a2c",
        "clone_url": "https://github.com/me/roman-3f9a2c.git",
    }

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "POST" and request.url.path == "/user/repos":
            return httpx.Response(create_status, json=repo if create_status == 201 else {})
        if request.url.path == "/user":
            return httpx.Response(200, json={"login": "me"})
        if request.url.path == "/repos/me/roman-3f9a2c":
            return httpx.Response(200, json=repo)
        return httpx.Response(404)

    return httpx.MockTransport(handle)


class NewProject(Git):
    """A workspace with no git repository yet, then one with the work committed."""

    def __call__(self, command: str, files: dict[str, str]) -> CommandResult:
        if command == "git rev-parse --git-dir":
            return CommandResult(exit_code=128, output="fatal: not a git repository")
        return super().__call__(command, files)


async def test_publish_creates_a_private_repo_and_pushes_main() -> None:
    seen: list[httpx.Request] = []
    sandbox = InMemorySandbox("sb", NewProject(changed="A roman.py"))

    delivery = await github(create_api(seen)).publish(sandbox, "roman-3f9a2c", "Roman numerals")

    assert delivery.status == DeliveryStatus.CREATED
    assert delivery.repo_url == "https://github.com/me/roman-3f9a2c"
    assert (delivery.branch, delivery.commit) == ("main", "deadbeef")
    assert json.loads(seen[0].content) == {
        "name": "roman-3f9a2c",
        "description": "Roman numerals",
        "private": True,
    }
    assert any(c.startswith("git init -q -b main") for c in sandbox.commands)
    push = next(c for c in sandbox.commands if " push " in c)
    assert "HEAD:refs/heads/main" in push and "--force" not in push and TOKEN not in push


async def test_publish_retry_reuses_the_repo_it_created() -> None:
    seen: list[httpx.Request] = []
    sandbox = InMemorySandbox("sb", Git(changed=""))  # already committed by the first try

    delivery = await github(create_api(seen, create_status=422)).publish(
        sandbox, "roman-3f9a2c", "Roman numerals"
    )

    assert delivery.repo_url == "https://github.com/me/roman-3f9a2c"
    assert [r.url.path for r in seen] == ["/user/repos", "/user", "/repos/me/roman-3f9a2c"]


async def test_publish_without_a_token_is_skipped() -> None:
    sandbox = InMemorySandbox("sb", Git())
    delivery = await github(create_api([]), token=None).publish(sandbox, "x", "y")
    assert delivery.status == DeliveryStatus.SKIPPED and sandbox.commands == []


async def test_pull_request_state_and_squash_merge() -> None:
    seen: list[httpx.Request] = []
    pr = "https://github.com/medhalabs/shop/pull/7"

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "PUT":
            return httpx.Response(200, json={"merged": True})
        return httpx.Response(200, json={"state": "closed", "merged": True})

    host = github(httpx.MockTransport(handle))

    assert await host.pull_request_state(pr) == "merged"
    assert await host.merge_pull_request(pr, "Add streaks")
    assert seen[0].url.path == "/repos/medhalabs/shop/pulls/7"
    assert seen[1].url.path == "/repos/medhalabs/shop/pulls/7/merge"
    assert b'"merge_method":"squash"' in seen[1].content.replace(b" ", b"")


async def test_open_and_closed_pull_requests_and_refused_merges() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        if request.method == "PUT":
            return httpx.Response(405, json={"message": "not mergeable"})
        number = request.url.path.rsplit("/", 1)[-1]
        state = "open" if number == "1" else "closed"
        return httpx.Response(200, json={"state": state, "merged": False})

    host = github(httpx.MockTransport(handle))

    assert await host.pull_request_state("https://github.com/a/b/pull/1") == "open"
    assert await host.pull_request_state("https://github.com/a/b/pull/2") == "closed"
    assert not await host.merge_pull_request("https://github.com/a/b/pull/1", "t")
    assert not await github(httpx.MockTransport(handle), token=None).merge_pull_request(
        "https://github.com/a/b/pull/1", "t"
    )
