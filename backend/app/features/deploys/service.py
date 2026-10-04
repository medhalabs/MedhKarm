"""DevOps (Neel): put the work online. A preview before the founder's release gate, production
once they approve. Only apps that can run online are deployed (see detect.py)."""

import base64
import re
import shlex
from pathlib import PurePosixPath

from app.features.deploys.detect import detect_app
from app.features.deploys.exceptions import DeployError
from app.features.deploys.interfaces import DeployTarget
from app.features.deploys.schemas import AppKind, DeployFile, Deployment
from app.features.sandbox.interfaces import Sandbox

MAX_FILES = 300
MAX_BYTES = 8_000_000
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "graphify-out",
    "tests",
}
SKIP_NAMES = re.compile(r"^(\.env.*|test_.*\.py|.*_test\.py|.*\.pyc|\.DS_Store)$")
FRAMEWORK = {AppKind.NEXTJS: "nextjs", AppKind.FASTAPI: None, AppKind.STATIC: None}


def project_name(name: str) -> str:
    """Vercel project names: lowercase letters, digits and single dashes, at most 100."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:100].strip("-") or "medhkarm-app"


class DeployService:
    def __init__(self, target: DeployTarget) -> None:
        self._target = target

    async def kind(self, sandbox: Sandbox) -> AppKind:
        return await detect_app(await sandbox.list_files(), sandbox.read_file)

    async def deploy(self, sandbox: Sandbox, name: str, production: bool) -> Deployment:
        """Deploy the workspace. Not an app: returns a NONE deployment. Problems come back in
        `error`, never as exceptions: a failed deploy mustn't lose the founder's work."""
        kind = await self.kind(sandbox)
        if kind == AppKind.NONE:
            return Deployment(kind=kind)
        try:
            files = await self._files(sandbox, kind)
            result = await self._target.deploy(
                project_name(name), files, production, FRAMEWORK.get(kind)
            )
        except DeployError as error:
            return Deployment(
                kind=kind,
                target="production" if production else "preview",
                state="ERROR",
                error=str(error),
            )
        return result.model_copy(update={"kind": kind})

    async def _files(self, sandbox: Sandbox, kind: AppKind) -> list[DeployFile]:
        paths = [p for p in await sandbox.list_files() if _shipped(p)]
        if len(paths) > MAX_FILES:
            raise DeployError(f"Too many files to deploy ({len(paths)}; at most {MAX_FILES})")
        files, total = [], 0
        for path in paths:
            result = await sandbox.run(f"base64 -w0 {shlex.quote(path)}")
            if not result.ok:
                continue
            total += len(result.output)
            if total > MAX_BYTES:
                raise DeployError("The app is too big to deploy this way (over 6 MB)")
            files.append(DeployFile(path=path, data=result.output.strip()))
        if kind == AppKind.FASTAPI and not {"requirements.txt", "pyproject.toml"} & set(paths):
            # Vercel installs dependencies from these; the sandbox had FastAPI preinstalled
            files.append(DeployFile(path="requirements.txt", data=_b64("fastapi\n")))
        return files


def _shipped(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return not (SKIP_DIRS & set(parts[:-1])) and not SKIP_NAMES.match(parts[-1])


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()
