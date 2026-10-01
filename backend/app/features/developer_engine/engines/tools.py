"""Tools the built-in developer engine offers the model, and how each one runs in the sandbox."""

import shlex
from typing import Any

from app.features.developer_engine.engines.patch import (
    BEGIN,
    PatchError,
    apply_hunks,
    extract_patch,
    parse_patch,
)
from app.features.models.schemas import ToolCall, ToolSpec
from app.features.sandbox.exceptions import SandboxError
from app.features.sandbox.interfaces import Sandbox

FINISH = "finish"
APPLY_PATCH = "apply_patch"


def _spec(name: str, description: str, properties: dict[str, Any]) -> ToolSpec:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties),
            },
        },
    }


TOOL_SPECS: list[ToolSpec] = [
    _spec(
        "write_file",
        "Create or overwrite a file in the workspace.",
        {"path": {"type": "string"}, "content": {"type": "string"}},
    ),
    _spec("read_file", "Read a file from the workspace.", {"path": {"type": "string"}}),
    _spec("list_files", "List all files in the workspace.", {}),
    _spec(
        APPLY_PATCH,
        "Edit files with a patch: add, update (context hunks with ' ', '-', '+' lines), "
        "move or delete files. Prefer this over rewriting whole files.",
        {
            "input": {
                "type": "string",
                "description": "Patch text from '*** Begin Patch' to '*** End Patch'",
            }
        },
    ),
    _spec(
        "run_command",
        "Run a shell command in the workspace and get its exit code and output.",
        {"command": {"type": "string"}},
    ),
    _spec(
        FINISH,
        "Call when the task is complete and the tests pass.",
        {"summary": {"type": "string"}},
    ),
]

MAX_OUTPUT_CHARS = 4000


async def execute_tool(name: str, arguments: dict[str, Any], sandbox: Sandbox) -> str:
    """Run one tool call and return the text the model sees. Errors are returned, not raised."""
    try:
        if name == "write_file":
            await sandbox.write_file(str(arguments["path"]), str(arguments["content"]))
            return f"Wrote {arguments['path']}"
        if name == "read_file":
            return _truncate(await sandbox.read_file(str(arguments["path"])))
        if name == "list_files":
            return "\n".join(await sandbox.list_files()) or "(empty workspace)"
        if name == APPLY_PATCH:
            return await _apply_patch(str(arguments["input"]), sandbox)
        if name == "run_command":
            result = await sandbox.run(str(arguments["command"]))
            return _truncate(f"exit code {result.exit_code}\n{result.output}")
        return f"Unknown tool: {name}"
    except KeyError as exc:
        return f"Missing argument {exc} for {name}"
    except SandboxError as exc:
        return f"Error: {exc.message}"
    except PatchError as exc:
        return f"Patch not applied: {exc}"


def normalize_call(call: ToolCall) -> ToolCall:
    """gpt-oss often runs `apply_patch` as a shell command. Turn that into a real apply_patch
    call: the shell has no such command, and Ollama Cloud returns 500s for conversations
    that contain such patch-in-shell calls."""
    if call.name == APPLY_PATCH and "input" not in call.arguments:
        # The model sometimes names the argument "patch" (Codex style) instead of "input".
        text = next((v for v in call.arguments.values() if isinstance(v, str)), "")
        return ToolCall(id=call.id, name=APPLY_PATCH, arguments={"input": text})
    command = str(call.arguments.get("command", ""))
    if call.name == "run_command" and BEGIN in command:
        try:
            return ToolCall(
                id=call.id, name=APPLY_PATCH, arguments={"input": extract_patch(command)}
            )
        except PatchError:
            return call
    return call


def compacted_patch_arguments(result: str) -> dict[str, str]:
    """What an applied (or rejected) patch call looks like in the conversation afterwards.

    Keeping full patch text in the history makes Ollama Cloud's gpt-oss:120b fail with HTTP 500
    on later requests (reproduced 0/3; 3/3 once compacted), and resending big patches every step
    wastes tokens. The files themselves hold the current content.
    """
    note = f"(patch already handled: {result[:300]}. Read the files for their current content.)"
    return {"input": note}


async def _apply_patch(text: str, sandbox: Sandbox) -> str:
    ops = parse_patch(text)
    done: list[str] = []
    for op in ops:
        if op.kind == "add":
            await sandbox.write_file(op.path, op.content)
            done.append(f"added {op.path}")
        elif op.kind == "delete":
            await sandbox.read_file(op.path)  # raises if missing, and checks the path is safe
            await sandbox.run(f"rm -f {shlex.quote(op.path)}")
            done.append(f"deleted {op.path}")
        else:
            updated = apply_hunks(await sandbox.read_file(op.path), op.hunks, op.path)
            target = op.move_to or op.path
            await sandbox.write_file(target, updated)
            if op.move_to and op.move_to != op.path:
                await sandbox.run(f"rm -f {shlex.quote(op.path)}")
                done.append(f"updated {op.path} -> {op.move_to}")
            else:
                done.append(f"updated {op.path}")
    return "Patch applied: " + ", ".join(done)


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n... ({len(text) - MAX_OUTPUT_CHARS} more characters)"
