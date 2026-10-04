"""CompanyRepository in memory, for tests."""

import uuid
from datetime import UTC, datetime

from app.features.companies.schemas import Company


class InMemoryCompanyRepository:
    def __init__(self) -> None:
        self.companies: dict[str, Company] = {}

    async def create(self, name: str) -> Company:
        company = Company(id=str(uuid.uuid4()), name=name, created_at=datetime.now(UTC))
        self.companies[company.id] = company
        return company

    async def get(self, company_id: str) -> Company | None:
        return self.companies.get(company_id)

    async def count(self) -> int:
        return len(self.companies)
