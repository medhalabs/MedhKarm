from typing import Protocol

from app.features.sandbox.interfaces import Sandbox
from app.features.security.schemas import ScanResult


class Scanner(Protocol):
    """One kind of security check over the files a run changed."""

    name: str

    async def scan(self, sandbox: Sandbox, changed: list[str]) -> ScanResult: ...
