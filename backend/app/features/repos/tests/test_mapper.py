import json

from app.features.repos.mapper import map_codebase
from app.features.repos.tests.fakes import sandbox_with

PACKAGE = json.dumps(
    {
        "name": "shop",
        "scripts": {"test": "vitest run", "dev": "next dev"},
        "dependencies": {"next": "16"},
        "devDependencies": {"vitest": "3"},
    }
)


async def test_maps_a_javascript_project() -> None:
    sandbox = sandbox_with(
        {
            ".git/HEAD": "ref: refs/heads/main",
            "package.json": PACKAGE,
            "package-lock.json": "{}",
            "README.md": "# Shop\nA small shop.",
            "src/cart.ts": "export function addItem(cart, item) {}\nexport const TAX = 0.18\n",
            "src/ui/Button.tsx": "export default function Button() {}\n",
            "node_modules/next/index.js": "function hidden() {}",
        }
    )

    codebase = await map_codebase(sandbox)

    assert codebase.languages == {"TypeScript": 2}
    assert "node_modules/next/index.js" not in codebase.tree
    assert codebase.setup_command == "npm ci --no-audit --no-fund"
    assert codebase.test_command == "npm test"
    assert codebase.outline["src/cart.ts"] == ["addItem", "TAX"]
    assert codebase.outline["src/ui/Button.tsx"] == ["Button"]
    assert "scripts: test, dev" in codebase.manifests["package.json"]
    assert codebase.readme.startswith("# Shop")
    brief = codebase.brief()
    assert "Tests run with: npm test" in brief and "src/cart.ts: addItem, TAX" in brief


async def test_maps_a_python_project_without_git() -> None:
    sandbox = sandbox_with(
        {
            "requirements.txt": "# deps\nfastapi\nhttpx\n",
            "app.py": "class Note:\n    def save(self): ...\n\nasync def create(): ...\n",
            "tests/test_app.py": "def test_create(): ...\n",
        }
    )

    codebase = await map_codebase(sandbox)

    assert codebase.file_count == 3
    assert codebase.setup_command == "pip install -q -r requirements.txt"
    assert codebase.test_command == "python -m pytest -q"
    assert codebase.outline["app.py"] == ["Note", "create"]  # top level only
    assert codebase.manifests["requirements.txt"] == "fastapi, httpx"


async def test_default_test_runner_when_a_project_has_no_tests() -> None:
    codebase = await map_codebase(sandbox_with({"index.js": "function main() {}\n"}))
    assert codebase.test_command == "node --test"
    assert codebase.setup_command == ""


async def test_empty_workspace_is_an_empty_map() -> None:
    codebase = await map_codebase(sandbox_with({}))
    assert codebase.empty and codebase.brief() == ""


async def test_installs_a_python_package_and_its_test_dependencies() -> None:
    pyproject = """
[project]
name = "signer"
dependencies = []
[project.optional-dependencies]
docs = ["sphinx"]
[dependency-groups]
tests = ["pytest", "freezegun"]
dev = [{include-group = "tests"}, "ruff"]
[build-system]
requires = ["flit_core"]
"""
    sandbox = sandbox_with(
        {"pyproject.toml": pyproject, "src/signer/__init__.py": "", "tests/test_sign.py": ""}
    )

    codebase = await map_codebase(sandbox)

    assert codebase.setup_command == "pip install -q -e . && pip install -q pytest freezegun ruff"
