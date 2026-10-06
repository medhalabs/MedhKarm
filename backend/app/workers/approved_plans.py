"""Gives the build graph the plan a founder approved (features/blueprints), without the
workflows feature knowing about blueprints."""

from app.features.blueprints.catalog import README_PATH
from app.features.blueprints.service import BlueprintService
from app.features.runs.schemas import StartRun
from app.features.starters.service import StarterService
from app.features.workflows.schemas import PlanDocs

STACK_LIMIT = 1500


class ApprovedPlans:
    def __init__(self, blueprints: BlueprintService) -> None:
        self._blueprints = blueprints

    async def for_run(self, run_id: str) -> PlanDocs | None:
        plan = await self._blueprints.for_run(run_id)
        if plan is None or not plan.docs:
            return None
        files = {d.path: d.content for d in plan.docs}
        titles = {d.path: d.title for d in plan.docs}
        if any(d.path.startswith("docs/changes/") for d in plan.docs):
            # A change to a project that has its own docs: add ours, never replace its index.
            return PlanDocs(files=files, titles=titles)
        index = "# Project plan\n\nWritten by Lekha and approved before the build.\n\n" + "\n".join(
            f"- [{d.title}]({d.path.removeprefix('docs/')})" for d in plan.docs
        )
        return PlanDocs(files={README_PATH: index + "\n", **files}, titles=titles)


class StackText:
    """The stack a new project will really be built on (the team's starter and defaults), as
    text for Lekha, so her documents match what the developers build. Existing repositories
    keep their own stack, so they get none."""

    def __init__(self, starters: StarterService) -> None:
        self._starters = starters

    def __call__(self, brief: StartRun) -> str:
        if brief.repo:
            return ""
        return self._starters.resolve(brief.request, brief.stack).brief()[:STACK_LIMIT]
