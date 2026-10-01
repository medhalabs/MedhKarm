from app.features.repos.code_graph import hubs
from app.features.repos.service import RepoService
from app.features.repos.tests.fakes import sandbox_with
from app.features.sandbox.interfaces import Sandbox


def _node(node_id: str, label: str, path: str, line: int) -> dict[str, object]:
    return {
        "id": node_id,
        "label": label,
        "file_type": "code",
        "source_file": path,
        "source_location": f"L{line}",
    }


GRAPH = {
    "nodes": [
        _node("ser", "Serializer", "src/s/serializer.py", 40),
        _node("loads", ".loads()", "src/s/serializer.py", 328),
        _node("dumps", ".dumps()", "src/s/serializer.py", 309),
        _node("sig", "Signer", "src/s/signer.py", 80),
        _node("tst", "TestSerializer", "tests/test_serializer.py", 35),
        _node("file", "serializer.py", "src/s/serializer.py", 1),
    ],
    "links": [
        {"source": "ser", "target": "loads", "relation": "method"},
        {"source": "ser", "target": "dumps", "relation": "method"},
        {"source": "ser", "target": "sig", "relation": "uses"},
        {"source": "tst", "target": "ser", "relation": "uses"},
        {"source": "tst", "target": "loads", "relation": "calls"},
        {"source": "tst", "target": "dumps", "relation": "calls"},
        {"source": "file", "target": "ser", "relation": "contains"},
    ],
}


def test_hubs_list_project_code_with_methods_in_line_order() -> None:
    text = hubs(GRAPH)

    lines = text.splitlines()
    assert lines[0] == "Most connected code (from the code graph):"
    assert lines[1] == "- Serializer (src/s/serializer.py L40, 5 links): dumps() L309, loads() L328"
    assert "TestSerializer" not in text  # tests left out
    assert "- serializer.py" not in text  # files are in the map already


def test_empty_graph_says_nothing() -> None:
    assert hubs({"nodes": [], "links": []}) == ""


class FixedGraph:
    async def describe(self, sandbox: Sandbox) -> str:
        return "Most connected code (from the code graph):\n- Serializer"


async def test_the_map_includes_the_graph_when_one_is_given() -> None:
    sandbox = sandbox_with({"app.py": "class Serializer: ...\n"})

    with_graph = await RepoService(graph=FixedGraph()).checkout(sandbox, None)
    without = await RepoService().checkout(sandbox, None)

    assert "- Serializer" in with_graph.map.brief()
    assert without.map.graph == ""
