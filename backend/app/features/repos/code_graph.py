"""The code graph's view of a project for the codebase map: its most connected classes and
functions, with their methods and line numbers. Built with Graphify (app/shared/code_graph.py);
empty when Graphify isn't in the sandbox."""

import json
from collections import Counter
from typing import Any

from app.features.sandbox.interfaces import Sandbox
from app.shared.code_graph import BUILD, GRAPH_FILE

MAX_HUBS = 10
MAX_METHODS = 12


class GraphifyCodeGraph:
    async def describe(self, sandbox: Sandbox) -> str:
        if not (await sandbox.run(BUILD)).ok:
            return ""
        raw = await sandbox.run(f"cat {GRAPH_FILE}")
        try:
            graph = json.loads(raw.output)
        except ValueError:
            return ""
        return hubs(graph)


def hubs(graph: dict[str, Any]) -> str:
    """'Serializer (src/x/serializer.py L40, 36 links): methods loads L328, dumps L309, …'"""
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    links = graph.get("links", [])
    degree: Counter[str] = Counter()
    methods: dict[str, list[dict[str, Any]]] = {}
    for link in links:
        degree[link["source"]] += 1
        degree[link["target"]] += 1
        if link.get("relation") == "method" and link["target"] in nodes:
            methods.setdefault(link["source"], []).append(nodes[link["target"]])
    lines = []
    for node_id, links_count in degree.most_common():
        node = nodes.get(node_id)
        if not node or not _is_project_code(node):
            continue
        where = f"{node['source_file']} {node.get('source_location', '')}".strip()
        line = f"- {node['label']} ({where}, {links_count} links)"
        own = sorted(methods.get(node_id, []), key=lambda m: _line(m))[:MAX_METHODS]
        if own:
            line += ": " + ", ".join(
                f"{m['label'].lstrip('.')} {m.get('source_location', '')}".strip() for m in own
            )
        lines.append(line)
        if len(lines) == MAX_HUBS:
            break
    return "Most connected code (from the code graph):\n" + "\n".join(lines) if lines else ""


def _is_project_code(node: dict[str, Any]) -> bool:
    path = str(node.get("source_file", ""))
    return (
        node.get("file_type") == "code"
        and bool(path)
        and not any(part in ("tests", "test", "__tests__") for part in path.split("/"))
        and not path.split("/")[-1].startswith("test_")
        and not node.get("label", "").endswith(".py")  # files themselves: already in the map
    )


def _line(node: dict[str, Any]) -> int:
    location = str(node.get("source_location", "")).lstrip("L")
    return int(location) if location.isdigit() else 0
