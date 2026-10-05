"""ModelSettingsRepository on Postgres."""

import uuid
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.model_settings.models import ModelSettingsRow
from app.features.model_settings.schemas import KeyMode, ModelChoices, Provider, StoredModels


class SqlModelSettingsRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def get(self, company_id: str) -> StoredModels | None:
        async with self._sessions() as session:
            row = await session.get(ModelSettingsRow, uuid.UUID(company_id))
            return _to_stored(row) if row else None

    async def save_choices(self, company_id: str, choices: ModelChoices) -> StoredModels:
        return await self._upsert(company_id, choices.model_dump(mode="json"))

    async def set_key(
        self, company_id: str, provider: Provider, sealed: str | None, hint: str
    ) -> StoredModels:
        current = await self.get(company_id) or StoredModels(company_id=company_id)
        keys = {
            p.value: {"sealed": s, "hint": current.hints.get(p, "")}
            for p, s in current.sealed_keys.items()
        }
        if sealed is None:
            keys.pop(provider.value, None)
        else:
            keys[provider.value] = {"sealed": sealed, "hint": hint}
        return await self._upsert(company_id, {"keys": keys})

    async def _upsert(self, company_id: str, values: dict[str, Any]) -> StoredModels:
        statement = (
            insert(ModelSettingsRow)
            .values(company_id=uuid.UUID(company_id), **values)
            .on_conflict_do_update(index_elements=["company_id"], set_=values)
            .returning(ModelSettingsRow)
        )
        async with self._sessions() as session, session.begin():
            row = (await session.scalars(statement)).one()
            return _to_stored(row)


def _to_stored(row: ModelSettingsRow) -> StoredModels:
    keys = {Provider(p): v for p, v in row.keys.items() if p in Provider}
    return StoredModels.model_construct(
        company_id=str(row.company_id),
        mode=KeyMode(row.mode),
        default_model=row.default_model,
        role_models=dict(row.role_models),
        local_url=row.local_url,
        sealed_keys={p: v["sealed"] for p, v in keys.items()},
        hints={p: v.get("hint", "") for p, v in keys.items()},
        updated_at=row.updated_at,
    )
