"""Lekha's changelog: before the founder approves, a plain-language entry about what changed
goes into the project's docs/CHANGELOG.md, so the release carries its own paperwork. Only for
projects that keep a docs/ folder (a blueprint's plan, or the founder's own); others are left
alone. Safe to repeat: an entry for this run is written once."""

from datetime import UTC, datetime
from typing import Any

from app.features.models.interfaces import LLMProvider
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.state import BuildState

PATH = "docs/CHANGELOG.md"
HEADER = "# Changelog\n\nWhat changed in this project, in plain words. Newest first.\n"
CHANGELOG_PROMPT = """You are Lekha, the documentation lead of a small software team. Write a
changelog entry for the founder, who may not be technical: two to five short bullet points
("- ...") saying what the product can do now that it couldn't before, or what was fixed. Plain
words, no file names, no jargon. Output only the bullet points."""
MAX_FILES = 40


def make_changelog_node(
    sandboxes: SandboxProvider, llm: LLMProvider | None, name: str = "Lekha"
) -> BuildNode:
    async def changelog(state: BuildState) -> dict[str, Any]:
        if llm is None or not state.get("sandbox_id"):
            return {}
        sandbox = await sandboxes.attach(state["sandbox_id"])
        if not any(f.startswith("docs/") for f in await sandbox.list_files()):
            return {}
        marker = f"<!-- run {state.get('run_id', '')} -->"
        try:
            current = await sandbox.read_file(PATH)
        except Exception:  # no changelog yet
            current = ""
        if marker in current:
            return {}
        response = await llm.complete(
            [
                {"role": "system", "content": CHANGELOG_PROMPT},
                {"role": "user", "content": _facts(state)},
            ]
        )
        entry = _bullets(response.content or "")
        if not entry:
            return {}
        today = datetime.now(UTC).strftime("%d %b %Y")
        section = f"## {today} {marker}\n\n{entry}\n"
        head, _, rest = (current or HEADER).partition("\n## ")
        body = f"{head.rstrip()}\n\n{section}" + (f"\n## {rest}" if rest else "")
        await sandbox.write_file(PATH, body)
        return {
            "docs_updated": {"path": PATH, "entry": entry, "by": name},
            "docs_tokens": response.usage.total_tokens,
        }

    return changelog


def _facts(state: BuildState) -> str:
    done = [
        f"- {t['title']}: {t.get('summary') or 'done'}"
        for t in state.get("tasks", [])
        if t.get("status") != "todo"
    ]
    files = [f for f in state.get("dev_result", {}).get("files_changed", [])][:MAX_FILES]
    return (
        f"The founder asked for:\n{state['request'][:3000]}\n\nThe team did:\n"
        + "\n".join(done)
        + f"\n\nFiles changed (for your context only): {', '.join(files)}"
    )


def _bullets(text: str) -> str:
    """Only the bullet lines (small models add a preamble)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith(("- ", "* "))]
    return "\n".join("- " + ln[2:].strip() for ln in lines[:6])
