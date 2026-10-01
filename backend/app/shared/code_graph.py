"""Shell commands for Graphify's code graph (tree-sitter, no model calls), shared by the
codebase map (repos) and the developer's `explain_symbol` tool (developer_engine).

Graphify writes `graphify-out/` into the project; we move it outside the workspace at once,
so it never counts as a changed file or ends up in a pull request. Needs `graphifyy` in the
sandbox image (backend/sandbox-image/Dockerfile) and CODE_GRAPH=true.
"""

import shlex

GRAPH_DIR = "/tmp/medhkarm-graph"
GRAPH_FILE = f"{GRAPH_DIR}/graph.json"

# Rebuilds the graph from the workspace's current code (about half a second for 20 files).
BUILD = (
    "command -v graphify >/dev/null || exit 3; "
    "rm -rf graphify-out; graphify extract . --code-only >/dev/null 2>&1; "
    f"[ -f graphify-out/graph.json ] || exit 4; rm -rf {GRAPH_DIR}; mv graphify-out {GRAPH_DIR}"
)
NOT_INSTALLED = 3


def explain(symbol: str) -> str:
    return f"graphify explain {shlex.quote(symbol)} --graph {GRAPH_FILE} 2>&1"
