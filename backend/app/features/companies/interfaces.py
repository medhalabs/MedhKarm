from typing import Protocol

from app.features.companies.schemas import Company


class CompanyRepository(Protocol):
    async def create(self, name: str) -> Company: ...

    async def get(self, company_id: str) -> Company | None: ...

    async def count(self) -> int: ...
