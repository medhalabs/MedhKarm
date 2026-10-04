import base64
import json

import httpx
from pydantic import SecretStr

from app.features.deploys.detect import detect_app
from app.features.deploys.schemas import AppKind, DeployFile, Deployment
from app.features.deploys.service import DeployService, project_name
from app.features.deploys.vercel import VercelDeployTarget
from app.features.sandbox.providers.memory_provider import InMemorySandbox
from app.features.sandbox.schemas import CommandResult


def reader(files: dict[str, str]):  # type: ignore[no-untyped-def]
    async def read(path: str) -> str:
        return files[path]

    return read


async def test_detects_what_kind_of_app_it_is() -> None:
    fastapi = {"app.py": "from fastapi import FastAPI\napp = FastAPI()\n"}
    nextjs = {"package.json": json.dumps({"dependencies": {"next": "15", "react": "19"}})}
    static = {"index.html": "<h1>hi</h1>", "style.css": ""}
    library = {"roman.py": "def to_roman(n): ...", "test_roman.py": ""}

    assert await detect_app(list(fastapi), reader(fastapi)) == AppKind.FASTAPI
    assert await detect_app(list(nextjs), reader(nextjs)) == AppKind.NEXTJS
    assert await detect_app(list(static), reader(static)) == AppKind.STATIC
    assert await detect_app(list(library), reader(library)) == AppKind.NONE


def test_project_names_follow_vercels_rules() -> None:
    assert project_name("BMI Calculator_v2!") == "bmi-calculator-v2"
    assert project_name("---") == "medhkarm-app"


def vercel(
    states: list[str], seen: list[httpx.Request], create_status: int = 200
) -> VercelDeployTarget:
    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.method == "POST":
            if create_status != 200:
                return httpx.Response(create_status, json={"error": {"message": "bad files"}})
            return httpx.Response(
                200, json={"id": "dpl_1", "url": "bmi-abc.vercel.app", "readyState": "QUEUED"}
            )
        state = states.pop(0)
        return httpx.Response(
            200,
            json={
                "id": "dpl_1",
                "url": "bmi-abc.vercel.app",
                "readyState": state,
                "alias": ["bmi.vercel.app"],
                "inspectorUrl": "https://vercel.com/i/1",
                "errorMessage": "build failed" if state == "ERROR" else None,
            },
        )

    return VercelDeployTarget(
        SecretStr("tok"),
        team="team-x",
        http=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
        poll_seconds=0,
        timeout_seconds=10,
    )


async def test_a_preview_is_created_and_waited_for() -> None:
    seen: list[httpx.Request] = []
    files = [DeployFile(path="index.html", data="PGgxPg==")]

    result = await vercel(["BUILDING", "READY"], seen).deploy("bmi", files, False, None)

    assert (result.state, result.url, result.target) == (
        "READY",
        "https://bmi-abc.vercel.app",
        "preview",
    )
    body = json.loads(seen[0].content)
    assert body["name"] == "bmi" and "target" not in body
    assert body["files"] == [{"file": "index.html", "data": "PGgxPg==", "encoding": "base64"}]
    assert seen[0].headers["authorization"] == "Bearer tok"
    assert seen[0].url.params["slug"] == "team-x"


async def test_production_uses_the_projects_own_address() -> None:
    result = await vercel(["READY"], []).deploy("bmi", [], True, None)

    assert (result.target, result.url) == ("production", "https://bmi.vercel.app")


async def test_failed_builds_and_refusals_are_reported() -> None:
    failed = await vercel(["ERROR"], []).deploy("bmi", [], False, None)
    assert (failed.state, failed.error) == ("ERROR", "build failed")

    service = DeployService(vercel([], [], create_status=400))
    box = InMemorySandbox("sb", lambda c, f: CommandResult(exit_code=0, output="aGk="))
    box.files["index.html"] = "<h1>hi</h1>"
    refused = await service.deploy(box, "bmi", production=False)
    assert refused.state == "ERROR" and "bad files" in refused.error


async def test_only_the_app_is_shipped_and_fastapi_gets_its_requirements() -> None:
    sent: list[list[DeployFile]] = []

    class Target:
        async def deploy(
            self, name: str, files: list[DeployFile], production: bool, framework: str | None
        ) -> Deployment:
            sent.append(files)
            return Deployment(state="READY", url="https://x.vercel.app")

    def shell(command: str, files: dict[str, str]) -> CommandResult:
        path = command.split(" ", 2)[2].strip("'")
        return CommandResult(exit_code=0, output=base64.b64encode(files[path].encode()).decode())

    box = InMemorySandbox("sb", shell)
    box.files.update(
        {
            "app.py": "from fastapi import FastAPI\napp = FastAPI()\n",
            "static/index.html": "<form></form>",
            "test_app.py": "def test(): ...",
            "tests/e2e/test_ui.py": "def test(page): ...",
            ".env": "SECRET=1",
        }
    )

    result = await DeployService(Target()).deploy(box, "BMI app", production=False)

    assert result.kind == AppKind.FASTAPI and result.ready
    assert sorted(f.path for f in sent[0]) == ["app.py", "requirements.txt", "static/index.html"]


async def test_libraries_arent_deployed() -> None:
    box = InMemorySandbox("sb", lambda c, f: CommandResult(exit_code=0, output=""))
    box.files["roman.py"] = "def to_roman(n): ..."

    result = await DeployService(VercelDeployTarget(None)).deploy(box, "roman", production=False)

    assert result.kind == AppKind.NONE and not result.ready
