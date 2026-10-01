"""Maps a project before the team changes it: files, languages, manifests, a code outline and
how to install and test it. Reads the sandbox with a few shell commands, no model call, so it
is cheap and the same every time. JavaScript/TypeScript and Python first."""

import json
import re
import shlex
import tomllib
from pathlib import PurePosixPath
from typing import Any

from app.features.repos.schemas import CodebaseMap
from app.features.sandbox.exceptions import SandboxError
from app.features.sandbox.interfaces import Sandbox

LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".html": "HTML",
    ".css": "CSS",
    ".sql": "SQL",
    ".go": "Go",
    ".rb": "Ruby",
    ".java": "Java",
    ".php": "PHP",
}
SKIP_DIRS = {
    "node_modules",
    "dist",
    "build",
    ".next",
    "venv",
    ".venv",
    "__pycache__",
    "vendor",
    "graphify-out",
}
MAX_TREE = 300
MAX_OUTLINE_FILES = 80
MAX_DEFS_PER_FILE = 15
TEST_GROUPS = ("test", "tests", "testing", "dev")

PY_DEF = re.compile(r"^(?:async\s+def|def|class)\s+([A-Za-z_]\w*)")
JS_DEF = re.compile(
    r"^(?:export\s+(?:default\s+)?)?(?:async\s+)?"
    r"(?:function\*?|class|const|let|interface|type|enum)\s+([A-Za-z_$][\w$]*)"
)
GREP_PATTERN = (
    r"^(async def|def|class) |^(export )?(default )?(async )?(function|class) "
    r"|^export (const|let|interface|type|enum) "
)


async def map_codebase(sandbox: Sandbox) -> CodebaseMap:
    files = await _project_files(sandbox)
    if not files:
        return CodebaseMap()
    languages: dict[str, int] = {}
    for path in files:
        language = LANGUAGES.get(PurePosixPath(path).suffix.lower())
        if language:
            languages[language] = languages.get(language, 0) + 1
    manifests, setup, tests = await _manifests(sandbox, set(files))
    if not tests and languages:  # no tests yet: the developers add them with the usual runner
        main = max(languages, key=lambda lang: languages[lang])
        tests = {"Python": ["python -m pytest -q"], "JavaScript": ["node --test"]}.get(main, [])
    tree = files[:MAX_TREE]
    if len(files) > MAX_TREE:
        tree.append(f"… and {len(files) - MAX_TREE} more")
    return CodebaseMap(
        file_count=len(files),
        languages=dict(sorted(languages.items(), key=lambda item: -item[1])),
        tree=tree,
        manifests=manifests,
        outline=await _outline(sandbox, files),
        readme=await _readme(sandbox, files),
        setup_command=" && ".join(setup),
        test_command=" && ".join(tests),
    )


async def _project_files(sandbox: Sandbox) -> list[str]:
    """Tracked files for a git checkout (respects .gitignore), else every file."""
    result = await sandbox.run("[ -d .git ] && git ls-files")
    files = result.output.splitlines() if result.ok else await sandbox.list_files()
    return sorted(
        f
        for f in files
        if f and not any(part in SKIP_DIRS or part.startswith(".") for part in f.split("/")[:-1])
    )


async def _manifests(
    sandbox: Sandbox, files: set[str]
) -> tuple[dict[str, str], list[str], list[str]]:
    """Summaries of package.json / pyproject.toml / requirements.txt at the project root, and
    the setup and test commands they imply."""
    manifests: dict[str, str] = {}
    setup: list[str] = []
    tests: list[str] = []

    if "package.json" in files:
        package = _json(await _read(sandbox, "package.json"))
        scripts: dict[str, Any] = package.get("scripts") or {}
        deps = [*(package.get("dependencies") or {}), *(package.get("devDependencies") or {})]
        manifests["package.json"] = _join(
            f"name {package.get('name', '?')}",
            f"scripts: {', '.join(scripts)}" if scripts else "",
            f"dependencies: {', '.join(deps[:20])}" + (" …" if len(deps) > 20 else ""),
        )
        tool = "npm"
        if "pnpm-lock.yaml" in files:
            tool = "pnpm"
        elif "yarn.lock" in files:
            tool = "yarn"
        if deps:
            setup.append(
                {
                    "npm": "npm ci --no-audit --no-fund"
                    if "package-lock.json" in files
                    else "npm install --no-audit --no-fund",
                    "pnpm": "corepack enable && pnpm install --frozen-lockfile",
                    "yarn": "corepack enable && yarn install --frozen-lockfile",
                }[tool]
            )
        test_script = str(scripts.get("test", ""))
        if test_script and "no test specified" not in test_script:
            tests.append(f"{tool} test")

    if "pyproject.toml" in files:
        pyproject = _toml(await _read(sandbox, "pyproject.toml"))
        project: dict[str, Any] = pyproject.get("project") or {}
        deps = [str(d) for d in project.get("dependencies") or []]
        manifests["pyproject.toml"] = _join(
            f"name {project.get('name', '?')}",
            f"dependencies: {', '.join(deps[:20])}" if deps else "",
        )
        if "build-system" in pyproject:  # src layouts only import once installed
            setup.append("pip install -q -e .")
        elif deps:
            setup.append("pip install -q " + " ".join(shlex.quote(d) for d in deps))
        test_deps = _test_dependencies(pyproject)
        if test_deps:
            setup.append("pip install -q " + " ".join(shlex.quote(d) for d in test_deps))
    for requirements in ("requirements.txt", "requirements-dev.txt"):
        if requirements in files:
            lines = [
                line.strip()
                for line in (await _read(sandbox, requirements)).splitlines()
                if line.strip() and not line.startswith("#")
            ]
            manifests[requirements] = ", ".join(lines[:20]) + (" …" if len(lines) > 20 else "")
            setup.append(f"pip install -q -r {requirements}")
    if any(_is_python_test(f) for f in files):
        tests.append("python -m pytest -q")
    return manifests, setup, tests


async def _outline(sandbox: Sandbox, files: list[str]) -> dict[str, list[str]]:
    sources = [f for f in files if PurePosixPath(f).suffix in LANGUAGES and not f.endswith(".css")]
    sources = sources[:MAX_OUTLINE_FILES]
    if not sources:
        return {}
    quoted = " ".join(shlex.quote(f) for f in sources)
    result = await sandbox.run(f"grep -HnE {shlex.quote(GREP_PATTERN)} -- {quoted}")
    outline: dict[str, list[str]] = {}
    for line in result.output.splitlines():
        path, _, rest = line.partition(":")
        _, _, text = rest.partition(":")
        match = (PY_DEF if path.endswith(".py") else JS_DEF).match(text)
        if not match:
            continue
        names = outline.setdefault(path, [])
        if match.group(1) not in names and len(names) < MAX_DEFS_PER_FILE:
            names.append(match.group(1))
    return outline


async def _readme(sandbox: Sandbox, files: list[str]) -> str:
    readme = next((f for f in files if f.lower() in ("readme.md", "readme", "readme.txt")), None)
    if not readme:
        return ""
    lines = (await _read(sandbox, readme)).splitlines()[:30]
    return "\n".join(lines).strip()[:1500]


async def _read(sandbox: Sandbox, path: str) -> str:
    try:
        return await sandbox.read_file(path)
    except SandboxError:
        return ""


def _test_dependencies(pyproject: dict[str, Any]) -> list[str]:
    """Packages the tests need: dependency groups and extras named test(s), testing or dev."""
    groups: dict[str, Any] = {
        **((pyproject.get("project") or {}).get("optional-dependencies") or {}),
        **(pyproject.get("dependency-groups") or {}),
    }
    found: list[str] = []
    for name in TEST_GROUPS:
        for dep in groups.get(name) or []:
            if isinstance(dep, str) and dep not in found:  # skips {include-group = ...}
                found.append(dep)
    return found


def _is_python_test(path: str) -> bool:
    name = PurePosixPath(path).name
    return name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def _json(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _toml(text: str) -> dict[str, Any]:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}


def _join(*parts: str) -> str:
    return "; ".join(p for p in parts if p)
