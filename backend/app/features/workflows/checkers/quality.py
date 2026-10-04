"""QA's quality checks beyond the tests: the project's own build, type-check and lint, plus a
syntax check of every Python file the team changed. Found from the workspace at check time, so
new projects get checked by whatever the developers set up.

A check that already failed before the team started (`checks_baseline`, measured when the
project was connected) is reported but doesn't block: the founder's old problems aren't the
team's to fix in this run. A project that doesn't configure a tool isn't checked with it."""

import json
import shlex
import tomllib
from typing import Any

from app.features.sandbox.exceptions import SandboxError
from app.features.sandbox.interfaces import Sandbox
from app.features.workflows.interfaces import WorkChecker
from app.features.workflows.schemas import CheckResult, CheckRun, QualityCheck
from app.features.workflows.state import BuildState

CHECK_TIMEOUT = 600
NOT_INSTALLED = 127  # the shell's "command not found"
TYPECHECK_SCRIPTS = ("typecheck", "type-check", "check-types", "tsc")
RUFF_CONFIGS = ("ruff.toml", ".ruff.toml")
MYPY_CONFIGS = ("mypy.ini", ".mypy.ini")
# Parses without writing bytecode into the workspace (py_compile would).
SYNTAX_COMMAND = (
    'python -c "import ast, sys; [ast.parse(open(f).read(), f) for f in sys.argv[1:]]" '
)


async def detect_checks(sandbox: Sandbox, changed: list[str] | None = None) -> list[QualityCheck]:
    """The checks this workspace supports, in the order they run. `changed` adds a syntax check
    of the changed Python files (left out when measuring the baseline)."""
    files = set(await sandbox.list_files())
    checks: list[QualityCheck] = []
    python_changed = [f for f in changed or [] if f.endswith(".py") and f in files]
    if python_changed:
        checks.append(
            QualityCheck(
                name="syntax",
                command=SYNTAX_COMMAND + " ".join(shlex.quote(f) for f in python_changed),
            )
        )
    if "package.json" in files:
        checks += _node_checks(_json(await _read(sandbox, "package.json")), files)
    pyproject = _toml(await _read(sandbox, "pyproject.toml")) if "pyproject.toml" in files else {}
    tools: dict[str, Any] = pyproject.get("tool") or {}
    if "ruff" in tools or files & set(RUFF_CONFIGS):
        checks.append(QualityCheck(name="ruff", command="ruff check ."))
    if "mypy" in tools or files & set(MYPY_CONFIGS):
        checks.append(QualityCheck(name="mypy", command="mypy ."))
    return checks


async def run_checks(sandbox: Sandbox, checks: list[QualityCheck]) -> list[CheckRun]:
    """Runs every check, even after one fails, so a fix sees all the problems at once."""
    runs: list[CheckRun] = []
    for check in checks:
        result = await sandbox.run(check.command, timeout_seconds=CHECK_TIMEOUT)
        runs.append(
            CheckRun(
                name=check.name,
                command=check.command,
                passed=result.ok,
                skipped=result.exit_code == NOT_INSTALLED,
                output=result.output[-1500:],
            )
        )
    return runs


async def measure_baseline(sandbox: Sandbox) -> dict[str, bool]:
    """Which checks pass on the project as the team found it (check name -> passed)."""
    return {
        run.name: run.passed
        for run in await run_checks(sandbox, await detect_checks(sandbox))
        if not run.skipped
    }


class QualityChecker:
    """Tests first (the `tests` checker), then the quality checks. Passes only when the tests
    pass and no check fails that passed (or didn't exist) before the team started."""

    def __init__(self, tests: WorkChecker) -> None:
        self._tests = tests

    async def check(self, state: BuildState, sandbox: Sandbox) -> CheckResult:
        tests = await self._tests.check(state, sandbox)
        changed = list(state.get("dev_result", {}).get("files_changed", []))
        baseline = state.get("checks_baseline", {})
        runs = [
            CheckRun(name="tests", command=state.get("test_command", ""), passed=tests.passed),
            *(
                run.model_copy(update={"already_failing": baseline.get(run.name) is False})
                for run in await run_checks(sandbox, await detect_checks(sandbox, changed))
            ),
        ]
        blocking = [r for r in runs[1:] if r.blocks]
        parts = [tests.output] if tests.output else []
        parts += [f"$ {r.command}\n{r.output}".strip() for r in blocking]
        return CheckResult(
            passed=tests.passed and not blocking,
            output="\n\n".join(parts)[-4000:],
            checks=runs,
        )


async def _read(sandbox: Sandbox, path: str) -> str:
    try:
        return await sandbox.read_file(path)
    except SandboxError:
        return ""


def _node_checks(package: dict[str, Any], files: set[str]) -> list[QualityCheck]:
    """npm/pnpm/yarn scripts for type-check, lint and build; `tsc --noEmit` for a TypeScript
    project with no type-check script. Installs first when dependencies aren't installed."""
    scripts: dict[str, Any] = package.get("scripts") or {}
    deps = {**(package.get("dependencies") or {}), **(package.get("devDependencies") or {})}
    tool = "pnpm" if "pnpm-lock.yaml" in files else "yarn" if "yarn.lock" in files else "npm"
    run = {"npm": "npm run", "pnpm": "pnpm run", "yarn": "yarn run"}[tool]
    install = {
        "npm": "npm ci --no-audit --no-fund"
        if "package-lock.json" in files
        else "npm install --no-audit --no-fund",
        "pnpm": "corepack enable && pnpm install --frozen-lockfile",
        "yarn": "corepack enable && yarn install --frozen-lockfile",
    }[tool]
    prefix = f"[ -d node_modules ] || {install}; " if deps else ""
    checks: list[QualityCheck] = []
    typecheck = next((s for s in TYPECHECK_SCRIPTS if s in scripts), None)
    if typecheck:
        checks.append(QualityCheck(name="types", command=f"{prefix}{run} {typecheck}"))
    elif "tsconfig.json" in files and "typescript" in deps:
        checks.append(QualityCheck(name="types", command=f"{prefix}npx --no-install tsc --noEmit"))
    if "lint" in scripts:
        checks.append(QualityCheck(name="lint", command=f"{prefix}{run} lint"))
    if "build" in scripts:
        checks.append(QualityCheck(name="build", command=f"{prefix}{run} build"))
    return checks


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
