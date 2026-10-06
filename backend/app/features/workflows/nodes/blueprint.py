"""Puts the approved plan in the project: Lekha's documents go into its docs/ folder (they are
released with the code), and the CTO and the developers are told to follow the plan. Runs that
didn't start from a blueprint skip it. Safe to repeat: the files are written again."""

from typing import Any

from app.features.sandbox.interfaces import SandboxProvider
from app.features.workflows.interfaces import ApprovedPlans
from app.features.workflows.nodes.base import BuildNode
from app.features.workflows.schemas import PlanDocs
from app.features.workflows.state import BuildState

BRIEF_LIMIT = 14_000  # characters of the plan given to every prompt
BUILD_FIRST = (
    "The founder approved this plan. Follow it: its stack, data model, structure and test plan. "
    "Build only milestone 1 of the roadmap now; the later milestones come later, as changes."
)
READ_ORDER = ("architecture", "data", "structure", "roadmap", "tests", "brief")


def make_blueprint_node(sandboxes: SandboxProvider, plans: ApprovedPlans | None) -> BuildNode:
    async def blueprint(state: BuildState) -> dict[str, Any]:
        if plans is None or not state.get("run_id") or not state.get("sandbox_id"):
            return {}
        plan = await plans.for_run(state["run_id"])
        if plan is None or not plan.files:
            return {}
        sandbox = await sandboxes.attach(state["sandbox_id"])
        for path, content in plan.files.items():
            await sandbox.write_file(path, content)
        return {"blueprint_brief": plan_brief(plan), "blueprint_files": sorted(plan.files)}

    return blueprint


def plan_brief(plan: PlanDocs) -> str:
    """The plan as text for a prompt: the most useful documents first, cut to a limit."""
    ranked = sorted(
        plan.titles,
        key=lambda path: next(
            (i for i, key in enumerate(READ_ORDER) if key in path.lower()), len(READ_ORDER)
        ),
    )
    text = BUILD_FIRST
    for path in ranked:
        section = f"\n\n--- {plan.titles[path]} ({path}) ---\n{plan.files[path]}"
        if len(text) + len(section) > BRIEF_LIMIT:
            break
        text += section
    return text
