from typing import Protocol

from app.features.messages.schemas import Message, ThreadKind


class MessageRepository(Protocol):
    async def add(
        self,
        company_id: str,
        thread: ThreadKind,
        thread_id: str,
        author: str,
        name: str,
        to: str,
        body: str,
    ) -> Message: ...

    async def get(self, message_id: int) -> Message | None: ...

    async def thread(self, thread: ThreadKind, thread_id: str, limit: int = 200) -> list[Message]:
        """Oldest first."""
        ...

    async def recent(self, company_id: str, limit: int = 20) -> list[Message]:
        """Newest first, across the company's threads."""
        ...


class ThreadOwner(Protocol):
    """Is this run or project the company's? (runs and projects services)"""

    async def owns(self, company_id: str, thread: ThreadKind, thread_id: str) -> bool: ...
