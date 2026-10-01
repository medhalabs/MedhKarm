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
from app.shared import code_graph

FINISH = "finish"
APPLY_PATCH = "apply_patch"


def _spec(
    name: str,
    description: str,
    properties: dict[str, Any],
    optional: tuple[str, ...] = (),
) -> ToolSpec:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": [p for p in properties if p not in optional],
            },
        },
    }


TOOL_SPECS: list[ToolSpec] = [
    _spec(
        "write_file",
        "Create a new file, or replace a whole file with its complete new content.",
        {"path": {"type": "string"}, "content": {"type": "string"}},
    ),
    _spec(
        "edit_file",
        "Change part of an existing file: replace old_text (copied exactly from the file, "
        "found once) with new_text. Use this for changes to existing files.",
        {
            "path": {"type": "string"},
            "old_text": {"type": "string"},
            "new_text": {"type": "string"},
        },
    ),
    _spec(
        "read_file",
        "Read a file from the workspace, with line numbers. Long files come in parts: pass "
        "start_line (and end_line) to read the part you need.",
        {
            "path": {"type": "string"},
            "start_line": {"type": "integer", "description": "First line to read (from 1)"},
            "end_line": {"type": "integer", "description": "Last line to read"},
        },
        optional=("start_line", "end_line"),
    ),
    _spec(
        "explain_symbol",
        "Explain a class, function or method from the code graph: where it is defined (file "
        "and line), its methods, what it calls and uses, and what uses it. Faster than reading "
        "files to find your way. Give a name like Serializer or loads.",
        {"name": {"type": "string"}},
    ),
    _spec(
        "search",
        "Find text in the workspace's files (a regular expression, like grep). Returns "
        "matching lines as path:line:text. Use it to find where something is defined or used.",
        {
            "pattern": {"type": "string"},
            "path": {"type": "string", "description": "File or folder to search; default all"},
        },
        optional=("path",),
    ),
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
READ_LINES = 150  # lines per read_file call when no range is given
SEARCH_LINES = 60
# write_file may not shrink an existing file of this many lines to under half: that was a
# fragment replacing a whole module (live run, Oct 1, 2026). edit_file is for changes.
GUARD_MIN_LINES = 40


async def execute_tool(name: str, arguments: dict[str, Any], sandbox: Sandbox) -> str:
    """Run one tool call and return the text the model sees. Errors are returned, not raised."""
    try:
        if name == "write_file":
            return await _write(str(arguments["path"]), str(arguments["content"]), sandbox)
        if name == "edit_file":
            return await _edit(
                str(arguments["path"]),
                str(arguments["old_text"]),
                str(arguments["new_text"]),
                sandbox,
            )
        if name == "read_file":
            return _read_lines(
                str(arguments["path"]),
                await sandbox.read_file(str(arguments["path"])),
                arguments.get("start_line"),
                arguments.get("end_line"),
            )
        if name == "explain_symbol":
            return await _explain(str(arguments["name"]), sandbox)
        if name == "search":
            return await _search(
                str(arguments["pattern"]), str(arguments.get("path") or "."), sandbox
            )
        if name == "list_files":
            return "\n".join(await sandbox.list_files()) or "(empty workspace)"
        if name == APPLY_PATCH:
            return await _apply_patch(str(arguments["input"]), sandbox)
        if name == "run_command":
            result = await sandbox.run(str(arguments["command"]))
            return _truncate(f"exit code {result.exit_code}\n{result.output}")
        return f"Unknown tool: {name}"
    except KeyError as exc:
        return (
            f"Missing argument {exc} for {name}. You sent: {', '.join(arguments) or 'nothing'}. "
            "Call it again with every argument."
        )
    except SandboxError as exc:
        return f"Error: {exc.message}"
    except PatchError as exc:
        return f"Patch not applied: {exc}"


# Other names small models use for our arguments (gpt-oss:20b sent write_file calls without
# `content` 5 times in one run, Oct 1, 2026).
ALIASES = {
    "path": ("file_path", "filepath", "file", "filename"),
    "content": ("contents", "text", "code", "file_content", "data"),
    "old_text": ("old", "old_string", "search", "find"),
    "new_text": ("new", "new_string", "replace", "replacement"),
}


def _with_aliases(call: ToolCall) -> ToolCall:
    arguments = dict(call.arguments)
    for name, others in ALIASES.items():
        if name not in arguments:
            found = next((o for o in others if o in arguments), None)
            if found:
                arguments[name] = arguments.pop(found)
    return ToolCall(id=call.id, name=call.name, arguments=arguments)


def normalize_call(call: ToolCall) -> ToolCall:
    """gpt-oss often runs `apply_patch` as a shell command. Turn that into a real apply_patch
    call: the shell has no such command, and Ollama Cloud returns 500s for conversations
    that contain such patch-in-shell calls. Also maps other argument names (ALIASES)."""
    if call.name in ("write_file", "edit_file", "read_file"):
        return _with_aliases(call)
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


def describe_tool_use(name: str, arguments: dict[str, Any], result: str) -> str:
    """One plain line for the activity feed: what the developer just did."""
    if result.startswith("Not allowed:"):
        return f"Tried {name}, which isn't one of its tools"
    path = str(arguments.get("path", ""))
    if name == "write_file":
        return f"Wrote {path}" if result.startswith("Wrote") else f"Tried to overwrite {path}"
    if name == "edit_file":
        return f"Edited {path}" if result.startswith("Edited") else f"Tried to edit {path}"
    if name == "read_file":
        start = arguments.get("start_line")
        return f"Read {path}" + (f" from line {start}" if start else "")
    if name == "explain_symbol":
        return f"Looked up {str(arguments.get('name', ''))[:60]} in the code graph"
    if name == "search":
        return f"Searched for “{str(arguments.get('pattern', ''))[:60]}”"
    if name == "list_files":
        return "Looked through the project files"
    if name == "run_command":
        command = (
            str(arguments.get("command", "")).strip().splitlines()[0][:80]
            if arguments.get("command")
            else ""
        )
        code = result.split("\n", 1)[0].removeprefix("exit code ").strip()
        return f"Ran `{command}` (exit {code})"
    if name == APPLY_PATCH:
        if result.startswith("Patch applied: "):
            return "Edited files: " + result.removeprefix("Patch applied: ")
        return "Tried an edit that didn't apply"
    if "__" in name:  # an MCP tool: "<server>__<tool>"
        server, tool = name.split("__", 1)
        detail = next((str(v) for v in arguments.values() if isinstance(v, str)), "")
        return f"Used {server}: {tool}" + (f" ({detail[:60]})" if detail else "")
    return f"Used {name}"


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


async def _write(path: str, content: str, sandbox: Sandbox) -> str:
    try:
        existing = await sandbox.read_file(path)
    except SandboxError:
        existing = ""
    old_lines, new_lines = len(existing.splitlines()), len(content.splitlines())
    if old_lines >= GUARD_MIN_LINES and new_lines < old_lines // 2:
        return (
            f"Not written: {path} has {old_lines} lines and this content has only {new_lines}, "
            "so it would delete most of the file. To change part of it, use edit_file. To "
            "replace it, send the complete new file."
        )
    await sandbox.write_file(path, content)
    return f"Wrote {path}"


async def _edit(path: str, old: str, new: str, sandbox: Sandbox) -> str:
    text = await sandbox.read_file(path)
    if not old:
        return "old_text is empty: copy the exact lines to replace from the file."
    count = text.count(old)
    if count == 0:
        return (
            f"old_text not found in {path}. Copy it exactly from read_file's output "
            "(without the line numbers), including spaces."
        )
    if count > 1:
        return f"old_text appears {count} times in {path}: include more lines to make it unique."
    await sandbox.write_file(path, text.replace(old, new, 1))
    return f"Edited {path}"


def _read_lines(path: str, text: str, start: Any = None, end: Any = None) -> str:
    """Numbered lines, so the model can quote and patch them; a long file comes in parts,
    with a note saying how to read the rest (a cut-off file was re-read over and over)."""
    lines = text.splitlines()
    try:
        first = max(int(start or 1), 1)
        last = min(int(end) if end else first + READ_LINES - 1, len(lines))
    except (TypeError, ValueError):
        first, last = 1, min(READ_LINES, len(lines))
    if not lines:
        return f"({path} is empty)"
    if first > len(lines):
        return f"{path} has only {len(lines)} lines."
    width = len(str(last))
    body = "\n".join(f"{n:>{width}}| {lines[n - 1]}" for n in range(first, last + 1))
    body = _truncate(body)
    if first > 1 or last < len(lines):
        more = f" Next: read_file with start_line={last + 1}." if last < len(lines) else ""
        body += f"\n(lines {first}-{last} of {len(lines)}.{more})"
    return body


MAX_EXPLAINED = 3


async def _explain(symbol: str, sandbox: Sandbox) -> str:
    """Rebuilds the graph (so it includes the developer's own changes) and explains the
    symbol; a name found in several files is explained for each (up to 3)."""
    built = await sandbox.run(code_graph.BUILD)
    if built.exit_code == code_graph.NOT_INSTALLED:
        return "explain_symbol isn't available in this workspace: use search instead."
    if not built.ok:
        return "Couldn't build the code graph: use search instead."
    result = (await sandbox.run(code_graph.explain(symbol))).output
    if result.startswith("Ambiguous"):
        ids = [line.split("id:", 1)[1].strip() for line in result.splitlines() if "id:" in line]
        parts = [(await sandbox.run(code_graph.explain(i))).output for i in ids[:MAX_EXPLAINED]]
        result = "\n\n".join(parts) or result
    return _truncate(result.strip() or f"No {symbol!r} in the code graph.")


async def _search(pattern: str, path: str, sandbox: Sandbox) -> str:
    result = await sandbox.run(
        f"grep -rnIE --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=__pycache__ "
        f"-e {shlex.quote(pattern)} -- {shlex.quote(path)} | head -n {SEARCH_LINES + 1}"
    )
    lines = [line.removeprefix("./")[:300] for line in result.output.splitlines()]
    if not lines:
        return f"No matches for {pattern!r}."
    if len(lines) > SEARCH_LINES:
        return "\n".join(lines[:SEARCH_LINES]) + "\n(more matches: narrow the pattern or path)"
    return "\n".join(lines)


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n... ({len(text) - MAX_OUTPUT_CHARS} more characters)"
