"""What kind of app the workspace holds, so it's deployed the right way (or not at all)."""

import json
import re
from collections.abc import Awaitable, Callable

from app.features.deploys.schemas import AppKind

PY_ENTRYPOINTS = [
    f"{folder}{name}.py"
    for folder in ("", "src/", "app/")
    for name in ("app", "index", "server", "main", "asgi")
]
FASTAPI_APP = re.compile(r"^\s*app\s*[:=].*FastAPI\(", re.MULTILINE)

Reader = Callable[[str], Awaitable[str]]


async def detect_app(files: list[str], read: Reader) -> AppKind:
    present = set(files)
    if "package.json" in present:
        try:
            manifest = json.loads(await read("package.json"))
        except (ValueError, OSError):
            manifest = {}
        deps = {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {})}
        if "next" in deps:
            return AppKind.NEXTJS
    for entry in PY_ENTRYPOINTS:
        if entry in present and FASTAPI_APP.search(await _safe(read, entry)):
            return AppKind.FASTAPI
    if "index.html" in present or "public/index.html" in present:
        return AppKind.STATIC
    return AppKind.NONE


async def _safe(read: Reader, path: str) -> str:
    try:
        return await read(path)
    except Exception:
        return ""
