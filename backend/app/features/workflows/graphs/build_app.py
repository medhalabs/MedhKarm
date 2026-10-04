"""Build graph: prepare → connect → plan → (develop → review)* → verify → browser QA →
security → preview → (release gate) → finish.

QA (verify) runs the tests, build, type-check and lint; failures go back to a developer once.

The CTO plans tasks; for each task the assigned developer works and the CTO reviews, sending
it back with changes if needed. Failed verification skips the gate: the founder is only asked
to approve working code. The security engineer then scans the changes: blocking findings go
back to a developer once (develop → review → verify → security again), warnings go to the gate.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.features.approvals.schemas import ApprovalPolicy
from app.features.deploys.service import DeployService
from app.features.developer_engine.interfaces import DeveloperEngine
from app.features.events.interfaces import EventStore
from app.features.models.interfaces import LLMProvider
from app.features.repos.service import RepoService
from app.features.sandbox.interfaces import SandboxProvider
from app.features.security.service import SecurityReview
from app.features.workflows.checkers.quality import QualityChecker
from app.features.workflows.checkers.test_command import TestCommandChecker
from app.features.workflows.interfaces import WorkChecker
from app.features.workflows.nodes.approval import make_approval_node
from app.features.workflows.nodes.browser_qa import after_browser_qa, make_browser_qa_node
from app.features.workflows.nodes.connect import make_connect_node
from app.features.workflows.nodes.develop import make_develop_node
from app.features.workflows.nodes.finish import make_finish_node
from app.features.workflows.nodes.plan import PLANNER_PROMPT, make_plan_node
from app.features.workflows.nodes.prepare import make_prepare_node
from app.features.workflows.nodes.preview import make_preview_node
from app.features.workflows.nodes.review import REVIEW_PROMPT, after_review, make_review_node
from app.features.workflows.nodes.security import after_security, make_security_node
from app.features.workflows.nodes.verify import after_verify, make_verify_node
from app.features.workflows.state import BuildState


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
    approval_policy: ApprovalPolicy | None = None,
    repos: RepoService | None = None,
    security: SecurityReview | None = None,
    specialties: dict[str, str] | None = None,
    specialty_instructions: dict[str, str] | None = None,
    browser_tester: DeveloperEngine | None = None,
    qa_name: str = "QA",
    deploys: DeployService | None = None,
) -> CompiledStateGraph[BuildState, None, BuildState, BuildState]:
    """`planner` is the CTO's model: it plans and reviews. The role settings normally come from
    the team template (see app/workers/wiring.py). `approval_policy` decides the release gate:
    without one, every release asks the founder. `repos` clones founders' repositories and
    opens pull requests; without one, runs can't use a repository (new projects still work).
    `security` is the security engineer's review after QA; without one, nothing is scanned.
    `specialties` (developer name -> specialty) and `specialty_instructions` let the CTO assign
    tasks to specialists, who get their specialty's instructions. `browser_tester` is QA's
    engine for end-to-end browser tests of web changes; without one, none are written.
    `deploys` is DevOps: a preview before the gate, production after approval."""
    repos = repos or RepoService()
    graph = StateGraph(BuildState)
    graph.add_node("prepare", make_prepare_node(sandboxes))
    graph.add_node("connect", make_connect_node(sandboxes, repos))
    graph.add_node(
        "plan",
        make_plan_node(
            planner,
            planner_instructions or PLANNER_PROMPT,
            developer_names,
            max_developers,
            specialties,
        ),
    )
    graph.add_node("develop", make_develop_node(engine, sandboxes, events, specialty_instructions))
    graph.add_node(
        "review",
        make_review_node(planner, sandboxes, review_instructions or REVIEW_PROMPT, max_revisions),
    )
    graph.add_node(
        "verify",
        make_verify_node(
            sandboxes, checker or QualityChecker(TestCommandChecker()), developer_names
        ),
    )
    names = developer_names or ["Developer"]
    frontend = next((n for n in names if (specialties or {}).get(n) == "frontend"), names[0])
    graph.add_node(
        "browser_qa",
        make_browser_qa_node(sandboxes, browser_tester, events, qa_name, frontend),
    )
    graph.add_node(
        "security", make_security_node(sandboxes, security, developer_names or ["Developer"])
    )
    graph.add_node("preview", make_preview_node(sandboxes, deploys))
    graph.add_node("approval", make_approval_node(approval_policy))
    graph.add_node("finish", make_finish_node(sandboxes, repos, deploys))

    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "connect")
    graph.add_edge("connect", "plan")
    graph.add_edge("plan", "develop")
    graph.add_edge("develop", "review")
    graph.add_conditional_edges("review", after_review, ["develop", "verify"])
    graph.add_conditional_edges("verify", after_verify, ["develop", "browser_qa", "finish"])
    graph.add_conditional_edges("browser_qa", after_browser_qa, ["develop", "security", "finish"])
    graph.add_conditional_edges("security", after_security, ["develop", "preview", "finish"])
    graph.add_edge("preview", "approval")
    graph.add_edge("approval", "finish")
    graph.add_edge("finish", END)

    return graph.compile(checkpointer=checkpointer)
