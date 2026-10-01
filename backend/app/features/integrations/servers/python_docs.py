"""A small MCP server: documentation for the Python standard library, offline and read-only.

Developers look up the real API (`csv.DictWriter`, `pathlib.Path.glob`) instead of guessing.
Only standard-library modules are imported, and a few with side effects on import are refused.

    python -m app.features.integrations.servers.python_docs   (speaks MCP over stdio)
"""

import importlib
import inspect
import pydoc
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

MAX_CHARS = 6000
REFUSED = frozenset({"antigravity", "this", "turtle", "turtledemo", "tkinter", "idlelib"})
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)

server = FastMCP("python_docs", log_level="WARNING")


def resolve(name: str) -> Any:
    """`pathlib.Path.glob` → the object, importing only standard-library modules."""
    parts = name.strip().split(".")
    if not parts[0] or parts[0] not in sys.stdlib_module_names or parts[0] in REFUSED:
        raise LookupError(f"{parts[0]!r} is not a standard-library module this tool can open")
    obj: Any = None
    for i in range(len(parts), 0, -1):  # longest importable module prefix
        try:
            obj = importlib.import_module(".".join(parts[:i]))
        except ImportError:
            continue
        for attr in parts[i:]:
            obj = getattr(obj, attr)
        return obj
    raise LookupError(f"Couldn't import {name!r}")


@server.tool(annotations=READ_ONLY)
def lookup(name: str) -> str:
    """Documentation for a standard-library module, class, function or method, by dotted
    name, e.g. "csv.DictWriter", "pathlib.Path.glob", "datetime.date.fromisoformat"."""
    try:
        text = pydoc.render_doc(resolve(name), renderer=pydoc.plaintext)  # type: ignore[attr-defined]
    except (LookupError, AttributeError) as exc:
        return f"Not found: {exc}"
    return text[:MAX_CHARS] + ("\n... (cut)" if len(text) > MAX_CHARS else "")


@server.tool(annotations=READ_ONLY)
def members(module: str) -> str:
    """The public classes and functions of a standard-library module, one line each, e.g.
    "statistics" or "itertools"."""
    try:
        obj = resolve(module)
    except (LookupError, AttributeError) as exc:
        return f"Not found: {exc}"
    lines = []
    for name, value in inspect.getmembers(obj):
        if name.startswith("_") or not (inspect.isclass(value) or callable(value)):
            continue
        summary = (inspect.getdoc(value) or "").split("\n", 1)[0]
        lines.append(f"{name}: {summary}"[:160])
    return "\n".join(lines)[:MAX_CHARS] or "(no public classes or functions)"


if __name__ == "__main__":
    server.run()
