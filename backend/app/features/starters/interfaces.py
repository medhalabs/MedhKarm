from typing import Protocol

from app.features.starters.schemas import HostingSpec, ModuleSpec, StarterSpec


class StarterCatalog(Protocol):
    """Where starters and modules come from (FileCatalog: backend/starters/)."""

    def starter(self, name: str) -> StarterSpec: ...

    def modules(self) -> list[ModuleSpec]: ...

    def hosting(self, starter: str, host: str) -> HostingSpec | None:
        """Extra files for hosting `starter` on `host` (Docker files for a server), if any."""
        ...

    def files(self, folder: str) -> dict[str, str]:
        """Every file under `folder` (relative to the catalog), path -> text."""
        ...
