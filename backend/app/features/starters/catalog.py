"""Reads starters and modules from backend/starters/: each starter is a folder with
`starter.toml` and `files/`, each module `modules/<name>/` with `module.toml` and `files/`,
and a starter's `hosting.toml` lists extra files per host. Files are plain text, copied as they are;
`*.tmpl` files are filled in (see service.py)."""

import tomllib
from functools import cache
from pathlib import Path
from typing import Any

from app.features.starters.exceptions import UnknownStarterError
from app.features.starters.schemas import HostingSpec, ModuleSpec, StarterSpec

STARTERS_DIR = Path(__file__).resolve().parents[3] / "starters"
SKIP = {"node_modules", ".next", "__pycache__", ".pytest_cache", ".data"}


class FileCatalog:
    def __init__(self, root: Path = STARTERS_DIR) -> None:
        self._root = root

    def starter(self, name: str) -> StarterSpec:
        path = self._root / name / "starter.toml"
        if not path.is_file():
            raise UnknownStarterError(f"No starter called {name!r}")
        return StarterSpec.model_validate(_toml(path))

    def modules(self) -> list[ModuleSpec]:
        folder = self._root / "modules"
        return [
            ModuleSpec.model_validate(_toml(path)) for path in sorted(folder.glob("*/module.toml"))
        ]

    def hosting(self, starter: str, host: str) -> HostingSpec | None:
        path = self._root / starter / "hosting.toml"
        if not path.is_file():
            return None
        for name, spec in _toml(path).items():
            if host in spec.get("hosts", []):
                return HostingSpec(name=name, hosts=spec["hosts"], dir=f"{starter}/{spec['dir']}")
        return None

    def files(self, folder: str) -> dict[str, str]:
        return _read_tree(self._root / folder)


@cache
def _toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text())


def _read_tree(base: Path) -> dict[str, str]:
    if not base.is_dir():
        raise UnknownStarterError(f"No folder {base.name!r} in the starter catalog")
    return {
        path.relative_to(base).as_posix(): path.read_text()
        for path in sorted(base.rglob("*"))
        if path.is_file() and not SKIP & set(path.relative_to(base).parts)
    }
