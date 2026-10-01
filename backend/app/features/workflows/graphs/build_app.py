"""Build graph: plan → develop → verify → (release gate) → finish.

Failed verification skips the gate: the founder is only asked to approve working code.
"""

from typing import Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.models.interfaces import LLMProvider
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.checkers.test_command import TestCommandChecker
from app.features.workflows.interfaces import WorkChecker
from app.features.workflows.nodes.approval import approval
from app.features.workflows.nodes.develop import make_develop_node
from app.features.workflows.nodes.finish import make_finish_node
from app.features.workflows.nodes.plan import make_plan_node
from app.features.workflows.nodes.verify import make_verify_node
from app.features.workflows.state import BuildState


def _after_verify(state: BuildState) -> Literal["approval", "finish"]:
    return "approval" if state.get("verified") else "finish"


def build_app_graph(
    planner: LLMProvider,
    engine: DeveloperEngine,
    sandboxes: SandboxProvider,
    checkpointer: BaseCheckpointSaver[str],
    checker: WorkChecker | None = None,
) -> CompiledStateGraph[BuildState, None, BuildState, BuildState]:
    graph = StateGraph(BuildState)
    graph.add_node("plan", make_plan_node(planner))
    graph.add_node("develop", make_develop_node(engine, sandboxes))
    graph.add_node("verify", make_verify_node(sandboxes, checker or TestCommandChecker()))
    graph.add_node("approval", approval)
    graph.add_node("finish", make_finish_node(sandboxes))

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "develop")
    graph.add_edge("develop", "verify")
    graph.add_conditional_edges("verify", _after_verify)
    graph.add_edge("approval", "finish")
    graph.add_edge("finish", END)

    return graph.compile(checkpointer=checkpointer)
