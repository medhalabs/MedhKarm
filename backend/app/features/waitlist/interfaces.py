from typing import Protocol

from app.features.waitlist.schemas import JoinWaitlist, WaitlistEntry


class WaitlistRepository(Protocol):
    async def add(self, entry: JoinWaitlist) -> bool:
        """True when new; False when that email was already on the list."""
        ...

    async def count(self) -> int: ...

    async def all(self) -> list[WaitlistEntry]: ...

    async def invite(self, email: str) -> bool:
        """Marks the email invited. False when it isn't on the list."""
        ...
