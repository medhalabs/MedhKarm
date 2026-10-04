"""Puts a starter and its modules in a new project's workspace and installs it, so the team
adapts tested parts instead of writing sign-in or payments from scratch.

Composition: the starter's files, then the host's extra files (Docker for a server), then each
module's files. `*.tmpl` files are filled in ({{stack_table}}, {{modules_section}}, the
modules' settings in .env.example) and lose the suffix. A Python API with a Next.js frontend
is split: web/ (Next.js) and api/ (Python)."""

from app.features.sandbox.interfaces import Sandbox
from app.features.starters.catalog import FileCatalog
from app.features.starters.interfaces import StarterCatalog
from app.features.starters.schemas import ModuleSpec, ScaffoldResult, Stack, StackChoice
from app.features.starters.stack import resolve_stack

SETUP_TIMEOUT = 900
TEMPLATE = ".tmpl"
VERCEL_ONLY = {"vercel.json"}
CRON_SERVICE = """  cron:  # calls the reminders route every 5 minutes
    image: curlimages/curl:8.11.1
    depends_on: [app]
    env_file: [.env]
    entrypoint: ["/bin/sh", "-c"]
    command: ['while true; do curl -fsS -H "Authorization: Bearer $$CRON_SECRET" http://app:3000/api/cron/reminders; sleep 300; done']
    restart: unless-stopped
"""  # noqa: E501


class StarterService:
    def __init__(self, catalog: StarterCatalog | None = None) -> None:
        self._catalog = catalog or FileCatalog()

    def modules(self) -> list[ModuleSpec]:
        return self._catalog.modules()

    def resolve(self, request: str, choice: StackChoice) -> Stack:
        return resolve_stack(request, choice, self._catalog.modules())

    def compose(self, stack: Stack) -> dict[str, str]:
        """Every file of the new project, path -> text. Empty when the stack has no starter."""
        if stack.starter is None:
            return {}
        if stack.layout == "split":
            web = self._project("nextjs", stack, [])
            api = self._project(stack.starter, stack, [])
            return {
                **{f"web/{p}": t for p, t in web.items()},
                **{f"api/{p}": t for p, t in api.items()},
                "README.md": _split_readme(stack),
            }
        return self._project(stack.starter, stack, stack.modules)

    def commands(self, stack: Stack) -> tuple[str, str]:
        """How to install and test the composed project."""
        if stack.starter is None:
            return "", ""
        spec = self._catalog.starter(stack.starter)
        if stack.layout == "split":
            web = self._catalog.starter("nextjs")
            return (
                f"(cd api && {spec.setup_command}) && (cd web && {web.setup_command})",
                f"(cd api && {spec.test_command}) && (cd web && {web.test_command})",
            )
        return spec.setup_command, spec.test_command

    async def scaffold(self, sandbox: Sandbox, stack: Stack) -> ScaffoldResult | None:
        files = self.compose(stack)
        if not files or stack.starter is None or stack.layout is None:
            return None
        for path, text in files.items():
            await sandbox.write_file(path, text)
        setup, test = self.commands(stack)
        result = await sandbox.run(setup, timeout_seconds=SETUP_TIMEOUT)
        return ScaffoldResult(
            starter=stack.starter,
            layout=stack.layout,
            modules=stack.modules,
            files=sorted(files),
            setup_command=setup,
            test_command=test,
            setup_ok=result.ok,
            setup_output=result.output[-2000:],
        )

    def _project(self, starter: str, stack: Stack, module_names: list[str]) -> dict[str, str]:
        files = self._catalog.files(f"{starter}/files")
        hosting = self._catalog.hosting(starter, stack.hosting)
        if hosting:
            files |= self._catalog.files(hosting.dir)
        by_name = {m.name: m for m in self._catalog.modules()}
        modules = [by_name[n] for n in module_names if n in by_name]
        for module in modules:
            files |= {
                path: text
                for path, text in self._catalog.files(f"modules/{module.name}/files").items()
                if path not in VERCEL_ONLY or stack.hosting == "vercel"
            }
        values = _values(stack, modules)
        rendered: dict[str, str] = {}
        for path, text in files.items():
            if path.endswith(TEMPLATE):
                path, text = path.removesuffix(TEMPLATE), _fill(text, values)
                if path == ".env.example":
                    text += "".join(
                        "\n" + _fill(m.env.strip(), values) + "\n" for m in modules if m.env
                    )
            rendered[path] = text
        return rendered


def _values(stack: Stack, modules: list[ModuleSpec]) -> dict[str, str]:
    section = ""
    if modules:
        section = "\n## Ready-made modules\n\n" + "\n".join(
            f"### {m.title}\n\n{m.description}.\n{m.guide.rstrip()}\n" for m in modules
        )
    return {
        "stack_table": stack.table(),
        "modules_section": section,
        "cron_service": CRON_SERVICE if any(m.name == "reminders" for m in modules) else "",
        **{
            field: str(getattr(stack, field))
            for field in ("frontend", "api", "database", "hosting", "payments")
        },
    }


def _fill(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _split_readme(stack: Stack) -> str:
    return (
        "# App\n\nBuilt by the MedhKarm software team.\n\n"
        "- `web/`: the Next.js frontend (see web/AGENTS.md)\n"
        "- `api/`: the Python API (see api/AGENTS.md)\n\n"
        f"{stack.table()}\n\n"
        "Run both: `cd api && uvicorn app.main:app --reload` and `cd web && npm run dev`.\n"
    )
