"""Build graph: plan → (develop → review)* → verify → (release gate) → finish.

The CTO plans tasks; for each task the assigned developer works and the CTO reviews, sending
it back with changes if needed. Failed verification skips the gate: the founder is only asked
to approve working code.
"""

from typing import Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.events.interfaces import EventStore
from app.features.models.interfaces import LLMProvider
from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.checkers.test_command import TestCommandChecker
from app.features.workflows.interfaces import WorkChecker
from app.features.workflows.nodes.approval import approval
from app.features.workflows.nodes.develop import make_develop_node
from app.features.workflows.nodes.finish import make_finish_node
from app.features.workflows.nodes.plan import PLANNER_PROMPT, make_plan_node
from app.features.workflows.nodes.review import REVIEW_PROMPT, after_review, make_review_node
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
    events: EventStore | None = None,
    planner_instructions: str | None = None,
    review_instructions: str | None = None,
    developer_names: list[str] | None = None,
    max_developers: int = 1,
    max_revisions: int = 1,
) -> CompiledStateGraph[BuildState, None, BuildState, BuildState]:
    """`planner` is the CTO's model: it plans and reviews. The role settings normally come from
    the team template (see app/workers/wiring.py)."""
    graph = StateGraph(BuildState)
    graph.add_node(
        "plan",
        make_plan_node(
            planner, planner_instructions or PLANNER_PROMPT, developer_names, max_developers
        ),
    )
    graph.add_node("develop", make_develop_node(engine, sandboxes, events))
    graph.add_node(
        "review",
        make_review_node(planner, sandboxes, review_instructions or REVIEW_PROMPT, max_revisions),
    )
    graph.add_node("verify", make_verify_node(sandboxes, checker or TestCommandChecker()))
    graph.add_node("approval", approval)
    graph.add_node("finish", make_finish_node(sandboxes))

    graph.add_edge(START, "plan")
    graph.add_edge("plan", "develop")
    graph.add_edge("develop", "review")
    graph.add_conditional_edges("review", after_review, ["develop", "verify"])
    graph.add_conditional_edges("verify", _after_verify)
    graph.add_edge("approval", "finish")
    graph.add_edge("finish", END)

    return graph.compile(checkpointer=checkpointer)
