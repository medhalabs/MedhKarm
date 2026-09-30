"""Tools the built-in developer engine offers the model, and how each one runs in the sandbox."""

from typing import Any

from app.features.models.schemas import ToolSpec
from app.features.sandbox.exceptions import SandboxError
from app.features.sandbox.interfaces import Sandbox

FINISH = "finish"


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
        if name == "run_command":
            result = await sandbox.run(str(arguments["command"]))
            return _truncate(f"exit code {result.exit_code}\n{result.output}")
        return f"Unknown tool: {name}"
    except KeyError as exc:
        return f"Missing argument {exc} for {name}"
    except SandboxError as exc:
        return f"Error: {exc.message}"


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n... ({len(text) - MAX_OUTPUT_CHARS} more characters)"
