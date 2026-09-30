"""Built-in developer engine: the model calls sandbox tools in a loop until it finishes.

Success is decided by running the task's test command ourselves, never by the model's word.
"""

import json

from app.features.developer_engine.engines.tools import FINISH, TOOL_SPECS, execute_tool
from app.features.developer_engine.schemas import DevResult, DevTask
from app.features.models.interfaces import LLMProvider
from app.features.models.schemas import LLMResponse, Message
from app.features.sandbox.interfaces import Sandbox

SYSTEM_PROMPT = """You are a careful software developer working in a Linux workspace.
Use the tools to write the code and tests the task needs, run the test command to check
your work, fix any failures, and call `finish` with a one-line summary once the tests pass.
Only change files inside the workspace. Keep solutions small and clear."""


class ToolLoopEngine:
    def __init__(self, llm: LLMProvider, max_steps: int = 15) -> None:
        self._llm = llm
        self._max_steps = max_steps

    async def run_task(self, task: DevTask, sandbox: Sandbox) -> DevResult:
        messages: list[Message] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Task: {task.description}\n\nTest command: {task.test_command}",
            },
        ]
        files_before = set(await sandbox.list_files())
        summary = "Stopped: step limit reached before `finish` was called."
        tokens = 0
        steps = 0

        for steps in range(1, self._max_steps + 1):  # noqa: B007 — steps is reported after the loop
            response = await self._llm.complete(messages, TOOL_SPECS)
            tokens += response.usage.total_tokens
            messages.append(_assistant_message(response))

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
                    result = await execute_tool(call.name, call.arguments, sandbox)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
            if finished:
                break

        test = await sandbox.run(task.test_command)
        files_after = set(await sandbox.list_files())
        return DevResult(
            success=test.ok,
            summary=summary,
            files_changed=sorted((files_after - files_before) | _written(messages)),
            test_output=test.output[-4000:],
            steps=steps,
            total_tokens=tokens,
        )


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


def _written(messages: list[Message]) -> set[str]:
    """Paths the model wrote, including ones that existed before (modified files)."""
    paths: set[str] = set()
    for message in messages:
        for call in message.get("tool_calls", []):
            if call["function"]["name"] == "write_file":
                path = json.loads(call["function"]["arguments"]).get("path")
                if path:
                    paths.add(str(path).removeprefix("./"))
    return paths
