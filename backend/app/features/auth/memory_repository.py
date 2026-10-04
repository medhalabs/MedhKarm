"""UserRepository in memory, for tests."""

import uuid
from datetime import UTC, datetime

from app.features.auth.schemas import StoredUser


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.users: dict[str, StoredUser] = {}

    async def create(
        self, email: str, name: str, password_hash: str, company_id: str
    ) -> StoredUser:
        user = StoredUser(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            company_id=company_id,
            password_hash=password_hash,
            created_at=datetime.now(UTC),
        )
        self.users[user.id] = user
        return user

    async def by_email(self, email: str) -> StoredUser | None:
        return next((u for u in self.users.values() if u.email == email), None)

    async def get(self, user_id: str) -> StoredUser | None:
        return self.users.get(user_id)
