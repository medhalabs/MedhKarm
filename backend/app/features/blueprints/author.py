"""Lekha at work (in the worker): writes a blueprint's documents one by one, saving each as it
is done so the founder sees progress, and rewrites the ones a comment touches. Safe to repeat:
documents already written are kept."""

from datetime import UTC, datetime

from app.features.blueprints.catalog import BY_ID, change_folder, docset
from app.features.blueprints.exceptions import BlueprintNotFoundError
from app.features.blueprints.interfaces import BlueprintRepository
from app.features.blueprints.schemas import Blueprint, BlueprintStatus, Comment, Doc
from app.features.blueprints.writer import BlueprintWriter


class BlueprintAuthor:
    def __init__(
        self, blueprints: BlueprintRepository, writer: BlueprintWriter, name: str = "Lekha"
    ) -> None:
        self._blueprints = blueprints
        self._writer = writer
        self._name = name

    async def write(self, blueprint_id: str) -> None:
        blueprint = await self._get(blueprint_id)
        docs = list(blueprint.docs)
        have = {d.id for d in docs}
        is_change = blueprint.brief.repo is not None
        specs = docset(is_change)
        folder = change_folder(blueprint.created_at, blueprint.title) if is_change else ""
        for number, spec in enumerate(specs, start=1):
            if spec.id in have:
                continue
            await self._blueprints.update(
                blueprint_id,
                progress=f"Writing the {spec.title.lower()} ({number} of {len(specs)})",
            )
            content = await self._writer.write(blueprint.brief, spec, docs)
            path = spec.path.format(folder=folder)
            docs.append(Doc(id=spec.id, title=spec.title, path=path, content=content))
            await self._blueprints.update(blueprint_id, docs=docs)
        unanswered = blueprint.comments and blueprint.comments[-1].author == "founder"
        if unanswered:  # a comment came in before a failed rewrite: apply it now
            await self.revise(blueprint_id)
            return
        await self._blueprints.update(
            blueprint_id, status=BlueprintStatus.READY, progress="", error=""
        )

    async def revise(self, blueprint_id: str) -> None:
        blueprint = await self._get(blueprint_id)
        comment = next((c for c in reversed(blueprint.comments) if c.author == "founder"), None)
        if comment is None:
            await self._blueprints.update(blueprint_id, status=BlueprintStatus.READY, progress="")
            return
        docs = list(blueprint.docs)
        ids = await self._writer.affected(docs, comment.text)
        for done, doc_id in enumerate(ids, start=1):
            spec = BY_ID[doc_id]
            await self._blueprints.update(
                blueprint_id, progress=f"Rewriting the {spec.title.lower()} ({done} of {len(ids)})"
            )
            index = next(i for i, d in enumerate(docs) if d.id == doc_id)
            content = await self._writer.write(
                blueprint.brief, spec, docs[:index], comment.text, docs[index]
            )
            docs[index] = docs[index].model_copy(update={"content": content})
            await self._blueprints.update(blueprint_id, docs=docs)
        titles = ", ".join(BY_ID[i].title.lower() for i in ids)
        reply = Comment(author="lekha", text=f"I updated the {titles}.", at=datetime.now(UTC))
        await self._blueprints.update(
            blueprint_id,
            status=BlueprintStatus.READY,
            progress="",
            comments=[*blueprint.comments, reply],
            revision=blueprint.revision + 1,
        )

    async def give_up(self, blueprint_id: str, error: str) -> None:
        """Out of retries: the founder sees why and can ask again."""
        if await self._blueprints.get(blueprint_id) is None:
            return
        await self._blueprints.update(
            blueprint_id,
            status=BlueprintStatus.FAILED,
            progress="",
            error=f"{self._name} couldn't finish: {error[:300]}",
        )

    async def _get(self, blueprint_id: str) -> Blueprint:
        found = await self._blueprints.get(blueprint_id)
        if found is None:
            raise BlueprintNotFoundError(f"No blueprint {blueprint_id}")
        return found
