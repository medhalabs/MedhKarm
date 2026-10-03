"""GitHub: clone into the sandbox, then push a branch and open a pull request with the work.
For a new project, create a private repository and push the work to its `main` branch.

The token never touches the disk: git gets it as a one-off `http.extraHeader` on the clone and
push commands only (not stored in .git/config, where agent-run code could read it), and it is
scrubbed from any output we keep. Without a token, public repositories still clone; delivery
is skipped with a reason.
"""

import base64
import shlex
from contextlib import AsyncExitStack

import httpx
from pydantic import SecretStr

from app.features.repos.exceptions import RepoError
from app.features.repos.schemas import Delivery, DeliveryStatus, RepoSource
from app.features.sandbox.interfaces import Sandbox

API = "https://api.github.com"
AUTHOR = "-c user.name='MedhKarm' -c user.email='team@medhkarm.ai'"
CLONE_TIMEOUT = 300
# Never committed, even if the repository's own .gitignore misses them (setup and tests make them)
LOCAL_ONLY = [
    "node_modules/",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    ".venv/",
    "graphify-out/",
]


class GitHubRepoHost:
    def __init__(self, token: SecretStr | None = None, http: httpx.AsyncClient | None = None):
        self._token = token.get_secret_value() if token else ""
        self._http = http

    async def clone(self, source: RepoSource, sandbox: Sandbox) -> str:
        branch = f"--branch {shlex.quote(source.branch)} " if source.branch else ""
        result = await sandbox.run(
            f"git {self._auth()} clone --quiet --depth 50 {branch}{shlex.quote(source.url)} .",
            timeout_seconds=CLONE_TIMEOUT,
        )
        if not result.ok:
            raise RepoError(f"Couldn't clone {source.url}: {self._scrub(result.output)[-500:]}")
        patterns = " ".join(shlex.quote(p) for p in LOCAL_ONLY)
        await sandbox.run(f"printf '%s\\n' {patterns} >> .git/info/exclude")
        return (await sandbox.run("git rev-parse HEAD")).output.strip()

    async def deliver(
        self, source: RepoSource, sandbox: Sandbox, branch: str, title: str, body: str
    ) -> Delivery:
        if not self._token:
            return Delivery(
                status=DeliveryStatus.SKIPPED,
                reason="No GITHUB_TOKEN set, so the work couldn't be pushed to GitHub",
            )
        status = await sandbox.run("git add -A && git status --porcelain")
        if not status.ok:
            raise RepoError(f"Couldn't read the work's changes: {status.output[-500:]}")
        current = await sandbox.run("git rev-parse --abbrev-ref HEAD")
        committed = current.output.strip() == branch  # a retry after the commit
        if not status.output.strip() and not committed:
            return Delivery(status=DeliveryStatus.NO_CHANGES, reason="The work changed no files")
        if status.output.strip():
            commit = await sandbox.run(
                f"git checkout -q -B {shlex.quote(branch)} && "
                f"git {AUTHOR} commit -q -m {shlex.quote(title)}"
            )
            if not commit.ok:
                raise RepoError(f"Couldn't commit the work: {commit.output[-500:]}")
        sha = (await sandbox.run("git rev-parse HEAD")).output.strip()
        push = await sandbox.run(
            f"git {self._auth()} push --quiet --force origin "
            f"{shlex.quote(f'HEAD:refs/heads/{branch}')}",
            timeout_seconds=CLONE_TIMEOUT,
        )
        if not push.ok:
            raise RepoError(f"Couldn't push to {source.url}: {self._scrub(push.output)[-500:]}")
        url = await self._open_pull_request(source, branch, title, body)
        return Delivery(
            status=DeliveryStatus.OPENED,
            branch=branch,
            commit=sha,
            pull_request_url=url,
        )

    async def _open_pull_request(
        self, source: RepoSource, branch: str, title: str, body: str
    ) -> str:
        repo = f"{API}/repos/{source.owner}/{source.name}"
        headers = self._headers()
        async with AsyncExitStack() as stack:
            http = await self._client(stack)
            base = source.branch or await self._default_branch(http, repo, headers)
            response = await http.post(
                f"{repo}/pulls",
                headers=headers,
                json={"title": title, "head": branch, "base": base, "body": body},
            )
            if response.status_code == 422:  # already open for this branch (a retry): reuse it
                existing = await http.get(
                    f"{repo}/pulls",
                    headers=headers,
                    params={"head": f"{source.owner}:{branch}", "state": "open"},
                )
                if existing.is_success and existing.json():
                    return str(existing.json()[0]["html_url"])
            if not response.is_success:
                raise RepoError(
                    f"GitHub didn't open the pull request ({response.status_code}): "
                    f"{response.text[:300]}"
                )
            return str(response.json()["html_url"])

    async def publish(self, sandbox: Sandbox, name: str, description: str) -> Delivery:
        if not self._token:
            return Delivery(
                status=DeliveryStatus.SKIPPED,
                reason="No GITHUB_TOKEN set, so no repository was created for the work",
            )
        if not (await sandbox.run("git rev-parse --git-dir")).ok:
            patterns = " ".join(shlex.quote(p) for p in LOCAL_ONLY)
            await sandbox.run(
                f"git init -q -b main && printf '%s\\n' {patterns} >> .git/info/exclude"
            )
        status = await sandbox.run("git add -A && git status --porcelain")
        if not status.ok:
            raise RepoError(f"Couldn't read the work's files: {status.output[-500:]}")
        if status.output.strip():
            commit = await sandbox.run(
                f"git {AUTHOR} commit -q -m {shlex.quote(description[:200] or 'First version')}"
            )
            if not commit.ok:
                raise RepoError(f"Couldn't commit the work: {commit.output[-500:]}")
        head = await sandbox.run("git rev-parse HEAD")
        if not head.ok:  # nothing was ever committed: an empty workspace
            return Delivery(status=DeliveryStatus.NO_CHANGES, reason="The work has no files")
        html_url, clone_url = await self._create_repository(name, description)
        push = await sandbox.run(
            f"git {self._auth()} push --quiet {shlex.quote(clone_url)} HEAD:refs/heads/main",
            timeout_seconds=CLONE_TIMEOUT,
        )
        if not push.ok:  # never forced: an existing repository's work is left alone
            raise RepoError(f"Couldn't push to {html_url}: {self._scrub(push.output)[-500:]}")
        return Delivery(
            status=DeliveryStatus.CREATED,
            branch="main",
            commit=head.output.strip(),
            repo_url=html_url,
        )

    async def _create_repository(self, name: str, description: str) -> tuple[str, str]:
        """Creates the private repository (or finds the one an earlier attempt created);
        returns its web address and clone address."""
        headers = self._headers()
        about = " ".join(description.split())[:300]
        async with AsyncExitStack() as stack:
            http = await self._client(stack)
            created = await http.post(
                f"{API}/user/repos",
                headers=headers,
                json={"name": name, "description": about, "private": True},
            )
            if created.status_code == 422:  # name taken: ours from a retry, or the founder's
                me = await http.get(f"{API}/user", headers=headers)
                if not me.is_success:
                    raise RepoError(
                        f"GitHub didn't say who the token belongs to ({me.status_code})"
                    )
                created = await http.get(
                    f"{API}/repos/{me.json()['login']}/{name}", headers=headers
                )
            if not created.is_success:
                raise RepoError(
                    f"GitHub didn't create the repository {name} ({created.status_code}): "
                    f"{created.text[:300]}"
                )
            data = created.json()
            return str(data["html_url"]), str(data["clone_url"])

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _client(self, stack: AsyncExitStack) -> httpx.AsyncClient:
        """The client tests passed in, or a new one closed with `stack`."""
        if self._http is not None:
            return self._http
        return await stack.enter_async_context(httpx.AsyncClient(timeout=30))

    async def _default_branch(
        self, http: httpx.AsyncClient, repo: str, headers: dict[str, str]
    ) -> str:
        response = await http.get(repo, headers=headers)
        if not response.is_success:
            raise RepoError(f"GitHub didn't find the repository ({response.status_code})")
        return str(response.json()["default_branch"])

    def _auth(self) -> str:
        if not self._token:
            return ""
        basic = base64.b64encode(f"x-access-token:{self._token}".encode()).decode()
        return f"-c http.extraHeader={shlex.quote(f'Authorization: Basic {basic}')}"

    def _scrub(self, text: str) -> str:
        if not self._token:
            return text
        basic = base64.b64encode(f"x-access-token:{self._token}".encode()).decode()
        return text.replace(self._token, "***").replace(basic, "***")
