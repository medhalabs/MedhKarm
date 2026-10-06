"""WaitlistRepository in memory, for tests."""

from datetime import UTC, datetime

from app.features.waitlist.schemas import JoinWaitlist, WaitlistEntry


class InMemoryWaitlistRepository:
    def __init__(self) -> None:
        self.entries: dict[str, WaitlistEntry] = {}

    async def add(self, entry: JoinWaitlist) -> bool:
        if entry.email in self.entries:
            return False
        self.entries[entry.email] = WaitlistEntry(
            id=len(self.entries) + 1,
            email=entry.email,
            name=entry.name,
            building=entry.building,
            source=entry.source,
            created_at=datetime.now(UTC),
        )
        return True

    async def count(self) -> int:
        return len(self.entries)

    async def all(self) -> list[WaitlistEntry]:
        return list(self.entries.values())

    async def invite(self, email: str) -> bool:
        key = email.strip().lower()
        if key not in self.entries:
            return False
        self.entries[key] = self.entries[key].model_copy(update={"invited_at": datetime.now(UTC)})
        return True
