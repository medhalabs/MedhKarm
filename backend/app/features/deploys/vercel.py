"""Vercel: create a deployment from the files (inline, base64), then wait for it to build.

Previews get a unique URL (on Hobby accounts, protected by Vercel login: the founder, signed
in, can open it). Production deployments also get the project's `<name>.vercel.app` alias.
The token is only ever sent in the Authorization header and never logged.
"""

import asyncio
from contextlib import AsyncExitStack
from typing import Any

import httpx
from pydantic import SecretStr

from app.features.deploys.exceptions import DeployError
from app.features.deploys.schemas import DeployFile, Deployment

API = "https://api.vercel.com"
DONE = {"READY", "ERROR", "CANCELED"}


class VercelDeployTarget:
    def __init__(
        self,
        token: SecretStr | None,
        team: str | None = None,
        http: httpx.AsyncClient | None = None,
        poll_seconds: float = 3.0,
        timeout_seconds: float = 420.0,
    ) -> None:
        self._token = token.get_secret_value() if token else ""
        self._team = team
        self._http = http
        self._poll = poll_seconds
        self._timeout = timeout_seconds

    async def deploy(
        self, name: str, files: list[DeployFile], production: bool, framework: str | None
    ) -> Deployment:
        if not self._token:
            raise DeployError("No VERCEL_TOKEN set")
        body: dict[str, Any] = {
            "name": name,
            "files": [{"file": f.path, "data": f.data, "encoding": "base64"} for f in files],
            "projectSettings": {"framework": framework},
        }
        if production:
            body["target"] = "production"
        params = {"skipAutoDetectionConfirmation": "1", "forceNew": "1", **self._scope()}
        async with AsyncExitStack() as stack:
            http = self._http
            if http is None:
                http = await stack.enter_async_context(httpx.AsyncClient(timeout=60))
            created = await http.post(
                f"{API}/v13/deployments", json=body, params=params, headers=self._headers()
            )
            if not created.is_success:
                raise DeployError(
                    f"Vercel refused the deployment ({created.status_code}): {_message(created)}"
                )
            data = created.json()
            waited = 0.0
            while data.get("readyState") not in DONE and waited < self._timeout:
                await asyncio.sleep(self._poll)
                waited += self._poll
                polled = await http.get(
                    f"{API}/v13/deployments/{data['id']}",
                    params=self._scope(),
                    headers=self._headers(),
                )
                if polled.is_success:
                    data = polled.json()
        state = str(data.get("readyState") or "TIMEOUT")
        if state not in DONE:
            state = "TIMEOUT"
        url = _best_url(data, production)
        return Deployment(
            id=str(data.get("id", "")),
            url=url,
            target="production" if production else "preview",
            state=state,
            inspector_url=str(data.get("inspectorUrl") or ""),
            error=str(data.get("errorMessage") or "")[:500] if state != "READY" else "",
        )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def _scope(self) -> dict[str, str]:
        return {"slug": self._team} if self._team else {}


def _best_url(data: dict[str, Any], production: bool) -> str:
    """Production: the project's own alias (name.vercel.app) when assigned; else the unique URL."""
    aliases = [a for a in data.get("alias") or [] if isinstance(a, str)]
    if production and aliases:
        return f"https://{min(aliases, key=len)}"
    url = str(data.get("url") or "")
    return f"https://{url}" if url and not url.startswith("http") else url


def _message(response: httpx.Response) -> str:
    try:
        return str(response.json().get("error", {}).get("message", ""))[:300]
    except ValueError:
        return response.text[:300]
