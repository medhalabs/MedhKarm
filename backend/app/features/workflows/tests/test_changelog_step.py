"""Lekha's changelog step: projects with a docs/ folder get a plain-language entry before the
gate; others are left alone; a repeat doesn't write it twice."""

from typing import Any

from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.events.stores.memory_store import InMemoryEventStore
from app.features.models.providers.scripted_provider import ScriptedLLMProvider
from app.features.models.schemas import LLMResponse, TokenUsage
from app.features.sandbox.providers.memory_provider import InMemorySandboxProvider
from app.features.workflows.activity import record_step
from app.features.workflows.nodes.changelog import PATH, make_changelog_node

TASKS = [{"id": "t1", "title": "Tip option", "summary": "Added a tip choice", "status": "done"}]


def reply(text: str) -> LLMResponse:
    return LLMResponse(content=text, usage=TokenUsage(prompt_tokens=30, completion_tokens=12))


async def state_with(files: dict[str, str]) -> tuple[InMemorySandboxProvider, dict[str, Any]]:
    sandboxes = InMemorySandboxProvider()
    sandbox = await sandboxes.create()
    for path, text in files.items():
        await sandbox.write_file(path, text)
    return sandboxes, {
        "run_id": "run-5",
        "sandbox_id": sandbox.id,
        "request": "Add a tip option at checkout",
        "tasks": TASKS,
        "dev_result": {"files_changed": ["app/checkout/page.tsx"]},
    }


async def test_a_project_with_docs_gets_a_changelog_entry_without_the_models_preamble() -> None:
    sandboxes, state = await state_with({"docs/README.md": "# Plan"})
    llm = ScriptedLLMProvider([reply("Here you go:\n- Customers can add a tip\n* Staff see it")])

    update = await make_changelog_node(sandboxes, llm)(state)  # type: ignore[arg-type]

    text = await (await sandboxes.attach(state["sandbox_id"])).read_file(PATH)
    assert text.startswith("# Changelog")
    assert "- Customers can add a tip\n- Staff see it" in text and "Here you go" not in text
    assert "<!-- run run-5 -->" in text
    assert update["docs_updated"]["entry"] == "- Customers can add a tip\n- Staff see it"
    assert update["docs_tokens"] == 42


async def test_new_entries_go_on_top_of_older_ones() -> None:
    old = "# Changelog\n\nWhat changed.\n\n## 01 Oct 2026 <!-- run run-1 -->\n\n- Menu page\n"
    sandboxes, state = await state_with({"docs/CHANGELOG.md": old})
    llm = ScriptedLLMProvider([reply("- Tips at checkout")])

    await make_changelog_node(sandboxes, llm)(state)  # type: ignore[arg-type]

    text = await (await sandboxes.attach(state["sandbox_id"])).read_file(PATH)
    assert text.index("Tips at checkout") < text.index("Menu page")
    assert text.count("## ") == 2


async def test_a_repeat_does_not_write_the_entry_twice() -> None:
    sandboxes, state = await state_with({"docs/README.md": "# Plan"})
    llm = ScriptedLLMProvider([reply("- Tips at checkout")])
    node = make_changelog_node(sandboxes, llm)

    await node(state)  # type: ignore[arg-type]
    assert await node(state) == {}  # type: ignore[arg-type]
    assert len(llm.calls) == 1


async def test_projects_without_docs_or_without_lekha_are_left_alone() -> None:
    sandboxes, state = await state_with({"app/page.tsx": "x"})
    llm = ScriptedLLMProvider([])
    assert await make_changelog_node(sandboxes, llm)(state) == {}  # type: ignore[arg-type]
    assert await make_changelog_node(sandboxes, None)(state) == {}  # type: ignore[arg-type]
    assert llm.calls == []


async def test_an_answer_without_bullets_writes_nothing() -> None:
    sandboxes, state = await state_with({"docs/README.md": "# Plan"})
    llm = ScriptedLLMProvider([reply("I could not summarise that.")])
    assert await make_changelog_node(sandboxes, llm)(state) == {}  # type: ignore[arg-type]
    assert PATH not in await (await sandboxes.attach(state["sandbox_id"])).list_files()


async def test_the_entry_is_told_to_the_founder_as_lekhas_work() -> None:
    events = InMemoryEventStore()
    data = {"docs_updated": {"path": PATH, "entry": "- Tips at checkout", "by": "Lekha"}}
    await record_step(RunRecorder(events, "run-5"), "changelog", {**data, "docs_tokens": 42})

    [event] = events.events
    assert (event.actor, event.type) == (Actor.DOCS, EventType.DOCS_UPDATED)
    assert event.summary == "Lekha added to the changelog: Tips at checkout"
    assert event.tokens == 42
