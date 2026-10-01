"""Built-in developer engine: the model calls sandbox tools in a loop until it finishes.

Success is decided by running the task's test command ourselves, never by the model's word.
"""

import json
from contextlib import AsyncExitStack

from app.features.developer_engine.engines.tools import (
    APPLY_PATCH,
    FINISH,
    TOOL_SPECS,
    compacted_patch_arguments,
    describe_tool_use,
    execute_tool,
    normalize_call,
)
from app.features.developer_engine.engines.workspace_snapshot import changed_files, snapshot
from app.features.developer_engine.interfaces import ToolSession, ToolSource
from app.features.developer_engine.schemas import DevResult, DevTask
from app.features.events.schemas import Actor, EventType
from app.features.events.service import RunRecorder
from app.features.models.interfaces import LLMProvider
from app.features.models.schemas import LLMResponse, Message, ToolSpec
from app.features.sandbox.interfaces import Sandbox

SYSTEM_PROMPT = """You are a careful software developer working in a Linux workspace.
Use the tools to write the code and tests the task needs, run the test command to check
your work, fix any failures, and call `finish` with a one-line summary once the tests pass.
Only change files inside the workspace. Keep solutions small and clear.
In an existing project, use `search` to find the code you need and read only those lines;
don't read the same part twice. Change existing files with `edit_file`; use `write_file`
only for new files. Make the change early, then test and fix."""

# When this many steps are left and nothing is written yet, the developer is told to write.
NUDGE_AT = 5

PATCH_HINT = "\nEdit existing files with `apply_patch`; use `write_file` for new files or rewrites."


DEFAULT_TOOLS = (
    "read_file",
    "write_file",
    "edit_file",
    "list_files",
    "search",
    "run_command",
    FINISH,
)
WRITE_TOOLS = ("write_file", "edit_file", APPLY_PATCH)


class ToolLoopEngine:
    def __init__(
        self,
        llm: LLMProvider,
        max_steps: int = 25,
        tools: list[str] | tuple[str, ...] = DEFAULT_TOOLS,
        instructions: str = SYSTEM_PROMPT,
        tool_sources: list[ToolSource] | tuple[ToolSource, ...] = (),
        existing_project_max_steps: int | None = None,
    ) -> None:
        """`tools` and `instructions` normally come from the developer role in the team
        template. `apply_patch` is left out by default: in the eval suite (gpt-oss:120b) it
        doubled tokens without improving results. Patches the model sends anyway (often
        through run_command) are still applied and compacted. `finish` is always offered.

        `tool_sources` add tools from outside the sandbox (MCP servers), each with its own
        access limits. Only offered tools ever run: a call to any other name is refused.

        `existing_project_max_steps` is the step limit for tasks on an existing project
        (`DevTask.existing_project`), which need more reading first; default `max_steps`."""
        self._llm = llm
        self._max_steps = max_steps
        self._existing_max_steps = existing_project_max_steps or max_steps
        allowed = set(tools) | {FINISH}
        self._tools = [spec for spec in TOOL_SPECS if spec["function"]["name"] in allowed]
        self._system_prompt = instructions.strip() + (PATCH_HINT if APPLY_PATCH in allowed else "")
        self._sources = list(tool_sources)

    async def run_task(
        self, task: DevTask, sandbox: Sandbox, recorder: RunRecorder | None = None
    ) -> DevResult:
        async with AsyncExitStack() as stack:
            extra: dict[str, ToolSession] = {}
            specs = list(self._tools)
            for source in self._sources:
                session = await stack.enter_async_context(source.session())
                for spec in await session.list_tools():
                    extra[spec["function"]["name"]] = session
                    specs.append(spec)
            return await self._loop(task, sandbox, recorder, specs, extra)

    async def _loop(
        self,
        task: DevTask,
        sandbox: Sandbox,
        recorder: RunRecorder | None,
        specs: list[ToolSpec],
        extra: dict[str, ToolSession],
    ) -> DevResult:
        offered = {spec["function"]["name"] for spec in specs}
        if "write_file" in offered or "edit_file" in offered:
            # Patches arrive even when apply_patch isn't offered (see __init__); for a role that
            # may write files anyway, a patch is just another way to write them.
            offered.add(APPLY_PATCH)
        messages: list[Message] = [
            {"role": "system", "content": self._system_prompt},
            {
                "role": "user",
                "content": f"Task: {task.description}\n\nTest command: {task.test_command}",
            },
        ]
        before = await snapshot(sandbox)
        summary = "Stopped: step limit reached before `finish` was called."
        tokens = 0
        steps = 0
        limit = self._existing_max_steps if task.existing_project else self._max_steps
        wrote = False

        for steps in range(1, limit + 1):
            if not wrote and steps == limit - NUDGE_AT + 1 and limit > NUDGE_AT * 2:
                messages.append(
                    {
                        "role": "user",
                        "content": f"Only {NUDGE_AT} steps left and no file is changed yet. "
                        "Write the change now, run the tests, then call `finish`.",
                    }
                )
            response = await self._llm.complete(messages, specs)
            tokens += response.usage.total_tokens
            if recorder:
                await recorder.record(
                    Actor.DEVELOPER,
                    EventType.MODEL_USED,
                    "Thought about the next step",
                    {"model": self._llm.model_name, "step": steps},
                    tokens=response.usage.total_tokens,
                )
            response.tool_calls = [normalize_call(call) for call in response.tool_calls]
            assistant = _assistant_message(response)
            messages.append(assistant)

            if not response.tool_calls:
                messages.append(
                    {"role": "user", "content": "Use the tools to continue, or call `finish`."}
                )
                continue

            finished = False
            for call in response.tool_calls:
                if call.name == FINISH:
                    summary = str(call.arguments.get("summary", "Finished."))
                    finished = True
                    result = "Finishing."
                else:
                    if call.name not in offered:
                        result = f"Not allowed: {call.name} isn't one of your tools."
                    elif call.name in extra:
                        result = await extra[call.name].call(call.name, call.arguments)
                    else:
                        result = await execute_tool(call.name, call.arguments, sandbox)
                    if recorder:
                        await recorder.record(
                            Actor.DEVELOPER,
                            EventType.TOOL_USED,
                            describe_tool_use(call.name, call.arguments, result),
                            {"tool": call.name, "result": result[:500]},
                        )
                    wrote = wrote or call.name in WRITE_TOOLS
                    if call.name == APPLY_PATCH:
                        _replace_arguments(assistant, call.id, compacted_patch_arguments(result))
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
            if finished:
                break

        test = await sandbox.run(task.test_command)
        after = await snapshot(sandbox)
        return DevResult(
            success=test.ok,
            summary=summary,
            files_changed=changed_files(before, after),
            test_output=test.output[-4000:],
            steps=steps,
            total_tokens=tokens,
        )


def _replace_arguments(assistant: Message, call_id: str, arguments: dict[str, str]) -> None:
    for tool_call in assistant.get("tool_calls", []):
        if tool_call["id"] == call_id:
            tool_call["function"]["arguments"] = json.dumps(arguments)


def _assistant_message(response: LLMResponse) -> Message:
    message: Message = {"role": "assistant", "content": response.content or ""}
    if response.tool_calls:
        message["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
            }
            for call in response.tool_calls
        ]
    return message
