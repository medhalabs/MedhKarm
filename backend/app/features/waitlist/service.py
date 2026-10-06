"""The waitlist. Joining is open to anyone, so a hidden field catches simple bots (they get
the same friendly answer and nothing is saved) and the same address twice is quietly one
entry. The emails are never served over HTTP: the team reads them with the command in
app/workers/waitlist.py."""

from app.features.waitlist.interfaces import WaitlistRepository
from app.features.waitlist.schemas import Joined, JoinWaitlist, WaitlistEntry


class WaitlistService:
    def __init__(self, entries: WaitlistRepository) -> None:
        self._entries = entries

    async def join(self, body: JoinWaitlist) -> Joined:
        if not body.website:  # a person never sees that field; a bot fills every field
            await self._entries.add(body)
        return Joined(count=await self._entries.count())

    async def count(self) -> int:
        return await self._entries.count()

    async def export(self) -> list[WaitlistEntry]:
        return await self._entries.all()

    async def invite(self, email: str) -> bool:
        return await self._entries.invite(email)
