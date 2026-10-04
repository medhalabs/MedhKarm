"""Composing a new project from the real catalog, and putting it in a sandbox."""

import json
from pathlib import Path

from app.features.sandbox.providers.memory_provider import InMemorySandbox
from app.features.sandbox.schemas import CommandResult
from app.features.starters.catalog import STARTERS_DIR
from app.features.starters.schemas import StackChoice
from app.features.starters.service import StarterService

service = StarterService()


def compose(request: str, **choice: object) -> dict[str, str]:
    return service.compose(service.resolve(request, StackChoice.model_validate(choice)))


def test_a_nextjs_project_with_modules() -> None:
    files = compose("A gym website where members log in and pay fees", payments="stripe")

    assert {"package.json", "lib/db/index.ts", "lib/auth/index.ts", "app/pay/page.tsx"} <= set(
        files
    )
    assert "lib/reminders/index.ts" not in files and "Dockerfile" not in files
    assert not any(p.endswith(".tmpl") for p in files)
    assert not any("{{" in text for text in files.values())
    assert "PAYMENTS_PROVIDER=stripe" in files[".env.example"]
    assert "SESSION_SECRET=" in files[".env.example"]
    agents = files["AGENTS.md"]
    assert "| payments | stripe | founder |" in agents
    assert "### Sign-in" in agents and "### Payments" in agents


def test_server_hosting_adds_docker_and_the_reminders_cron() -> None:
    files = compose("A clinic website that sends appointment reminders", hosting="aws")

    assert {"Dockerfile", ".dockerignore", "docker-compose.yml"} <= set(files)
    assert "/api/cron/reminders" in files["docker-compose.yml"]
    assert "vercel.json" not in files  # Vercel's cron only on Vercel

    on_vercel = compose("A clinic website that sends appointment reminders")
    assert "vercel.json" in on_vercel and "Dockerfile" not in on_vercel


def test_a_python_api_with_a_frontend_is_split() -> None:
    stack = service.resolve("A clinic website", StackChoice(api="python"))
    files = service.compose(stack)

    assert {"web/package.json", "api/app/main.py", "api/tests/test_store.py", "README.md"} <= set(
        files
    )
    setup, test = service.commands(stack)
    assert setup.startswith("(cd api && pip install") and "(cd web && npm ci" in setup
    assert test == "(cd api && python -m pytest -q) && (cd web && npm run typecheck && npm test)"


def test_nothing_to_compose_without_a_starter() -> None:
    assert compose("An inventory web app", api="java") == {}


async def test_scaffold_writes_the_files_and_installs() -> None:
    sandbox = InMemorySandbox(
        "s", lambda c, f: CommandResult(exit_code=0, output="added 419 packages")
    )
    stack = service.resolve("A shop website with checkout", StackChoice())

    result = await service.scaffold(sandbox, stack)

    assert result is not None and result.setup_ok
    assert result.modules == ["payments"] and result.test_command == "npm run typecheck && npm test"
    assert sandbox.commands == ["npm ci --prefer-offline --no-audit --no-fund"]
    assert "lib/payments/razorpay.ts" in sandbox.files


def test_the_sandbox_image_caches_the_starters_exact_packages() -> None:
    """sandbox-image/starter-deps must match the starter, or runs download packages again."""
    cached = STARTERS_DIR.parent / "sandbox-image" / "starter-deps" / "nextjs"
    starter = STARTERS_DIR / "nextjs" / "files"
    for name in ("package.json", "package-lock.json"):
        assert (cached / name).read_text() == (starter / name).read_text(), name
    lock = json.loads((starter / "package-lock.json").read_text())
    assert (
        lock["packages"][""]["dependencies"]
        == json.loads((starter / "package.json").read_text())["dependencies"]
    )


def test_every_module_declares_what_it_needs() -> None:
    modules = {m.name: m for m in service.modules()}
    assert set(modules) == {"auth", "payments", "reminders", "dashboards"}
    for module in modules.values():
        assert module.keywords and module.guide and module.env
        assert set(module.requires) <= set(modules)
        assert (Path(STARTERS_DIR) / "modules" / module.name / "files").is_dir()
