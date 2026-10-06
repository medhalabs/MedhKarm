"""Lekha's writing: one model call per document, in the founder's language of plain words."""

from collections.abc import Callable

from app.features.blueprints.catalog import BY_ID, DOCS, DocSpec
from app.features.blueprints.schemas import Doc
from app.features.models.interfaces import LLMProvider
from app.features.runs.schemas import StartRun

LEKHA_PROMPT = """You are Lekha, the documentation lead of a small software team. You write
the project's plan for the founder, who may not be technical: plain words, short sentences,
no jargon without a one-line explanation. Be specific to this project, never generic. Write
Markdown only: start with a level-1 heading, no preamble, no closing remarks. Keep it as
short as it can be while being complete. When you are unsure, state your assumption."""

EARLIER_LIMIT = 3500  # characters of each earlier document given as context
REWRITE_TOOL = {
    "type": "function",
    "function": {
        "name": "rewrite_docs",
        "description": "Say which documents the founder's comment changes.",
        "parameters": {
            "type": "object",
            "properties": {
                "docs": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(BY_ID)},
                    "description": "ids of the documents that need rewriting",
                }
            },
            "required": ["docs"],
        },
    },
}


def describe(brief: StartRun, stack: str = "") -> str:
    """The agreed brief as text for the documents. `stack`: what the team will really build on."""
    lines = [f"The founder's request:\n{brief.request.strip()}"]
    if brief.repo:
        lines.append(f"Existing repository to change: {brief.repo.url}")
    else:
        lines.append("A new project (a new private repository is created for it).")
    chosen = {
        k: v
        for k, v in brief.stack.model_dump().items()
        if v not in (None, "", []) and k != "starter"
    }
    if chosen:
        lines.append("Founder's choices: " + ", ".join(f"{k}: {v}" for k, v in chosen.items()))
    if stack:
        lines.append(
            "The team builds on this stack. Your documents must use it and must not propose "
            f"another:\n{stack}"
        )
    return "\n".join(lines)


class BlueprintWriter:
    def __init__(
        self,
        llm: LLMProvider,
        instructions: str = "",
        stack: Callable[[StartRun], str] | None = None,
    ) -> None:
        self._llm = llm
        self._stack = stack
        self._instructions = instructions.strip() or LEKHA_PROMPT

    async def write(
        self,
        brief: StartRun,
        spec: DocSpec,
        earlier: list[Doc],
        comment: str = "",
        previous: Doc | None = None,
    ) -> str:
        """One document. With a comment, the document is rewritten to follow it."""
        parts = [describe(brief, self._stack(brief) if self._stack else "")]
        if earlier:
            parts.append(
                "Documents already written (stay consistent with them):\n\n"
                + "\n\n".join(f"## {d.title}\n{d.content[:EARLIER_LIMIT]}" for d in earlier)
            )
        if previous:
            parts.append(f"The current version of this document:\n{previous.content}")
        if comment:
            parts.append(f"The founder's comment (follow it):\n{comment}")
        parts.append(f"Write the document '{spec.title}'. It must contain: {spec.asks}")
        response = await self._llm.complete(
            [
                {"role": "system", "content": self._instructions},
                {"role": "user", "content": "\n\n".join(parts)},
            ]
        )
        return _clean(response.content or "", spec.title)

    async def affected(self, docs: list[Doc], comment: str) -> list[str]:
        """Which documents the founder's comment changes (ids, in writing order)."""
        listing = "\n".join(f"- {d.id}: {d.title}" for d in docs)
        response = await self._llm.complete(
            [
                {"role": "system", "content": self._instructions},
                {
                    "role": "user",
                    "content": f"Documents:\n{listing}\n\nThe founder's comment:\n{comment}\n\n"
                    "Which documents must change? Answer with rewrite_docs. Include every "
                    "document the comment touches, even indirectly.",
                },
            ],
            [REWRITE_TOOL],
        )
        asked: list[str] = []
        for call in response.tool_calls:
            if call.name == "rewrite_docs":
                raw = call.arguments.get("docs")
                asked += [str(x) for x in raw] if isinstance(raw, list) else []
        known = {d.id for d in docs}
        chosen = [s.id for s in DOCS if s.id in asked and s.id in known]
        return chosen or [d.id for d in docs]  # unclear: rewrite them all, never nothing


def _clean(text: str, title: str) -> str:
    """The document without a code fence around it; a heading added if the model left it out."""
    text = text.strip()
    if text.startswith("```markdown") or text.startswith("```md"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.removesuffix("```").strip()
    if not text.startswith("#"):
        text = f"# {title}\n\n{text}"
    return text
