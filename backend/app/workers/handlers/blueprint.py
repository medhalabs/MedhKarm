"""The blueprint jobs: Lekha writes the documents, and rewrites them after a comment
(features/blueprints/author.py)."""

from typing import Any

from app.features.blueprints.author import BlueprintAuthor
from app.features.jobs.exceptions import PermanentJobError


def _id(payload: dict[str, Any]) -> str:
    blueprint_id = str(payload.get("blueprint_id", ""))
    if not blueprint_id:
        raise PermanentJobError(f"No blueprint in job payload: {payload}")
    return blueprint_id


class WriteBlueprint:
    def __init__(self, author: BlueprintAuthor) -> None:
        self._author = author

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        await self._author.write(_id(payload))
        return {"blueprint_id": _id(payload)}

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        await self._author.give_up(str(payload.get("blueprint_id", "")), error)


class ReviseBlueprint:
    def __init__(self, author: BlueprintAuthor) -> None:
        self._author = author

    async def run(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        await self._author.revise(_id(payload))
        return {"blueprint_id": _id(payload)}

    async def give_up(self, payload: dict[str, Any], error: str) -> None:
        await self._author.give_up(str(payload.get("blueprint_id", "")), error)
