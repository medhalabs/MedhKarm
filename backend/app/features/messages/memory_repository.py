"""MessageRepository in memory, for tests."""

from datetime import UTC, datetime

from app.features.messages.schemas import Message, ThreadKind


class InMemoryMessageRepository:
    def __init__(self) -> None:
        self.messages: list[Message] = []

    async def add(
        self,
        company_id: str,
        thread: ThreadKind,
        thread_id: str,
        author: str,
        name: str,
        to: str,
        body: str,
    ) -> Message:
        message = Message(
            id=len(self.messages) + 1,
            company_id=company_id,
            thread=thread,
            thread_id=thread_id,
            author=author,
            name=name,
            to=to,
            body=body,
            created_at=datetime.now(UTC),
        )
        self.messages.append(message)
        return message

    async def get(self, message_id: int) -> Message | None:
        return next((m for m in self.messages if m.id == message_id), None)

    async def thread(self, thread: ThreadKind, thread_id: str, limit: int = 200) -> list[Message]:
        found = [m for m in self.messages if m.thread == thread and m.thread_id == thread_id]
        return found[:limit]

    async def recent(self, company_id: str, limit: int = 20) -> list[Message]:
        mine = [m for m in self.messages if m.company_id == company_id]
        return list(reversed(mine))[:limit]
