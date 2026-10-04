from typing import Protocol

from app.features.auth.schemas import StoredUser


class UserRepository(Protocol):
    async def create(
        self, email: str, name: str, password_hash: str, company_id: str
    ) -> StoredUser: ...

    async def by_email(self, email: str) -> StoredUser | None: ...

    async def get(self, user_id: str) -> StoredUser | None: ...


class DataAdopter(Protocol):
    """Gives records made before sign-in existed to a company (runs, projects)."""

    async def adopt_unowned(self, company_id: str) -> int:
        """How many records it adopted."""
        ...
